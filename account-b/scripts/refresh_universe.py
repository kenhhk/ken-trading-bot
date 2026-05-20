#!/usr/bin/env python3
"""
Refresh UNIVERSE.json with the top 100 US common stocks by market cap.

Runs monthly via GitHub Actions. Uses a hardcoded seed list updated manually
each month — FMP free tier does not support the screener endpoint.

To update the universe: edit the TOP100 list below and push to main.
The monthly workflow will commit the refreshed UNIVERSE.json automatically.

Env: ALPACA_KEY_B, ALPACA_SECRET_B, GITHUB_TOKEN, SMTP_*
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


UNIVERSE_FILE = Path(__file__).parent.parent / "memory" / "UNIVERSE.json"
REPO_ROOT = UNIVERSE_FILE.parent.parent.parent

# ── Update this list monthly ──────────────────────────────────────────────
# Top 100 US stocks by market cap. Source: public market cap rankings.
# Last updated: May 2026
TOP100 = [
    {"symbol": "NVDA",  "name": "NVIDIA Corporation",                  "sector": "Technology"},
    {"symbol": "MSFT",  "name": "Microsoft Corporation",               "sector": "Technology"},
    {"symbol": "AAPL",  "name": "Apple Inc.",                          "sector": "Technology"},
    {"symbol": "AMZN",  "name": "Amazon.com Inc.",                     "sector": "Consumer Discretionary"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. Class A",               "sector": "Communication Services"},
    {"symbol": "GOOG",  "name": "Alphabet Inc. Class C",               "sector": "Communication Services"},
    {"symbol": "META",  "name": "Meta Platforms Inc.",                  "sector": "Communication Services"},
    {"symbol": "TSLA",  "name": "Tesla Inc.",                          "sector": "Consumer Discretionary"},
    {"symbol": "AVGO",  "name": "Broadcom Inc.",                       "sector": "Technology"},
    {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc.",             "sector": "Financials"},
    {"symbol": "LLY",   "name": "Eli Lilly and Company",               "sector": "Health Care"},
    {"symbol": "JPM",   "name": "JPMorgan Chase & Co.",                "sector": "Financials"},
    {"symbol": "V",     "name": "Visa Inc.",                           "sector": "Financials"},
    {"symbol": "MA",    "name": "Mastercard Incorporated",             "sector": "Financials"},
    {"symbol": "ORCL",  "name": "Oracle Corporation",                  "sector": "Technology"},
    {"symbol": "COST",  "name": "Costco Wholesale Corporation",        "sector": "Consumer Staples"},
    {"symbol": "XOM",   "name": "Exxon Mobil Corporation",             "sector": "Energy"},
    {"symbol": "UNH",   "name": "UnitedHealth Group Incorporated",     "sector": "Health Care"},
    {"symbol": "WMT",   "name": "Walmart Inc.",                        "sector": "Consumer Staples"},
    {"symbol": "NFLX",  "name": "Netflix Inc.",                        "sector": "Communication Services"},
    {"symbol": "AMD",   "name": "Advanced Micro Devices Inc.",         "sector": "Technology"},
    {"symbol": "PM",    "name": "Philip Morris International Inc.",    "sector": "Consumer Staples"},
    {"symbol": "BAC",   "name": "Bank of America Corporation",         "sector": "Financials"},
    {"symbol": "GS",    "name": "The Goldman Sachs Group Inc.",        "sector": "Financials"},
    {"symbol": "QCOM",  "name": "Qualcomm Incorporated",               "sector": "Technology"},
    {"symbol": "MS",    "name": "Morgan Stanley",                      "sector": "Financials"},
    {"symbol": "ABT",   "name": "Abbott Laboratories",                 "sector": "Health Care"},
    {"symbol": "RTX",   "name": "RTX Corporation",                     "sector": "Industrials"},
    {"symbol": "NOW",   "name": "ServiceNow Inc.",                     "sector": "Technology"},
    {"symbol": "INTU",  "name": "Intuit Inc.",                         "sector": "Technology"},
    {"symbol": "AMGN",  "name": "Amgen Inc.",                          "sector": "Health Care"},
    {"symbol": "TXN",   "name": "Texas Instruments Incorporated",      "sector": "Technology"},
    {"symbol": "AXP",   "name": "American Express Company",            "sector": "Financials"},
    {"symbol": "PG",    "name": "The Procter & Gamble Company",        "sector": "Consumer Staples"},
    {"symbol": "GE",    "name": "GE Aerospace",                        "sector": "Industrials"},
    {"symbol": "CRM",   "name": "Salesforce Inc.",                     "sector": "Technology"},
    {"symbol": "ISRG",  "name": "Intuitive Surgical Inc.",             "sector": "Health Care"},
    {"symbol": "SPGI",  "name": "S&P Global Inc.",                     "sector": "Financials"},
    {"symbol": "BLK",   "name": "BlackRock Inc.",                      "sector": "Financials"},
    {"symbol": "HON",   "name": "Honeywell International Inc.",        "sector": "Industrials"},
    {"symbol": "PLD",   "name": "Prologis Inc.",                       "sector": "Real Estate"},
    {"symbol": "AMAT",  "name": "Applied Materials Inc.",              "sector": "Technology"},
    {"symbol": "MU",    "name": "Micron Technology Inc.",              "sector": "Technology"},
    {"symbol": "PANW",  "name": "Palo Alto Networks Inc.",             "sector": "Technology"},
    {"symbol": "ANET",  "name": "Arista Networks Inc.",                "sector": "Technology"},
    {"symbol": "ADI",   "name": "Analog Devices Inc.",                 "sector": "Technology"},
    {"symbol": "LRCX",  "name": "Lam Research Corporation",            "sector": "Technology"},
    {"symbol": "APP",   "name": "AppLovin Corporation",                "sector": "Technology"},
    {"symbol": "KLAC",  "name": "KLA Corporation",                     "sector": "Technology"},
    {"symbol": "MCD",   "name": "McDonald's Corporation",              "sector": "Consumer Discretionary"},
    {"symbol": "WFC",   "name": "Wells Fargo & Company",               "sector": "Financials"},
    {"symbol": "CEG",   "name": "Constellation Energy Corporation",    "sector": "Utilities"},
    {"symbol": "UBER",  "name": "Uber Technologies Inc.",              "sector": "Industrials"},
    {"symbol": "CRWD",  "name": "CrowdStrike Holdings Inc.",           "sector": "Technology"},
    {"symbol": "PH",    "name": "Parker-Hannifin Corporation",         "sector": "Industrials"},
    {"symbol": "BSX",   "name": "Boston Scientific Corporation",       "sector": "Health Care"},
    {"symbol": "TMO",   "name": "Thermo Fisher Scientific Inc.",       "sector": "Health Care"},
    {"symbol": "CDNS",  "name": "Cadence Design Systems Inc.",         "sector": "Technology"},
    {"symbol": "SNPS",  "name": "Synopsys Inc.",                       "sector": "Technology"},
    {"symbol": "VRT",   "name": "Vertiv Holdings Co",                  "sector": "Industrials"},
    {"symbol": "KKR",   "name": "KKR & Co. Inc.",                      "sector": "Financials"},
    {"symbol": "ADP",   "name": "Automatic Data Processing Inc.",      "sector": "Technology"},
    {"symbol": "MSTR",  "name": "MicroStrategy Incorporated",          "sector": "Technology"},
    {"symbol": "CB",    "name": "Chubb Limited",                       "sector": "Financials"},
    {"symbol": "PGR",   "name": "The Progressive Corporation",          "sector": "Financials"},
    {"symbol": "PFE",   "name": "Pfizer Inc.",                         "sector": "Health Care"},
    {"symbol": "GILD",  "name": "Gilead Sciences Inc.",                "sector": "Health Care"},
    {"symbol": "BKNG",  "name": "Booking Holdings Inc.",               "sector": "Consumer Discretionary"},
    {"symbol": "ICE",   "name": "Intercontinental Exchange Inc.",      "sector": "Financials"},
    {"symbol": "NKE",   "name": "Nike Inc.",                           "sector": "Consumer Discretionary"},
    {"symbol": "DHR",   "name": "Danaher Corporation",                 "sector": "Health Care"},
    {"symbol": "WELL",  "name": "Welltower Inc.",                      "sector": "Real Estate"},
    {"symbol": "APH",   "name": "Amphenol Corporation",                "sector": "Technology"},
    {"symbol": "ECL",   "name": "Ecolab Inc.",                         "sector": "Materials"},
    {"symbol": "AXON",  "name": "Axon Enterprise Inc.",                "sector": "Industrials"},
    {"symbol": "HCA",   "name": "HCA Healthcare Inc.",                 "sector": "Health Care"},
    {"symbol": "CME",   "name": "CME Group Inc.",                      "sector": "Financials"},
    {"symbol": "TT",    "name": "Trane Technologies plc",              "sector": "Industrials"},
    {"symbol": "EMR",   "name": "Emerson Electric Co.",                "sector": "Industrials"},
    {"symbol": "AON",   "name": "Aon plc",                             "sector": "Financials"},
    {"symbol": "CTAS",  "name": "Cintas Corporation",                  "sector": "Industrials"},
    {"symbol": "USB",   "name": "U.S. Bancorp",                        "sector": "Financials"},
    {"symbol": "SO",    "name": "The Southern Company",                "sector": "Utilities"},
    {"symbol": "TDG",   "name": "TransDigm Group Incorporated",        "sector": "Industrials"},
    {"symbol": "APO",   "name": "Apollo Global Management Inc.",       "sector": "Financials"},
    {"symbol": "GEV",   "name": "GE Vernova Inc.",                     "sector": "Industrials"},
    {"symbol": "COF",   "name": "Capital One Financial Corporation",   "sector": "Financials"},
    {"symbol": "SHW",   "name": "The Sherwin-Williams Company",        "sector": "Materials"},
    {"symbol": "PLTR",  "name": "Palantir Technologies Inc.",          "sector": "Technology"},
    {"symbol": "DUK",   "name": "Duke Energy Corporation",             "sector": "Utilities"},
    {"symbol": "COP",   "name": "ConocoPhillips",                      "sector": "Energy"},
    {"symbol": "MCO",   "name": "Moody's Corporation",                 "sector": "Financials"},
    {"symbol": "WDAY",  "name": "Workday Inc.",                        "sector": "Technology"},
    {"symbol": "PSA",   "name": "Public Storage",                      "sector": "Real Estate"},
    {"symbol": "ITW",   "name": "Illinois Tool Works Inc.",            "sector": "Industrials"},
    {"symbol": "TFC",   "name": "Truist Financial Corporation",        "sector": "Financials"},
    {"symbol": "CVX",   "name": "Chevron Corporation",                 "sector": "Energy"},
    {"symbol": "CARR",  "name": "Carrier Global Corporation",          "sector": "Industrials"},
    {"symbol": "ABNB",  "name": "Airbnb Inc.",                         "sector": "Consumer Discretionary"},
    {"symbol": "LIN",   "name": "Linde plc",                           "sector": "Materials"},
]


def verify_alpaca_tradeable(tickers: list[str]) -> list[str]:
    """Filter to only Alpaca-tradeable tickers. Warns on any that are missing."""
    try:
        import requests
        r = requests.get(
            f"{alpaca.ALPACA_BASE}/assets",
            headers=alpaca.HEADERS,
            params={"status": "active", "asset_class": "us_equity"},
            timeout=30,
        )
        r.raise_for_status()
        tradeable = {a["symbol"] for a in r.json() if a.get("tradable")}
        missing = [t for t in tickers if t not in tradeable]
        if missing:
            print(f"[universe] WARNING: not tradeable on Alpaca: {missing}")
        return [t for t in tickers if t in tradeable]
    except Exception as e:
        print(f"[universe] Alpaca tradeable check failed ({e}); using full list")
        return tickers


def main() -> int:
    print(f"[universe] refresh started {datetime.now(timezone.utc).isoformat()}")

    tickers_all = [t["symbol"] for t in TOP100]
    tradeable = verify_alpaca_tradeable(tickers_all)
    details = [t for t in TOP100 if t["symbol"] in tradeable]

    payload = {
        "last_refreshed": datetime.now(timezone.utc).isoformat(),
        "source": "Hardcoded seed list — update TOP100 in refresh_universe.py monthly",
        "method": f"top {len(details)} US common stocks by market cap (manual seed)",
        "tickers": [t["symbol"] for t in details],
        "details": details,
        "notes": "FMP free tier does not support screener; using curated seed list instead.",
    }

    UNIVERSE_FILE.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[universe] wrote {len(details)} tickers to {UNIVERSE_FILE}")

    gitops.commit_and_push(
        [str(UNIVERSE_FILE.relative_to(REPO_ROOT))],
        f"acct-b universe refresh ({len(details)} tickers)",
    )
    notify.send_email(
        "Acct-B universe refreshed",
        f"{len(details)} tickers loaded.\nFirst 10: {', '.join(payload['tickers'][:10])}",
    )
    print("[universe] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
