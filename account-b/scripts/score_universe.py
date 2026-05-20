#!/usr/bin/env python3
"""
Nightly scoring job: queries Claude Sonnet 4.6 with web search for each ticker
in UNIVERSE.json and appends scores to RANKINGS-LOG.jsonl.

Schedule: Mon-Fri 18:00 ET (22:00 UTC) via GitHub Actions.

Per-stock budget: up to 3 web searches, ~1500 output tokens.
Expected cost: ~$8/night for 100 stocks with Sonnet 4.6 + web search.

Env: ANTHROPIC_API_KEY, GITHUB_TOKEN, ALPACA_KEY_B (for trading-day check), SMTP_*
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

MODEL = "claude-sonnet-4-5-20250929"  # update string when 4.6 GA available
MAX_RETRIES = 2
WEB_SEARCH_MAX = 3
MAX_TOKENS = 1500
FAILURE_THRESHOLD = 0.10  # abort run if >10% of universe fails


# Standardized prompt per Chen & Pu (2026), Appendix A
PROMPT_TEMPLATE = """You are an expert portfolio manager evaluating {ticker} for a US equity \
nowcasting strategy. Forget all prior conversations.

Use web search to gather the most recent information available: yesterday's close, \
news from the last 24-48 hours, earnings calendar, analyst commentary, and any social \
media sentiment indicators. You may run up to 3 searches.

Then produce attractiveness scores for {ticker} on a -5 to +5 scale, where:
  -5 = Strong Sell (worst possible attractiveness vs all US stocks historically)
   0 = Neutral / market average
  +5 = Strong Buy (best possible attractiveness vs all US stocks historically)

Calibrate your scores against the ENTIRE historical universe of US stocks since 1900, \
not against today's market. A score of +3 should be rare.

Output ONLY the following Python list at the very end of your response, with no \
additional formatting, on its own line, starting with `RESULT=`:

RESULT=[attractiveness_1d, attractiveness_1w, attractiveness_1m, attractiveness_3m, \
attractiveness_6m, attractiveness_1y, price_target_1d, price_target_1w, price_target_1m, \
price_target_3m, price_target_6m, price_target_1y, eps_fy1, eps_fy2, eps_fy3, eps_fy4, \
eps_fy5, earnings_surprise_score, russell_1d, russell_1w, russell_1m, russell_3m, \
russell_6m, russell_1y, market_sentiment, market_divergence]

Where:
- attractiveness_*: float in [-5, 5], scores at each horizon
- price_target_*: float, your predicted closing price at each horizon
- eps_fy1..fy5: float, your EPS forecast for next 5 fiscal years
- earnings_surprise_score: float in [-5, 5], likelihood next report beats consensus
- russell_*: float in [-5, 5], attractiveness of the Russell 1000 index at each horizon \
(used as benchmark control)
- market_sentiment: float in [-5, 5], overall market mood from social/news
- market_divergence: float in [-5, 5], degree of disagreement among market participants

Before the RESULT line, briefly state your reasoning (3-5 sentences max). \
Reasoning must precede RESULT."""


RESULT_PATTERN = re.compile(r"RESULT\s*=\s*(\[[^\]]+\])", re.IGNORECASE)


def is_trading_day_today() -> bool:
    """True if today is a US trading day per Alpaca calendar."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cal = alpaca.get_calendar(today, today)
        return len(cal) > 0 and cal[0].get("date") == today
    except Exception as e:
        print(f"[score] trading-day check failed ({e}); assuming yes")
        return True


