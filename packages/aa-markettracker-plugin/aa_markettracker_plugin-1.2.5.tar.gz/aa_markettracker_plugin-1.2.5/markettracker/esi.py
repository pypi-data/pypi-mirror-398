import requests

ESI_BASE = "https://esi.evetech.net/latest"
COMMON = {"datasource": "tranquility"}

def get_market_history(region_id: int, type_id: int):
    """
    Daily market history for a type in a region.
    Returns list[ {date, average, highest, lowest, order_count, volume} ].
    """
    url = f"{ESI_BASE}/markets/{region_id}/history/"
    r = requests.get(url, params={**COMMON, "type_id": type_id}, timeout=15)
    r.raise_for_status()
    return r.json()

def get_type_info(type_id: int, language: str = "en"):
    """Primary: /universe/types/{id} (has 'name')."""
    url = f"{ESI_BASE}/universe/types/{type_id}/"
    r = requests.get(url, params={**COMMON, "language": language}, timeout=10)
    r.raise_for_status()
    return r.json()

def get_type_name(type_id: int, language: str = "en") -> str | None:
    """
    Reliable name resolver:
      1) /universe/types/{id}
      2) fallback: /universe/names (POST [id])
    """
    try:
        info = get_type_info(type_id, language=language)
        name = info.get("name") or info.get("type_name")
        if name:
            return name
    except Exception:
        pass

    try:
        url = f"{ESI_BASE}/universe/names/"
        r = requests.post(url, json=[type_id], params={**COMMON, "language": language}, timeout=10)
        r.raise_for_status()
        arr = r.json()
        if isinstance(arr, list) and arr:
            return arr[0].get("name") or None
    except Exception:
        pass

    return None

def get_best_prices(region_id: int, type_id: int, max_pages: int = 30):
    """
    Returns best prices in region
    """
    base = f"{ESI_BASE}/markets/{region_id}/orders/"

    def _scan(order_type: str):
        best = None
        page = 1
        while True:
            r = requests.get(
                base,
                params={**COMMON, "order_type": order_type, "type_id": type_id, "page": page},
                timeout=10,
            )
            if r.status_code == 404:
                break
            r.raise_for_status()
            data = r.json()
            if not data:
                break

            if order_type == "sell":
                for o in data:
                    p = o.get("price")
                    if p is None:
                        continue
                    best = p if best is None else min(best, p)
            else:  # buy
                for o in data:
                    p = o.get("price")
                    if p is None:
                        continue
                    best = p if best is None else max(best, p)

            # stronicowanie
            xpages = int(r.headers.get("X-Pages", "1"))
            if page >= xpages or page >= max_pages:
                break
            page += 1
        return best

    return {"sell": _scan("sell"), "buy": _scan("buy")}