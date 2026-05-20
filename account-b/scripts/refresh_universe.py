#!/usr/bin/env python3
"""
Refresh UNIVERSE.json with the top 100 US common stocks by market cap.

Runs monthly via GitHub Actions. Uses FMP (Financial Modeling Prep) for
market cap rankings, then filters to Alpaca-tradeable common stocks.

Env: FMP_API_KEY, ALPACA_KEY_B, ALPACA_SECRET_B, GITHUB_TOKEN
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


UNIVERSE_FILE = Path(__file__).parent.parent / "memory" / "UNIVERSE.json"
FMP_KEY = os.environ.get("FMP_API_KEY", "")
TARGET_SIZE = 100


def fetch_top_mcap_tickers(n: int = 200) -> list[dict]:
    """Get top-n US stocks by market cap from FMP. We over-fetch to allow for filtering."""
    if not FMP_KEY:
        raise RuntimeError("FMP_API_KEY not set")
    url = (
        f"https://financialmodelingprep.com/api/v3/stock-screener"
        f"?marketCapMoreThan=10000000000"
        f"&exchange=NYSE,NASDAQ"
        f"&isEtf=false"
        f"&isFund=false"
        f"&isActivelyTrading=true"
        f"&limit={n}"
        f"&apikey={FMP_KEY}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Sort by market cap descending
    data.sort(key=lambda x: x.get("marketCap", 0) or 0, reverse=True)
    return data


def filter_alpaca_tradeable(candidates: list[dict]) -> list[dict]:
    """Keep only tickers Alpaca will accept for paper trading."""
    # Pull Alpaca's active+tradeable US equity list once
    r = requests.get(
        f"{alpaca.ALPACA_BASE}/assets",
        headers=alpaca.HEADERS,
        params={"status": "active", "asset_class": "us_equity"},
        timeout=30,
    )
    r.raise_for_status()
    alpaca_assets = {
        a["symbol"]: a
        for a in r.json()
        if a.get("tradable") and a.get("status") == "active"
    }

    kept = []
    for c in candidates:
        sym = c.get("symbol", "").upper()
        if sym in alpaca_assets:
            kept.append(
                {
                    "symbol": sym,
                    "name": c.get("companyName", ""),
                    "market_cap": c.get("marketCap"),
                    "sector": c.get("sector", ""),
                }
            )
    return kept


def main() -> int:
    print(f"[universe] refresh started {datetime.now(timezone.utc).isoformat()}")
    try:
        candidates = fetch_top_mcap_tickers(n=200)
        print(f"[universe] fetched {len(candidates)} candidates from FMP")
        tradeable = filter_alpaca_tradeable(candidates)
        print(f"[universe] {len(tradeable)} are Alpaca-tradeable")
        top_n = tradeable[:TARGET_SIZE]

        if len(top_n) < TARGET_SIZE:
            notify.alert(
                "universe refresh WARN",
                f"Only {len(top_n)} tradeable tickers found (target {TARGET_SIZE})",
                sms=False,
            )

        payload = {
            "last_refreshed": datetime.now(timezone.utc).isoformat(),
            "source": "FMP stock-screener + Alpaca tradeable filter",
            "method": f"top {TARGET_SIZE} US common stocks by market cap, NYSE/NASDAQ",
            "tickers": [t["symbol"] for t in top_n],
            "details": top_n,
            "notes": "",
        }
        UNIVERSE_FILE.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"[universe] wrote {UNIVERSE_FILE} with {len(top_n)} tickers")

        gitops.commit_and_push(
            [str(UNIVERSE_FILE.relative_to(UNIVERSE_FILE.parent.parent.parent))],
            f"acct-b universe refresh ({len(top_n)} tickers)",
        )
        notify.send_email(
            "Acct-B universe refreshed",
            f"Top {len(top_n)} mega-caps loaded. "
            f"First 10: {', '.join(payload['tickers'][:10])}",
        )
        return 0
    except Exception as e:
        print(f"[universe] FAILED: {e}")
        notify.alert("universe refresh FAILED", str(e), sms=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