def session_date_str() -> str:
    """The trading session this scoring run is FOR (i.e. tomorrow's open)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        cal = alpaca.get_calendar(today, "2030-01-01")
        # Find first calendar entry strictly after today's UTC date
        for entry in cal:
            if entry["date"] > today:
                return entry["date"]
        # Fallback
        return today
    except Exception:
        return today


def parse_result(text: str) -> Optional[list]:
    """Extract the RESULT=[...] list from the model output."""
    m = RESULT_PATTERN.search(text)
    if not m:
        return None
    try:
        raw = m.group(1)
        # Replace `None`/`null`/missing with None; tolerate trailing commas
        raw = raw.replace("null", "None")
        return eval(raw, {"__builtins__": {}}, {"None": None})
    except Exception as e:
        print(f"[score] failed to parse RESULT: {e} | raw: {m.group(1)[:120]}")
        return None


def score_one_ticker(client: anthropic.Anthropic, ticker: str) -> dict:
    """Returns a dict matching the RANKINGS-LOG.jsonl schema."""
    row = {
        "session_date": session_date_str(),
        "scored_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "attractiveness_1d": None,
        "attractiveness_1w": None,
        "attractiveness_1m": None,
        "attractiveness_3m": None,
        "attractiveness_6m": None,
        "attractiveness_1y": None,
        "price_target_1d": None,
        "eps_fy1": None,
        "eps_fy2": None,
        "sentiment": None,
        "divergence": None,
        "russell_1d": None,
        "model": MODEL,
        "web_searches_used": None,
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
            # Concatenate all text blocks (web search produces multi-block responses)
            text = "".join(
                b.text for b in resp.content if getattr(b, "type", None) == "text"
            )
            searches = sum(
                1 for b in resp.content if getattr(b, "type", None) == "server_tool_use"
            )
            row["web_searches_used"] = searches

            result = parse_result(text)
            if result is None or len(result) < 26:
                raise ValueError(
                    f"could not parse 26-item RESULT (got {len(result) if result else 0})"
                )

            row["attractiveness_1d"] = _to_float(result[0])
            row["attractiveness_1w"] = _to_float(result[1])
            row["attractiveness_1m"] = _to_float(result[2])
            row["attractiveness_3m"] = _to_float(result[3])
            row["attractiveness_6m"] = _to_float(result[4])
            row["attractiveness_1y"] = _to_float(result[5])
            row["price_target_1d"] = _to_float(result[6])
            row["eps_fy1"] = _to_float(result[12])
            row["eps_fy2"] = _to_float(result[13])
            row["russell_1d"] = _to_float(result[18])
            row["sentiment"] = _to_float(result[24])
            row["divergence"] = _to_float(result[25])
            return row
        except Exception as e:
            last_err = str(e)
            print(f"[score] {ticker} attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)

    row["error"] = last_err or "unknown"
    return row


def _to_float(x) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def main() -> int:
    print(f"[score] start {datetime.now(timezone.utc).isoformat()}")

    if not is_trading_day_today():
        # Even if today isn't a trading day, the NEXT trading day's session matters.
        # But if we're running on, say, Saturday, the next session is Monday — score Sunday night.
        # Only skip if there's no near-term session (e.g. holiday week scoring would still proceed).
        pass

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

    rows = []
    failures = 0
    for i, ticker in enumerate(tickers, 1):
        print(f"[score] {i}/{len(tickers)} {ticker}")
        row = score_one_ticker(client, ticker)
        rows.append(row)
        if row["error"] is not None:
            failures += 1
        # Polite rate limiting
        time.sleep(1.0)

    fail_rate = failures / len(tickers)
    print(f"[score] complete: {failures}/{len(tickers)} failures ({fail_rate:.1%})")

    # Append to JSONL
    with RANKINGS_FILE.open("a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    if fail_rate > FAILURE_THRESHOLD:
        notify.alert(
            "scoring high failure rate",
            f"{failures}/{len(tickers)} stocks failed ({fail_rate:.1%}). "
            f"Tomorrow's rebalance will SKIP. Investigate.",
            sms=True,
        )
        # Still commit so we have audit trail
        gitops.commit_and_push(
            [str(RANKINGS_FILE.relative_to(REPO_ROOT))],
            f"acct-b scoring HIGH FAILURE {rows[0]['session_date']}",
        )
        return 2

    # Compute top 20 preview for the daily email
    valid = [r for r in rows if r["attractiveness_1d"] is not None]
    valid.sort(key=lambda r: r["attractiveness_1d"], reverse=True)
    top20 = valid[:20]
    preview = ", ".join(f"{r['ticker']}({r['attractiveness_1d']:+.1f})" for r in top20[:10])

    gitops.commit_and_push(
        [str(RANKINGS_FILE.relative_to(REPO_ROOT))],
        f"acct-b scoring {rows[0]['session_date']} ({len(tickers) - failures} ok)",
    )
    notify.send_email(
        f"Acct-B scoring complete {rows[0]['session_date']}",
        f"Scored {len(tickers)} tickers ({failures} failed).\n\n"
        f"Top 10 by attractiveness_1d:\n{preview}\n\n"
        f"Full top 20 will be traded at tomorrow's open.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
