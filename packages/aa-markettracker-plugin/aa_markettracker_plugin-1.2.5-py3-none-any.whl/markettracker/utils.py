import logging

import requests
from allianceauth.groupmanagement.models import Group
from allianceauth.services.modules.discord.models import DiscordUser
from django.conf import settings
from esi.clients import EsiClientProvider
from esi.errors import TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveRegion
from requests.exceptions import HTTPError

from .models import (
    ContractSnapshot,
    MTTaskLog,
    TrackedContract,
    TrackedStructure,
)

logger = logging.getLogger(__name__)
ESI_BASE_URL = "https://esi.evetech.net/latest"
esi = EsiClientProvider()


def resolve_ping_target(ping_value: str) -> str:
    if not ping_value:
        return ""
    if ping_value in ("@here", "@everyone"):
        return ping_value

    if ping_value.startswith("@"):
        group_name = ping_value[1:]
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            return f"@{group_name}"

        try:
            discord_group_info = DiscordUser.objects.group_to_role(group=group)
        except HTTPError:
            return f"@{group_name}"
        except Exception:
            return f"@{group_name}"

        if discord_group_info and "id" in discord_group_info:
            return f"<@&{discord_group_info['id']}>"
        return f"@{group_name}"

    return ""



def location_display(scope: str, location_id: int) -> str:
    """
    Location name.
    """
    if scope == "region":
        try:
            return EveRegion.objects.get(id=location_id).name
        except EveRegion.DoesNotExist:
            return str(location_id)
    else:
        try:
            return TrackedStructure.objects.get(structure_id=location_id).name
        except TrackedStructure.DoesNotExist:
            return str(location_id)


def resolve_ping_target_from_config(config) -> str:
    """
    Pings for discord messages
    """
    if config.discord_ping_group:
        try:
            mapping = DiscordUser.objects.group_to_role(group=config.discord_ping_group)
            role_id = mapping.get("id") if mapping else None
            if role_id:
                return f"<@&{role_id}>"
        except HTTPError:
            logger.exception("[MarketTracker] Discord service error when resolving group role")

        return f"@{config.discord_ping_group.name}"

    v = (config.discord_ping_group_text or "").strip()
    if v in {"here", "@here"}:
        return "@here"
    if v in {"everyone", "@everyone"}:
        return "@everyone"
    return ""


def contract_matches(tc: TrackedContract, snap: ContractSnapshot):
    """
    Checks for contracts to match tracking
    """

    if not tc.is_active:
        return False, None

    if (snap.type or "").lower() != "item_exchange":
        return False, "type"

    if (snap.status or "").lower() != "outstanding":
        return False, "status"

    if tc.max_price and float(tc.max_price) > 0:
        price = float(snap.price or 0)
        if price > float(tc.max_price):
            logger.debug(
                "[match] snap %s price %.2f > max %.2f",
                snap.contract_id,
                price,
                float(tc.max_price),
            )
            return False, "price"


    title = (snap.title or "").strip()


    if tc.mode == TrackedContract.Mode.CUSTOM:
        filt = (tc.title_filter or "").strip()
        if not filt:

            return False, "title"

        if filt.lower() not in title.lower():
            logger.debug(
                "[match] snap %s title '%s' !contains '%s'",
                snap.contract_id,
                title,
                filt,
            )
            return False, "title"

        return True, None

    if tc.mode == TrackedContract.Mode.DOCTRINE:
        fit = tc.fitting
        if not fit or not getattr(fit, "ship_type_id", None):
            return False, "fit"

        ship_type_id = int(fit.ship_type_id)

        items = snap.items or []
        if not items:
            logger.debug("[match] snap %s has no items json", snap.contract_id)
            return False, "items"

        contract_counts: dict[int, int] = {}
        for it in items:
            try:
                t_id = int(it.get("type_id"))
                qty = int(it.get("quantity") or 0)
            except (TypeError, ValueError):
                continue
            contract_counts[t_id] = contract_counts.get(t_id, 0) + qty

        if contract_counts.get(ship_type_id, 0) < 1:
            logger.debug(
                "[match] snap %s missing ship type_id=%s",
                snap.contract_id,
                ship_type_id,
            )
            return False, "fit"

        required_items: dict[int, int] = {}

        for slot in ("high_slots", "mid_slots", "low_slots", "rigs", "subsystems"):
            for mod in getattr(fit, slot, []) or []:
                try:
                    t_id = int(mod.type_id)
                except (TypeError, ValueError):
                    continue
                required_items[t_id] = required_items.get(t_id, 0) + 1

        for t_id, req_qty in required_items.items():
            have_qty = contract_counts.get(t_id, 0)
            if have_qty < req_qty:
                logger.debug(
                    "[match] snap %s missing module type_id=%s (have %s, need %s)",
                    snap.contract_id,
                    t_id,
                    have_qty,
                    req_qty,
                )
                return False, "fit"

        return True, None

    return False, "mode"




def fetch_contract_items(contract_obj, _access_token_unused, char_id):
    """
    Lazy item snapshot.
    Fetches items once per contract if missing.
    403 is normal (token not allowed to view that contract's items).
    """

    # already cached on snapshot
    if contract_obj.items:
        return contract_obj.items

    if not char_id:
        logger.warning(
            "[Contracts] Cannot fetch items for contract %s: missing owner char_id",
            contract_obj.contract_id,
        )
        return []

    tokens = Token.objects.filter(
        character_id=char_id,
        scopes__name="esi-contracts.read_character_contracts.v1",
    )

    if not tokens.exists():
        logger.warning(
            "[Contracts] No contracts token for character %s (contract %s)",
            char_id,
            contract_obj.contract_id,
        )
        return []

    url = f"{ESI_BASE_URL}/characters/{char_id}/contracts/{contract_obj.contract_id}/items/"

    for token in tokens:
        try:
            access_token = token.valid_access_token()
        except TokenInvalidError:
            logger.warning(
                "[Contracts] Invalid token for character %s (token id=%s)",
                char_id,
                token.id,
            )
            continue
        except Exception as e:
            logger.exception(
                "[Contracts] Token refresh failed for character %s (token id=%s): %s",
                char_id,
                token.id,
                e,
            )
            continue

        headers = {
            "User-Agent": getattr(settings, "ESI_USER_AGENT", "MarketTracker/1.0"),
            "Authorization": f"Bearer {access_token}",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)

            # 403 = this char/token can't access items for that contract; not retryable
            if resp.status_code == 403:
                logger.info(
                    "[Contracts] Items not accessible for contract %s with char %s (403).",
                    contract_obj.contract_id,
                    char_id,
                )
                return []

            resp.raise_for_status()

            items = resp.json() or []
            contract_obj.items = items
            contract_obj.save(update_fields=["items"])

            db_log(source="contracts", event="items_saved", data={
                "contract_id": contract_obj.contract_id,
                "owner_character_id": char_id,
            })


            return items

        except Exception as e:
            logger.error(
                "[Contracts] Failed to load items for contract %s with char %s (token id=%s): %s",
                contract_obj.contract_id,
                char_id,
                token.id,
                e,
            )
            continue

    logger.warning(
        "[Contracts] Could not fetch items for contract %s (char %s) with any token",
        contract_obj.contract_id,
        char_id,
    )
    return []


def db_log(level="INFO", source="contracts", event="run", message="", data=None):
    try:
        MTTaskLog.objects.create(
            level=level,
            source=source,
            event=event,
            message=message,
            data=data or None,
        )
    except Exception:
        # logging must not crash the task
        pass
