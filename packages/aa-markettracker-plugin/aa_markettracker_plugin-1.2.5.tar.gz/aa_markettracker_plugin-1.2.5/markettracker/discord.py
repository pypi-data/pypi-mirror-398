import logging

import requests
from django.conf import settings
from django.utils import timezone

from .models import DiscordMessage, DiscordWebhook
from .utils import resolve_ping_target

logger = logging.getLogger(__name__)


def _iter_webhook_urls():
    for wh in DiscordWebhook.objects.all():
        url = (wh.url or "").strip()
        if url:
            yield url


def _get_ping_string(dm: DiscordMessage, which: str) -> str:
    if which == "items":
        if dm.item_ping_choice in ("here", "everyone"):
            return f"@{dm.item_ping_choice}"
        if dm.item_ping_group:
            return f"@{dm.item_ping_group.name}"
        return ""
    else:
        if dm.contract_ping_choice in ("here", "everyone"):
            return f"@{dm.contract_ping_choice}"
        if dm.contract_ping_group:
            return f"@{dm.contract_ping_group.name}"
        return ""


def _post_embed(embed: dict, ping: str = ""):
    payload = {
        "username": "Market Tracker",
        
        "content": ping or "", "embeds": [embed]
        }
    headers = {"User-Agent": getattr(settings, "ESI_USER_AGENT", "MarketTracker/1.0")}
    for url in _iter_webhook_urls():
        try:
            requests.post(url, json=payload, headers=headers, timeout=6)
        except Exception:
            logger.exception("[MarketTracker] Discord send failed for %s", url)


def send_items_alert(changed_items, location_name: str):
    """
    Alert when item goes YELLOW or RED.
    changed_items tuple:
    (item, old_status, new_status, percent, total, desired)
    """

    filtered = [
        (item, old_s, new_s, percent, total, desired)
        for (item, old_s, new_s, percent, total, desired) in changed_items
        if new_s in ("YELLOW", "RED")
        and not (old_s == "RED" and new_s == "YELLOW")
    ]

    if not filtered:
        return

    dm = DiscordMessage.objects.first()
    header = (
        dm.item_alert_header
        if dm and dm.item_alert_header
        else "⚠️ MarketTracker Items"
    )

    embed = {
        "title": f"Items status changes in {location_name}",
        "description": header,
        "color": 0xFF0000,
        "fields": [],
        "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
    }

    for item, _old_status, new_status, percent, total, desired in filtered:
        embed["fields"].append({
            "name": item.item.name,
            "value": f"**{new_status}** ({percent}%) – {total}/{desired}",
            "inline": False,
        })

    ping_str = _get_ping_string(dm, "items") if dm else ""
    _post_embed(embed, resolve_ping_target(ping_str))



def items_restocked_alert(changed_items, location_name: str):
    """
    Alert when item goes back to OK.
    changed_items tuple:
    (item, old_status, new_status, percent, total, desired)
    """

    filtered = [
        (item, old_s, new_s, percent, total, desired)
        for (item, old_s, new_s, percent, total, desired) in changed_items
        if new_s == "OK" and old_s in ("YELLOW", "RED")
    ]

    if not filtered:
        return

    dm = DiscordMessage.objects.first()
    header = (
        dm.item_alert_header
        if dm and dm.item_alert_header
        else "⚠️ MarketTracker Items"
    )

    embed = {
        "title": f"Items restocked in {location_name}",
        "description": header,
        "color": 0x00AA00,
        "fields": [],
        "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
    }

    for item, old_status, _new_status, percent, total, desired in filtered:
        embed["fields"].append({
            "name": item.item.name,
            "value": (
                f"✅ **RESTOCKED** ({percent}%) – "
                f"{total}/{desired} (before: {old_status})"
            ),
            "inline": False,
        })

    ping_str = _get_ping_string(dm, "items") if dm else ""
    _post_embed(embed, resolve_ping_target(ping_str))



def send_contracts_alert(changed_rows):
    changed_rows = [r for r in changed_rows if r.get("status") in ("YELLOW", "RED")]
    if not changed_rows:
        return

    dm = DiscordMessage.objects.first()
    header = (dm.contract_alert_header if dm and dm.contract_alert_header else "📦 MarketTracker Contracts")

    embed = {
        "title": "Tracked Contracts status changes",
        "description": header,
        "color": 0xFF0000,
        "fields": [],
        "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
    }
    for r in changed_rows:
        line = f"**{r['status']}** ({r['percent']}%) – {r['current']}/{r['desired']}"
        if r.get("min_price") is not None:
            line += f" | min: {r['min_price']:.2f} ISK"
        embed["fields"].append({"name": r["name"], "value": line, "inline": False})

    ping_str = _get_ping_string(dm, "contracts") if dm else ""
    _post_embed(embed, resolve_ping_target(ping_str))


def contracts_restocked_alert(changed_rows):
    rows_ok = [
        r for r in changed_rows
        if r.get("status") == "OK" and r.get("old_status") and r["old_status"] != "OK"
    ]
    if not rows_ok:
        return

    dm = DiscordMessage.objects.first()
    header = (
        dm.contract_alert_header
        if dm and dm.contract_alert_header
        else "📦 MarketTracker Contracts – Restocked"
    )

    embed = {
        "title": "Tracked Contracts restocked",
        "description": header,
        "color": 0x008000,
        "fields": [],
        "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
    }

    for r in rows_ok:
        line = f"**{r['status']}** ({r['percent']}%) – {r['current']}/{r['desired']}"
        if r.get("min_price") is not None:
            line += f" | min: {r['min_price']:.2f} ISK"
        embed["fields"].append({"name": r["name"], "value": line, "inline": False})

    ping_str = _get_ping_string(dm, "contracts") if dm else ""
    _post_embed(embed, resolve_ping_target(ping_str))
