import logging
import socket
import time
import traceback
import uuid

import requests
from celery import current_task, shared_task
from django.conf import settings
from django.db import connection
from django.db.models import Sum
from django.utils import timezone as _tz
from django.utils.dateparse import parse_datetime
from esi.errors import TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveRegion
from requests.exceptions import HTTPError, RequestException

from .discord import (
    contracts_restocked_alert,
    items_restocked_alert,
    send_contracts_alert,
    send_items_alert,
)
from .models import (
    ContractDelivery,
    ContractSnapshot,
    Delivery,
    MarketCharacter,
    MarketOrderSnapshot,
    MarketTrackingConfig,
    TrackedContract,
    TrackedItem,
    TrackedStructure,
)
from .utils import contract_matches, db_log, fetch_contract_items

logger = logging.getLogger(__name__)
ESI_BASE_URL = "https://esi.evetech.net/latest"
HOSTNAME = socket.gethostname()
MARKET_ORDERS_TABLE = MarketOrderSnapshot._meta.db_table
CONTRACTS_TABLE = ContractSnapshot._meta.db_table

def _task_suffix(n: int = 8) -> str:
    tid = getattr(getattr(current_task, "request", None), "id", None) or uuid.uuid4().hex
    return str(tid).replace("-", "")[:n]

def esi_headers(access_token: str | None = None) -> dict:
    """
    Safe ESI headers builder.
    Never crashes if ESI_USER_AGENT is missing.
    """
    ua = (
        getattr(settings, "ESI_USER_AGENT", None)
        or getattr(settings, "ESI_USERAGENT", None)
        or "MarketTracker/1.0"
    )

    headers = {"User-Agent": ua}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def esi_get_json(url: str, *, access_token: str | None, params: dict | None = None, timeout: int = 20,
                 source: str = "items", event: str = "esi_error", ctx: dict | None = None,
                 max_attempts: int = 4) -> tuple[list | dict | None, dict]:
    """
    GET to ESI with retry/backoff. Returns (json_data_or_none, meta).
    meta contains: status_code, headers, attempts, error
    """
    meta = {"status_code": None, "headers": {}, "attempts": 0, "error": None}

    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        meta["attempts"] = attempt
        try:
            resp = requests.get(
                url,
                headers=esi_headers(access_token),
                params=params or {},
                timeout=timeout,
            )
            meta["status_code"] = resp.status_code
            meta["headers"] = dict(resp.headers or {})

            # rate-limit / throttling
            if resp.status_code in (420, 429, 503):
                retry_after = resp.headers.get("Retry-After")
                reset = resp.headers.get("X-Esi-Error-Limit-Reset")
                wait_s = None
                if retry_after:
                    try:
                        wait_s = float(retry_after)
                    except ValueError:
                        pass
                if wait_s is None and reset:
                    try:
                        wait_s = float(reset)
                    except ValueError:
                        pass
                if wait_s is None:
                    wait_s = backoff

                # log only on the last attempt to avoid spamming
                if attempt == max_attempts:
                    db_log(
                        level="ERROR",
                        source=source,
                        event=event,
                        message=f"{resp.status_code} for {resp.url}",
                        data=_ctx({**(ctx or {}), "attempts": attempt, "wait_s": wait_s}),
                    )
                    return None, meta

                time.sleep(min(wait_s, 30.0))
                backoff = min(backoff * 2.0, 30.0)
                continue

            resp.raise_for_status()
            return (resp.json() or []), meta

        except (HTTPError, RequestException, ValueError) as e:
            meta["error"] = str(e)

            if attempt == max_attempts:
                db_log(
                    level="ERROR",
                    source=source,
                    event=event,
                    message=str(e),
                    data=_ctx({**(ctx or {}), "attempts": attempt}),
                )
                return None, meta

            time.sleep(min(backoff, 10.0))
            backoff = min(backoff * 2.0, 10.0)

    return None, meta


def _ctx(extra=None):
    data = {
        "host": HOSTNAME,
        "task_id": getattr(getattr(current_task, "request", None), "id", None),
    }
    if extra:
        data.update(extra)
    return data


