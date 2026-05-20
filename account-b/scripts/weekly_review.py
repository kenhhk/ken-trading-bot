#!/usr/bin/env python3
"""
Friday weekly review: compute week P&L, benchmark comparison, Sharpe-to-date,
turnover stats. Appends to WEEKLY-REVIEW.md.

Schedule: Fri 16:30 ET (20:30 UTC) via GitHub Actions.

Env: ALPACA_KEY_B, ALPACA_SECRET_B, GITHUB_TOKEN, SMTP_*
"""

import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


WEEKLY_REVIEW = Path(__file__).parent.parent / "memory" / "WEEKLY-REVIEW.md"
TRADE_LOG = Path(__file__).parent.parent / "memory" / "TRADE-LOG.md"
RANKINGS_FILE = Path(__file__).parent.parent / "memory" / "RANKINGS-LOG.jsonl"
REPO_ROOT = WEEKLY_REVIEW.parent.parent.parent

STARTING_CAPITAL = 25000.0


def get_portfolio_history(period: str = "1W") -> dict:
    """Alpaca portfolio history endpoint."""
    r = requests.get(
        f"{alpaca.ALPACA_BASE}/account/portfolio/history",
        headers=alpaca.HEADERS,
        params={"period": period, "timeframe": "1D"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def get_etf_weekly_return(symbol: str) -> Optional[float]:
    """Closing price 5 trading days ago vs latest close. Returns pct return."""
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=10)
        r = requests.get(
            f"{alpaca.ALPACA_DATA}/stocks/{symbol}/bars",
            headers=alpaca.HEADERS,
            params={
                "timeframe": "1Day",
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "adjustment": "all",
            },
            timeout=15,
        )
        r.raise_for_status()
        bars = r.json().get("bars", [])
        if len(bars) < 2:
            return None
        return (bars[-1]["c"] / bars[-5]["c"] - 1) * 100 if len(bars) >= 5 else (
            bars[-1]["c"] / bars[0]["c"] - 1
        ) * 100
    except Exception as e:
        print(f"[weekly] {symbol} fetch failed: {e}")
        return None


def annualized_sharpe(equity_series: list[float]) -> Optional[float]:
    """Simple Sharpe from daily equity, assuming 0% risk-free."""
    if len(equity_series) < 2:
        return None
    rets = [equity_series[i] / equity_series[i - 1] - 1 for i in range(1, len(equity_series))]
    if not rets:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    sd = math.sqrt(var)
    if sd == 0:
        return None
    return (mean / sd) * math.sqrt(252)


def compute_turnover_stats() -> dict:
    """Parse RANKINGS-LOG.jsonl for the last 5 trading sessions; compute top-20 turnover."""
    if not RANKINGS_FILE.exists():
        return {"avg_turnover_pct": None, "sessions_analyzed": 0}
    by_session = {}
    with RANKINGS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('{"_schema'):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            sd = row.get("session_date")
            score = row.get("attractiveness_1d")
            if sd and score is not None:
                by_session.setdefault(sd, []).append((score, row["ticker"]))

    sessions = sorted(by_session.keys())[-5:]
    if len(sessions) < 2:
        return {"avg_turnover_pct": None, "sessions_analyzed": len(sessions)}

    top20s = []
    for sd in sessions:
        rows = sorted(by_session[sd], reverse=True)[:20]
        top20s.append(set(t for _, t in rows))

    turnovers = []
    for i in range(1, len(top20s)):
        new = top20s[i] - top20s[i - 1]
        turnovers.append(len(new) / 20 * 100)
    return {
        "avg_turnover_pct": sum(turnovers) / len(turnovers) if turnovers else None,
        "sessions_analyzed": len(sessions),
    }


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[weekly] start {today}")

    try:
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        history = get_portfolio_history("1W")
    except Exception as e:
        notify.alert("weekly review FAILED", str(e), sms=True)
        return 1

    equity = float(account["equity"])
    equity_series = [e for e in history.get("equity", []) if e is not None]
    week_start_equity = equity_series[0] if equity_series else STARTING_CAPITAL
    week_return = equity - week_start_equity
    week_pct = (week_return / week_start_equity * 100) if week_start_equity else 0
    phase_pct = (equity - STARTING_CAPITAL) / STARTING_CAPITAL * 100

    spy_pct = get_etf_weekly_return("SPY")
    iwb_pct = get_etf_weekly_return("IWB")
    spy_alpha = (week_pct - spy_pct) if spy_pct is not None else None
    iwb_alpha = (week_pct - iwb_pct) if iwb_pct is not None else None

    sharpe = annualized_sharpe(equity_series)
    turnover = compute_turnover_stats()

    positions.sort(key=lambda p: float(p.get("market_value", 0)), reverse=True)
    top5 = [
        f"{p['symbol']} ({float(p['market_value']) / equity * 100:.1f}%)"
        for p in positions[:5]
    ]

    grade = _grade(week_pct, spy_pct)

    review_lines = [
        f"\n## Week ending {today}",
        f"- Equity start: ${week_start_equity:,.2f}",
        f"- Equity end: ${equity:,.2f}",
        f"- Week return: {week_pct:+.2f}% (${week_return:+,.2f})",
        f"- SPY: {spy_pct:+.2f}%" if spy_pct is not None else "- SPY: n/a",
        f"  - Alpha vs SPY: {spy_alpha:+.2f}%" if spy_alpha is not None else "",
        f"- IWB (Russell 1000): {iwb_pct:+.2f}%" if iwb_pct is not None else "- IWB: n/a",
        f"  - Alpha vs IWB: {iwb_alpha:+.2f}%" if iwb_alpha is not None else "",
        f"- Phase return: {phase_pct:+.2f}%",
        f"- Sharpe-to-date (ann.): {sharpe:.2f}" if sharpe is not None else "- Sharpe: n/a",
        f"- Avg daily turnover (last {turnover['sessions_analyzed']} sessions): "
        f"{turnover['avg_turnover_pct']:.0f}%" if turnover["avg_turnover_pct"] is not None
        else "- Turnover: n/a",
        f"- Top 5 holdings: {', '.join(top5)}",
        f"- Grade: {grade}",
        "",
    ]
    review = "\n".join(l for l in review_lines if l != "")

    with WEEKLY_REVIEW.open("a") as f:
        f.write(review)

    email_body = review.strip()
    notify.alert(f"Week {today} {grade}", email_body[:1000], sms=True)

    gitops.commit_and_push(
        [str(WEEKLY_REVIEW.relative_to(REPO_ROOT))],
        f"acct-b weekly review {today}",
    )
    return 0


def _grade(week_pct: float, spy_pct: Optional[float]) -> str:
    if spy_pct is None:
        return "?"
    alpha = week_pct - spy_pct
    if alpha > 2:
        return "A"
    if alpha > 0.5:
        return "B"
    if alpha > -0.5:
        return "C"
    if alpha > -2:
        return "D"
    return "F"


if __name__ == "__main__":
    sys.exit(main())
