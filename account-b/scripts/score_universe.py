#!/usr/bin/env python3
"""
Nightly scoring job: queries Claude with web search for each ticker
in UNIVERSE.json and appends scores to RANKINGS-LOG.jsonl.

Cost-optimized version:
- Stripped prompt to only what drives decisions (attractiveness_1d)
- MAX_TOKENS = 400 (was 1500)
- WEB_SEARCH_MAX = 1 (was 3)
- Model: claude-haiku-4-5 for cost; swap to sonnet if quality is poor

Expected cost: ~$1-2/night for 100 stocks.

Schedule: Mon-Fri 18:00 ET (22:00 UTC) via GitHub Actions.
Env: ANTHROPIC_API_KEY, GITHUB_TOKEN, ALPACA_KEY_B, SMTP_*
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


UNIVERSE_FILE = Path(__file__).parent.parent / "memory" / "UNIVERSE.json"
RANKINGS_FILE = Path(__file__).parent.parent / "memory" / "RANKINGS-LOG.jsonl"
REPO_ROOT = UNIVERSE_FILE.parent.parent.parent

# Cost levers — adjust here
MODEL = "claude-haiku-4-5-20251001"   # cheapest capable model; swap to claude-sonnet-4-5-20250929 if needed
MAX_RETRIES = 1
WEB_SEARCH_MAX = 1                     # 1 search per stock keeps cost low
MAX_TOKENS = 400                       # enough for reasoning + RESULT line
FAILURE_THRESHOLD = 0.10


# Lean prompt — only asks for what we actually use
PROMPT_TEMPLATE = """You are an expert portfolio manager. Evaluate {ticker} for a 1-day horizon.

Run 1 web search to get the latest news, price action, and analyst sentiment for {ticker}.

Then output a single attractiveness score on a scale of -5 to +5:
  -5 = Strong Sell (extremely unattractive vs all US stocks historically)
   0 = Neutral
  +5 = Strong Buy (extremely attractive vs all US stocks historically)

Calibrate against the ENTIRE historical US equity universe since 1900. Scores above +3 or below -3 should be rare.

Write 2-3 sentences of reasoning, then output exactly this on the last line:
RESULT={{score}}

Where {{score}} is a single float. Example: RESULT=1.5"""


RESULT_PATTERN = re.compile(r"RESULT\s*=\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)


def session_date_str() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        cal = alpaca.get_calendar(today, "2030-01-01")
        for entry in cal:
            if entry["date"] > today:
                return entry["date"]
        return today
    except Exception:
        return today


def parse_result(text: str) -> Optional[float]:
    m = RESULT_PATTERN.search(text)
    if not m:
        return None
    try:
        val = float(m.group(1))
        return max(-5.0, min(5.0, val))  # clamp to valid range
    except (ValueError, TypeError):
        return None


def score_one_ticker(client: anthropic.Anthropic, ticker: str, session_date: str) -> dict:
    row = {
        "session_date": session_date,
        "scored_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "attractiveness_1d": None,
        "model": MODEL,
        "web_searches_used": 0,
        "error": None,
    }

    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                tools=[
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": WEB_SEARCH_MAX,
                    }
                ],
                messages=[
                    {"role": "user", "content": PROMPT_TEMPLATE.format(ticker=ticker)}
                ],
            )
            text = "".join(
                b.text for b in resp.content if getattr(b, "type", None) == "text"
            )
            searches = sum(
                1 for b in resp.content
                if getattr(b, "type", None) in ("server_tool_use", "tool_use")
            )
            row["web_searches_used"] = searches

            score = parse_result(text)
            if score is None:
                raise ValueError(f"could not parse RESULT from: {text[-200:]}")

            row["attractiveness_1d"] = score
            return row

        except Exception as e:
            last_err = str(e)
            print(f"[score] {ticker} attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

    row["error"] = last_err or "unknown"
    return row


def main() -> int:
    print(f"[score] start {datetime.now(timezone.utc).isoformat()}")

    if not UNIVERSE_FILE.exists():
        notify.alert("scoring FAILED", "UNIVERSE.json missing", sms=True)
        return 1

    universe = json.loads(UNIVERSE_FILE.read_text())
    tickers = universe.get("tickers", [])
    if not tickers:
        notify.alert("scoring FAILED", "UNIVERSE.json has 0 tickers", sms=True)
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        notify.alert("scoring FAILED", "ANTHROPIC_API_KEY not set", sms=True)
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    session_date = session_date_str()
    print(f"[score] session_date={session_date}, model={MODEL}, tickers={len(tickers)}")

    rows = []
    failures = 0
    for i, ticker in enumerate(tickers, 1):
        print(f"[score] {i}/{len(tickers)} {ticker}")
        row = score_one_ticker(client, ticker, session_date)
        rows.append(row)
        if row["error"] is not None:
            failures += 1
        time.sleep(0.5)  # gentle rate limiting

    fail_rate = failures / len(tickers)
    print(f"[score] complete: {failures}/{len(tickers)} failures ({fail_rate:.1%})")

    with RANKINGS_FILE.open("a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    if fail_rate > FAILURE_THRESHOLD:
        notify.alert(
            "scoring high failure rate",
            f"{failures}/{len(tickers)} stocks failed ({fail_rate:.1%}). "
            f"Tomorrow's rebalance will SKIP.",
            sms=True,
        )
        gitops.commit_and_push(
            [str(RANKINGS_FILE.relative_to(REPO_ROOT))],
            f"acct-b scoring HIGH FAILURE {session_date}",
        )
        return 2

    valid = [r for r in rows if r["attractiveness_1d"] is not None]
    valid.sort(key=lambda r: r["attractiveness_1d"], reverse=True)
    top20 = valid[:20]
    preview = ", ".join(
        f"{r['ticker']}({r['attractiveness_1d']:+.1f})" for r in top20[:10]
    )

    gitops.commit_and_push(
        [str(RANKINGS_FILE.relative_to(REPO_ROOT))],
        f"acct-b scoring {session_date} ({len(tickers) - failures} ok)",
    )
    notify.send_email(
        f"Acct-B scoring complete {session_date}",
        f"Scored {len(tickers)} tickers ({failures} failed).\n\n"
        f"Top 10 by attractiveness_1d:\n{preview}\n\n"
        f"Full top 20 will be traded at tomorrow's open.\n\n"
        f"Model: {MODEL} | Searches: 1/stock",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