def _location_name(config: MarketTrackingConfig) -> str:
    if not config:
        return "Unknown"
    if config.scope == "region":
        try:
            return EveRegion.objects.get(id=config.location_id).name
        except EveRegion.DoesNotExist:
            return str(config.location_id)
    else:
        try:
            return TrackedStructure.objects.get(structure_id=config.location_id).name
        except TrackedStructure.DoesNotExist:
            return str(config.location_id)
        
def _parse_esi_datetime(value):
    """
    Convert ESI ISO8601 datetime (with Z) into naive UTC datetime
    safe for MySQL DATETIME.
    """
    if not value:
        return None
    if isinstance(value, str):
        dt = parse_datetime(value)
        if dt:
            return dt.astimezone(_tz.utc).replace(tzinfo=None)
        return None
    if hasattr(value, "tzinfo"):
        return value.astimezone(_tz.utc).replace(tzinfo=None)
    return value


# ========== MARKET (ITEMS) ==========

@shared_task
def fetch_market_data_auto():
    mc = MarketCharacter.objects.first()
    if not mc:
        logger.warning("[MarketTracker] No MarketCharacter found for auto refresh.")
        return
    fetch_market_data(mc.character.character_id)


@shared_task
def fetch_market_data(character_id: int):
    db_log(
        source="items",
        event="start",
        message="fetch_market_data start",
        data=_ctx({"character_id": character_id}),
    )

    config = MarketTrackingConfig.objects.first()
    if not config:
        db_log(
            level="WARN",
            source="items",
            event="no_config",
            message="No MarketTrackingConfig found",
            data=_ctx(),
        )
        return

    yellow_threshold = int(config.yellow_threshold or 50)
    red_threshold = int(config.red_threshold or 25)

    # --- token (structure mode needs token) ---
    try:
        mc = MarketCharacter.objects.get(character__character_id=character_id)
        admin_access_token = mc.token.valid_access_token()
    except MarketCharacter.DoesNotExist:
        db_log(
            level="WARN",
            source="items",
            event="no_market_character",
            message=f"No MarketCharacter found for character_id={character_id}",
            data=_ctx({"character_id": character_id}),
        )
        return
    except Exception as e:
        db_log(
            level="ERROR",
            source="items",
            event="token_refresh_failed",
            message=str(e),
            data=_ctx({"character_id": character_id, "traceback": traceback.format_exc()}),
        )
        return

    orig_table = MARKET_ORDERS_TABLE
    suffix = _task_suffix()
    tmp_table = f"{orig_table}_tmp_{suffix}"
    old_table = f"{orig_table}_old_{suffix}"

    location_name = _location_name(config)

    db_log(
        source="items",
        event="tmp_plan",
        data=_ctx(
            {
                "orig_table": orig_table,
                "tmp_table": tmp_table,
                "old_table": old_table,
                "scope": config.scope,
                "location_id": config.location_id,
            }
        ),
    )

    # used for alerts
    changed_statuses: list[tuple] = []

    try:
        # --- prepare tmp table ---
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{tmp_table}`;")
            cursor.execute(f"CREATE TABLE `{tmp_table}` LIKE `{orig_table}`;")

        db_log(
            source="items",
            event="tmp_ready",
            data=_ctx({"tmp_table": tmp_table, "orig_table": orig_table}),
        )

        # --- import orders into tmp table ---
        if config.scope == "region":
            seen_orders = _fetch_region_orders_sql(config.location_id, table_name=tmp_table)
        else:
            # structure -> uses esi_get_json + _save_orders_sql(table_name,...)
            seen_orders = _fetch_structure_orders(config.location_id, admin_access_token, table_name=tmp_table)

        db_log(
            source="items",
            event="orders_imported",
            data=_ctx(
                {
                    "seen_orders": len(seen_orders),
                    "scope": config.scope,
                    "location_id": config.location_id,
                }
            ),
        )

        if not seen_orders:
            db_log(
                level="WARN",
                source="items",
                event="import_empty_skip_swap",
                message="No orders imported, skipping atomic swap",
                data=_ctx({"tmp_table": tmp_table}),
            )
            # cleanup tmp
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp_table}`;")
            return

        # --- calculate statuses using tmp table (SQL SUM) ---
        tracked_items = list(TrackedItem.objects.select_related("item").all())
        tracked_count = len(tracked_items)

        db_log(
            source="items",
            event="status_calc_start",
            data=_ctx(
                {
                    "tracked_items": tracked_count,
                    "yellow_threshold": yellow_threshold,
                    "red_threshold": red_threshold,
                    "tmp_table": tmp_table,
                }
            ),
        )

        # also count how many items would be RED with total_volume=0
        # to detect a suspicious "all zero"
        would_all_go_red = True
        any_desired_positive = False

        with connection.cursor() as cursor:
            for ti in tracked_items:
                cursor.execute(
                    f"SELECT COALESCE(SUM(volume_remain), 0) "
                    f"FROM `{tmp_table}` WHERE tracked_item_id = %s",
                    [ti.id],
                )
                total_volume = cursor.fetchone()[0] or 0

                desired = int(ti.desired_quantity or 0)
                if desired <= 0:
                    # if desired=0 treat as OK (we do not monitor quantity)
                    percentage = 100
                    new_status = "OK"
                else:
                    any_desired_positive = True
                    percentage = int((int(total_volume) / desired) * 100)
                    if percentage <= red_threshold:
                        new_status = "RED"
                    elif percentage <= yellow_threshold:
                        new_status = "YELLOW"
                    else:
                        new_status = "OK"

                # suspicious check
                if desired > 0:
                    # detect "all-zero => RED" when desired>0 and total_volume == 0 with status RED
                    if not (int(total_volume) == 0 and new_status == "RED"):
                        would_all_go_red = False

                old_status = ti.last_status or "OK"
                if new_status != old_status:
                    # tuple shape matches discord.py:
                    # (i, old_s, new_s, p, t, d)
                    changed_statuses.append((ti, old_status, new_status, percentage, int(total_volume), desired))
                    ti.last_status = new_status
                    ti.save(update_fields=["last_status"])

        db_log(
            source="items",
            event="status_calc_done",
            data=_ctx({"tracked_items": tracked_count, "changed": len(changed_statuses)}),
        )

        # --- suspicious "all zero" protection  ---
        # If ALL monitored items (desired>0) end up RED because total_volume=0,
        # it almost always means: ESI failure / missing permissions / empty response / 403.
        if any_desired_positive and would_all_go_red and changed_statuses:
            db_log(
                level="WARN",
                source="items",
                event="suspicious_all_zero",
                message="Suspicious all-zero snapshot detected; skipping swap+alerts and rolling back statuses",
                data=_ctx({"changed": len(changed_statuses), "tmp_table": tmp_table}),
            )

            # rollback statuses
            for (ti, old_s, new_s, _p, _t, _d) in changed_statuses:
                TrackedItem.objects.filter(pk=ti.pk).update(last_status=old_s)

            # cleanup tmp
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp_table}`;")

            return

        # --- atomic swap FIRST (so deliveries/alerts align with the new snapshot) ---
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{old_table}`;")
            cursor.execute(
                f"RENAME TABLE `{orig_table}` TO `{old_table}`, `{tmp_table}` TO `{orig_table}`;"
            )
            cursor.execute(f"DROP TABLE IF EXISTS `{old_table}`;")

        db_log(
            source="items",
            event="swap_done",
            message="Atomic swap done",
            data=_ctx({"orig_table": orig_table, "tmp_table": tmp_table, "old_table": old_table}),
        )

        # --- deliveries / alerts AFTER swap ---
        _update_deliveries(config)

        if changed_statuses:
            send_items_alert(changed_statuses, location_name)
            items_restocked_alert(changed_statuses, location_name)

    except Exception as e:
        db_log(
            level="ERROR",
            source="items",
            event="exception",
            message=str(e),
            data=_ctx(
                {
                    "traceback": traceback.format_exc(),
                    "tmp_table": tmp_table,
                    "orig_table": orig_table,
                }
            ),
        )
        # cleanup best-effort
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp_table}`;")
        except Exception:
            pass
        return

    finally:
        db_log(source="items", event="end", message="fetch_market_data end", data=_ctx())




def _fetch_region_orders_sql(region_id: int, *, table_name: str) -> set[int]:
    seen_orders: set[int] = set()
    tracked_items = list(TrackedItem.objects.select_related("item").all())

    for tracked in tracked_items:
        type_id = tracked.item.id
        page = 1
        while True:
            url = f"{ESI_BASE_URL}/markets/{region_id}/orders/"
            data, meta = esi_get_json(
                url,
                access_token=None,
                params={"order_type": "sell", "type_id": type_id, "page": page},
                timeout=20,
                source="items",
                event="esi_region_error",
                ctx={"region_id": region_id, "type_id": type_id, "page": page, "url": url},
                max_attempts=4,
            )
            if data is None:
                break

            try:
                pages = int(meta["headers"].get("X-Pages", 1) or 1)
            except ValueError:
                pages = 1

            # data already contains sell orders, but keep the filter defensively
            sell_orders = [o for o in data if isinstance(o, dict) and not o.get("is_buy_order")]
            seen_orders.update(_save_orders_sql(table_name, sell_orders, tracked, region_id))

            if page >= pages:
                break
            page += 1

    return seen_orders



def _fetch_structure_orders(structure_id: int, access_token: str, table_name: str) -> set[int]:
    tracked_map = {
        int(t.item_id): t
        for t in TrackedItem.objects.select_related("item").all()
    }

    seen_orders: set[int] = set()
    page = 1

    while True:
        url = f"{ESI_BASE_URL}/markets/structures/{structure_id}/"
        data, meta = esi_get_json(
            url,
            access_token=access_token,
            params={"page": page},
            timeout=20,
            source="items",
            event="esi_structure_error",
            ctx={"structure_id": structure_id, "page": page, "url": url},
            max_attempts=4,
        )
        if data is None:
            break

        try:
            pages = int(meta["headers"].get("X-Pages", 1) or 1)
        except ValueError:
            pages = 1

        orders_by_tracked: dict[int, list[dict]] = {}

        for order in data:
            if not isinstance(order, dict):
                continue
            if order.get("is_buy_order"):
                continue

            type_id = order.get("type_id")
            if not type_id:
                continue

            tracked = tracked_map.get(int(type_id))
            if not tracked:
                continue

            orders_by_tracked.setdefault(tracked.pk, []).append(order)

        for orders in orders_by_tracked.values():
            tracked = tracked_map[int(orders[0]["type_id"])]
            seen_orders.update(_save_orders_sql(table_name, orders, tracked, structure_id))

        if page >= pages:
            break
        page += 1

    return seen_orders


def _save_orders_sql(
    table_name: str,
    orders: list[dict],
    tracked_item: TrackedItem,
    location_id: int,
) -> set[int]:
    if not orders:
        return set()

    now = _tz.now()
    rows = []
    order_ids = []

    for o in orders:
        if not isinstance(o, dict):
            continue
        oid = o.get("order_id")
        if not oid:
            continue

        oid = int(oid)
        order_ids.append(oid)

        issued = _parse_esi_datetime(o.get("issued")) or now


        rows.append((
            oid,                    # order_id
            tracked_item.id,        # tracked_item_id
            int(location_id),       # structure_id
            float(o.get("price") or 0),
            int(o.get("volume_remain") or 0),
            bool(o.get("is_buy_order", False)),
            issued,
        ))

    if not rows:
        return set()

    # WARNING: columns must match your table
    sql = f"""
        INSERT INTO `{table_name}`
            (`order_id`, `tracked_item_id`, `structure_id`, `price`, `volume_remain`, `is_buy_order`, `issued`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `tracked_item_id` = VALUES(`tracked_item_id`),
            `structure_id`    = VALUES(`structure_id`),
            `price`           = VALUES(`price`),
            `volume_remain`   = VALUES(`volume_remain`),
            `is_buy_order`    = VALUES(`is_buy_order`),
            `issued`          = VALUES(`issued`)
    """

    with connection.cursor() as cursor:
        cursor.executemany(sql, rows)

    return set(order_ids)


def _update_deliveries(config):
    deliveries = Delivery.objects.filter(status="PENDING")

    raw_tokens = [
        t for t in Token.objects.select_related("user").all()
        if t.scopes.filter(name="esi-markets.read_character_orders.v1").exists()
    ]

    valid_tokens = []
    for token in raw_tokens:
        try:
            access_token = token.valid_access_token()
            valid_tokens.append((token, access_token))
        except TokenInvalidError:
            logger.warning(
                "[MarketTracker] Skipping invalid token for char %s (id=%s)",
                token.character_id,
                token.id,
            )
        except Exception:
            logger.exception(
                "[MarketTracker] Token refresh failed for char %s (id=%s)",
                token.character_id,
                token.id,
            )

    if not valid_tokens:
        logger.warning("[MarketTracker] No valid tokens available for deliveries update.")
        return

    for delivery in deliveries:
        total_delivered = 0
        for token, access_token in valid_tokens:
            try:
                orders = _fetch_character_orders(token.character_id, access_token, config)
                filtered = []
                for o in orders:
                    if "issued" not in o or "type_id" not in o:
                        continue
                    issued_dt = parse_datetime(o["issued"])
                    if issued_dt:
                        issued_dt = issued_dt.astimezone(_tz.utc)
                    if (
                        issued_dt
                        and issued_dt >= delivery.created_at
                        and o["type_id"] == delivery.item.id
                        and not o.get("is_buy_order", False)
                    ):
                        filtered.append(o)
                delivered_from_orders = sum(o["volume_remain"] for o in filtered)
                total_delivered += delivered_from_orders
            except Exception:
                logger.exception(
                    "[MarketTracker] Orders fetch failed for char %s", token.character_id
                )

        delivery.delivered_quantity = min(total_delivered, delivery.declared_quantity)
        if delivery.delivered_quantity >= delivery.declared_quantity:
            delivery.status = "FINISHED"
        delivery.save(update_fields=["delivered_quantity", "status"])

def _fetch_character_orders(character_id, access_token, config):
    url = f"{ESI_BASE_URL}/characters/{character_id}/orders/"

    resp = requests.get(url, headers=esi_headers(access_token), timeout=10)
    resp.raise_for_status()
    orders = resp.json()
    if config.scope == "region":
        return [o for o in orders if o.get("region_id") == config.location_id]
    return [o for o in orders if o.get("location_id") == config.location_id]


# ========== CONTRACTS ==========

@shared_task
def refresh_contracts():
    db_log(source="contracts", event="start", message="refresh_contracts start", data=_ctx())

    orig = CONTRACTS_TABLE
    suffix = _task_suffix()
    tmp = f"{orig}_tmp_{suffix}"
    old = f"{orig}_old_{suffix}"

    # --- prepare tmp table ---
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{tmp}`;")
            cursor.execute(f"CREATE TABLE `{tmp}` LIKE `{orig}`;")

            # sanity check: tmp should have id (AUTO PK) if orig has it
            cursor.execute(f"SHOW COLUMNS FROM `{tmp}`;")
            cols = [r[0] for r in cursor.fetchall()]
            db_log(source="contracts", event="tmp_ready", data=_ctx({
                "tmp": tmp,
                "orig": orig,
                "has_id": "id" in cols,
                "col_count": len(cols),
                "cols_head": cols[:20],
            }))

            if "id" not in cols:
                db_log(
                    level="ERROR",
                    source="contracts",
                    event="tmp_missing_id",
                    message="tmp table missing id column; aborting",
                    data=_ctx({"tmp": tmp, "orig": orig}),
                )
                # cleanup
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp}`;")
                return

    except Exception as e:
        db_log(
            level="ERROR",
            source="contracts",
            event="tmp_prepare_failed",
            message=str(e),
            data=_ctx({"traceback": traceback.format_exc(), "tmp": tmp, "orig": orig}),
        )
        return

    try:
        # --- tokens ---
        raw_tokens = [
            t for t in Token.objects.select_related("user").all()
            if t.scopes.filter(name="esi-contracts.read_character_contracts.v1").exists()
        ]

        valid_tokens = []
        for token in raw_tokens:
            try:
                token.valid_access_token()
                valid_tokens.append(token)
            except TokenInvalidError:
                logger.warning(
                    "[MarketTracker] Skipping invalid contracts token for char %s (id=%s)",
                    token.character_id, token.id
                )
            except Exception:
                logger.exception(
                    "[MarketTracker] Token refresh failed for char %s (id=%s)",
                    token.character_id, token.id
                )

        if not valid_tokens:
            db_log(
                level="WARN",
                source="contracts",
                event="no_valid_tokens",
                message="No valid tokens available for contracts refresh",
                data=_ctx(),
            )
            # cleanup tmp
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp}`;")
            return

        # --- fill tmp via SQL ---
        seen = fetch_contracts_snapshots(tmp, valid_tokens)
        db_log(source="contracts", event="fetched", data=_ctx({
            "contracts_seen": int(seen),
            "tmp": tmp,
        }))

        if not seen:
            db_log(
                level="WARN",
                source="contracts",
                event="import_empty_skip_swap",
                message="No contracts imported, skipping atomic swap",
                data=_ctx({"tmp": tmp}),
            )
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp}`;")
            return

        # --- atomic swap ---
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{old}`;")
            cursor.execute(f"RENAME TABLE `{orig}` TO `{old}`, `{tmp}` TO `{orig}`;")
            cursor.execute(f"DROP TABLE IF EXISTS `{old}`;")

        db_log(source="contracts", event="swap_done", message="Atomic snapshot swap done", data=_ctx({
            "orig": orig,
            "tmp": tmp,
            "old": old,
            "contracts_seen": int(seen),
        }))

        # --- now read from orig using normal ORM ---
        all_contracts = list(ContractSnapshot.objects.all())

        cfg = MarketTrackingConfig.objects.first()
        yellow = cfg.yellow_threshold if cfg else 50
        red = cfg.red_threshold if cfg else 25

        summary = _recalculate_contract_statuses_and_alert(all_contracts, yellow, red)
        db_log(source="contracts", event="recalc_done", data=_ctx(summary or {}))

        _update_contract_deliveries(all_contracts)

    except Exception as e:
        logger.exception("[Contracts] Error during contracts refresh: %s", e)
        db_log(
            level="ERROR",
            source="contracts",
            event="exception",
            message=str(e),
            data=_ctx({"traceback": traceback.format_exc(), "tmp": tmp, "orig": orig}),
        )
        # best-effort cleanup of tmp if the swap failed
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{tmp}`;")
        except Exception:
            pass
        raise
    finally:
        db_log(source="contracts", event="end", message="refresh_contracts end", data=_ctx())



def fetch_contracts_snapshots(table_name: str, tokens) -> int:
    import json
    import requests

    seen = 0

    for char in tokens:
        token = getattr(char, "token", char)

        try:
            access_token = token.valid_access_token()
            char_id = token.character_id
            if not isinstance(char_id, int) or char_id < 10:
                continue
        except Exception:
            continue

        page = 1
        while True:
            url = f"{ESI_BASE_URL}/characters/{char_id}/contracts/"
            params = {"page": page}

            try:
                resp = requests.get(url, params=params, headers=esi_headers(access_token), timeout=10)
                resp.raise_for_status()
            except Exception:
                break

            data = resp.json() or []
            pages = int(resp.headers.get("X-Pages", 1) or 1)

            rows = []
            now = _tz.now()
            now_iso = now.isoformat()

            for c in data:
                status = (c.get("status") or "").lower()
                if status != "outstanding":
                    continue

                contract_id = c.get("contract_id")
                if not contract_id:
                    continue

                # items are usually unavailable at this stage -> start with an empty list
                items_json = json.dumps([])

                date_issued = _parse_esi_datetime(c.get("date_issued")) or now
                date_expired = _parse_esi_datetime(c.get("date_expired"))
                date_completed = _parse_esi_datetime(c.get("date_completed"))

                rows.append((
                    int(contract_id),
                    int(char_id),
                    "",
                    c.get("type") or "",
                    c.get("availability") or "",
                    c.get("status") or "",
                    c.get("title") or "",
                    date_issued,
                    date_expired,
                    c.get("start_location_id"),
                    c.get("end_location_id"),
                    c.get("price") or 0,
                    c.get("reward") or 0,
                    c.get("collateral") or 0,
                    c.get("volume") or 0,
                    bool(c.get("for_corporation") or False),
                    c.get("assignee_id"),
                    c.get("acceptor_id"),
                    c.get("issuer_id"),
                    c.get("issuer_corporation_id"),
                    items_json,
                    now,               # fetched_at (datetime, nie string)
                    date_completed,
                ))

            if rows:
                sql = f"""
                    INSERT INTO `{table_name}` (
                        `contract_id`,
                        `owner_character_id`,
                        `owner_character_name`,
                        `type`,
                        `availability`,
                        `status`,
                        `title`,
                        `date_issued`,
                        `date_expired`,
                        `start_location_id`,
                        `end_location_id`,
                        `price`,
                        `reward`,
                        `collateral`,
                        `volume`,
                        `for_corporation`,
                        `assignee_id`,
                        `acceptor_id`,
                        `issuer_id`,
                        `issuer_corporation_id`,
                        `items`,
                        `fetched_at`,
                        `date_completed`
                    )
                    VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    ON DUPLICATE KEY UPDATE
                        `owner_character_id`      = VALUES(`owner_character_id`),
                        `owner_character_name`    = VALUES(`owner_character_name`),
                        `type`                    = VALUES(`type`),
                        `availability`            = VALUES(`availability`),
                        `status`                  = VALUES(`status`),
                        `title`                   = VALUES(`title`),
                        `date_issued`             = VALUES(`date_issued`),
                        `date_expired`            = VALUES(`date_expired`),
                        `start_location_id`       = VALUES(`start_location_id`),
                        `end_location_id`         = VALUES(`end_location_id`),
                        `price`                   = VALUES(`price`),
                        `reward`                  = VALUES(`reward`),
                        `collateral`              = VALUES(`collateral`),
                        `volume`                  = VALUES(`volume`),
                        `for_corporation`         = VALUES(`for_corporation`),
                        `assignee_id`             = VALUES(`assignee_id`),
                        `acceptor_id`             = VALUES(`acceptor_id`),
                        `issuer_id`               = VALUES(`issuer_id`),
                        `issuer_corporation_id`   = VALUES(`issuer_corporation_id`),
                        `items`                   = VALUES(`items`),
                        `fetched_at`              = VALUES(`fetched_at`),
                        `date_completed`          = VALUES(`date_completed`)
                """
                with connection.cursor() as cursor:
                    cursor.executemany(sql, rows)
                seen += len(rows)

            if page >= pages:
                break
            page += 1

    return seen



def _recalculate_contract_statuses_and_alert(all_contracts, yellow, red):
    """
    Recalculate status of tracked contracts.
    IMPORTANT: We preload doctrine contract items once, to avoid ESI spam inside matching loops.
    """

    tracked_qs = TrackedContract.objects.select_related("fitting").all()
    tracked_count = tracked_qs.count()
    snapshot_count = len(all_contracts)

    db_log(
        source="contracts",
        event="recalc_start",
        data=_ctx({
            "tracked_count": tracked_count,
            "snapshot_count": snapshot_count,
        }),
    )

    # Only outstanding item_exchange are relevant for doctrine mode
    doctrine_contracts = [
        c for c in all_contracts
        if (c.type or "").lower() == "item_exchange"
        and (c.status or "").lower() == "outstanding"
    ]

    # Preload items ONCE for doctrine contracts that have no items yet
    # This prevents N*M calls in the matching loops.
    preload_total = 0
    preload_ok = 0
    preload_skipped_has_items = 0

    for c in doctrine_contracts:
        if c.items:
            preload_skipped_has_items += 1
            continue
        owner_id = c.owner_character_id or 0
        preload_total += 1
        try:
            items = fetch_contract_items(c, None, owner_id)
            if items:
                preload_ok += 1
        except Exception as e:
            logger.error(
                "[Contracts] Preload items failed for contract %s owner=%s: %s",
                c.contract_id,
                owner_id,
                e,
            )

    db_log(
        source="contracts",
        event="items_preload_done",
        data=_ctx({
            "doctrine_candidates": len(doctrine_contracts),
            "preload_total": preload_total,
            "preload_ok": preload_ok,
            "preload_skipped_has_items": preload_skipped_has_items,
        }),
    )

    changed = []

    for tc in tracked_qs:
        matched = []

        # base selection depends on mode
        if tc.mode == TrackedContract.Mode.CUSTOM:
            tf = (tc.title_filter or "").lower().strip()
            if not tf:
                base_contracts = []
            else:
                base_contracts = [
                    c for c in all_contracts
                    if tf in (c.title or "").lower()
                ]

        elif tc.mode == TrackedContract.Mode.DOCTRINE:
            base_contracts = doctrine_contracts

        else:
            base_contracts = []

        # pure matching: NO ESI calls here
        for c in base_contracts:
            ok, _reason = contract_matches(tc, c)
            if ok:
                matched.append(c)

        current = len(matched)
        desired = tc.desired_quantity or 0

        if desired <= 0:
            percent = 100
            new_status = "OK"
        else:
            percent = int((current / desired) * 100)
            if percent <= red:
                new_status = "RED"
            elif percent <= yellow:
                new_status = "YELLOW"
            else:
                new_status = "OK"

        old_status = tc.last_status

        if old_status != new_status:
            tc.last_status = new_status
            tc.save(update_fields=["last_status"])

            if tc.mode == TrackedContract.Mode.DOCTRINE and tc.fitting:
                name = tc.fitting.name
            else:
                name = tc.title_filter or "—"

            prices = [float(m.price) for m in matched if getattr(m, "price", None)]
            min_price = min(prices) if prices else None

            changed.append({
                "tc_id": tc.id,  # IMPORTANT: needed for rollback
                "name": name,
                "status": new_status,
                "old_status": old_status,
                "current": current,
                "desired": desired,
                "percent": percent,
                "min_price": min_price,
            })

    db_log(source="contracts", event="alerts_summary", data=_ctx({"changed": len(changed)}))

    if changed:
        suspicious_all_zero = all(
            c["desired"] > 0
            and c["current"] == 0
            and c["status"] == "RED"
            and c["old_status"] != "RED"
            for c in changed
        )

        if suspicious_all_zero:
            db_log(
                level="WARN",
                source="contracts",
                event="suspicious_all_zero",
                message="Suspicious all-zero snapshot detected; skipping alerts",
                data=_ctx({"changed": len(changed)}),
            )

            # Roll back statuses to prevent false alarm spam
            for c in changed:
                TrackedContract.objects.filter(pk=c["tc_id"]).update(
                    last_status=c["old_status"] or "OK"
                )
            return {"changed": len(changed), "alerts_sent": 0, "skipped": "suspicious_all_zero"}

        send_contracts_alert(changed)
        contracts_restocked_alert(changed)

    return {"changed": len(changed)}


def _update_contract_deliveries(all_contracts):
    """
    Delivery auto completion.
    IMPORTANT: Preload doctrine items once to avoid ESI spam in delivery evaluation.
    """
    deliveries = ContractDelivery.objects.select_related("tracked_contract").filter(status="PENDING")

    # Filter doctrine candidates once
    doctrine_contracts = [
        c for c in all_contracts
        if (c.type or "").lower() == "item_exchange"
        and (c.status or "").lower() == "outstanding"
    ]

    # Preload items for doctrine contracts (only when needed)
    for c in doctrine_contracts:
        if c.items:
            continue
        owner_id = c.owner_character_id or 0
        try:
            fetch_contract_items(c, None, owner_id)
        except Exception:
            # don't crash deliveries on preload issues
            continue

    for d in deliveries:
        tc = d.tracked_contract
        matched = 0

        if tc.mode == TrackedContract.Mode.CUSTOM:
            tf = (tc.title_filter or "").lower().strip()
            if tf:
                base = [c for c in all_contracts if tf in (c.title or "").lower()]
            else:
                base = []

        elif tc.mode == TrackedContract.Mode.DOCTRINE:
            base = doctrine_contracts

        else:
            base = []

        for c in base:
            if c.date_issued and c.date_issued < d.created_at:
                continue

            ok, _ = contract_matches(tc, c)
            if ok:
                matched += 1

        d.delivered_quantity = min(matched, d.declared_quantity)
        if d.delivered_quantity >= d.declared_quantity:
            d.status = "FINISHED"
        d.save(update_fields=["delivered_quantity", "status"])
