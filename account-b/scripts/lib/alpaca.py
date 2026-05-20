"""Thin Alpaca paper API client for Account B."""

import os
import time
from typing import Optional

import requests

ALPACA_BASE = os.environ.get("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets/v2")
ALPACA_DATA = os.environ.get("ALPACA_DATA_ENDPOINT", "https://data.alpaca.markets/v2")
KEY = os.environ.get("ALPACA_KEY_B", "")
SECRET = os.environ.get("ALPACA_SECRET_B", "")

HEADERS = {
    "APCA-API-KEY-ID": KEY,
    "APCA-API-SECRET-KEY": SECRET,
    "Content-Type": "application/json",
}


def _require_keys():
    if not KEY or not SECRET:
        raise RuntimeError("ALPACA_KEY_B / ALPACA_SECRET_B not set in environment")


def get_account() -> dict:
    _require_keys()
    r = requests.get(f"{ALPACA_BASE}/account", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get_positions() -> list[dict]:
    _require_keys()
    r = requests.get(f"{ALPACA_BASE}/positions", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get_clock() -> dict:
    _require_keys()
    r = requests.get(f"{ALPACA_BASE}/clock", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get_calendar(start: str, end: str) -> list[dict]:
    """Trading calendar between start and end (YYYY-MM-DD inclusive)."""
    _require_keys()
    r = requests.get(
        f"{ALPACA_BASE}/calendar",
        headers=HEADERS,
        params={"start": start, "end": end},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def get_latest_quote(symbol: str) -> Optional[dict]:
    _require_keys()
    r = requests.get(
        f"{ALPACA_DATA}/stocks/{symbol}/quotes/latest", headers=HEADERS, timeout=15
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("quote")


def submit_opg_order(symbol: str, qty: float, side: str) -> dict:
    """Submit a market-on-open (OPG) order. Fractional supported for 'market' type."""
    _require_keys()
    # OPG TIF requires whole shares per Alpaca docs. For fractional we'd need market + day,
    # but that fills immediately at market open if submitted just before 9:30. Use OPG with
    # rounded shares; tiny dollar drift is acceptable on $25K capital.
    qty_int = max(1, int(round(qty)))
    body = {
        "symbol": symbol,
        "qty": str(qty_int),
        "side": side,
        "type": "market",
        "time_in_force": "opg",
    }
    r = requests.post(f"{ALPACA_BASE}/orders", headers=HEADERS, json=body, timeout=15)
    if r.status_code >= 400:
        return {"error": True, "status": r.status_code, "body": r.text, "submitted": body}
    return r.json()


def list_orders(status: str = "all", limit: int = 100) -> list[dict]:
    _require_keys()
    r = requests.get(
        f"{ALPACA_BASE}/orders",
        headers=HEADERS,
        params={"status": status, "limit": limit, "direction": "desc"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def cancel_all_open_orders() -> None:
    _require_keys()
    requests.delete(f"{ALPACA_BASE}/orders", headers=HEADERS, timeout=15)


def is_market_open_today() -> bool:
    """True if today is a trading day and current time is before next close."""
    clock = get_clock()
    return bool(clock.get("is_open")) or _next_open_is_today(clock)


def _next_open_is_today(clock: dict) -> bool:
    from datetime import datetime
    try:
        next_open = datetime.fromisoformat(clock["next_open"].replace("Z", "+00:00"))
        now = datetime.fromisoformat(clock["timestamp"].replace("Z", "+00:00"))
        return next_open.date() == now.date()
    except Exception:
        return False
