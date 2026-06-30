from typing import Optional

try:
    import requests
except Exception:
    requests = None


def _read_json(url: str, timeout: int = 12):
    if requests is None:
        return None
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "legoprice/1.0"},
    )
    response.raise_for_status()
    return response.json()


def _extract_isk_rate(payload: dict) -> Optional[float]:
    if not isinstance(payload, dict):
        return None

    if payload.get("success") is False:
        return None
    if payload.get("result") not in (None, "success"):
        return None

    rates = payload.get("rates") or {}
    value = rates.get("ISK")
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return None
    return rate if rate > 0 else None


def fetch_usd_to_isk(timeout: int = 12) -> Optional[float]:
    if requests is None:
        return None

    urls = [
        "https://api.frankfurter.app/latest?from=USD&to=ISK",
        "https://open.er-api.com/v6/latest/USD",
    ]

    for url in urls:
        try:
            payload = _read_json(url, timeout=timeout)
            rate = _extract_isk_rate(payload)
            if rate is not None:
                return rate
        except Exception:
            continue

    return None
