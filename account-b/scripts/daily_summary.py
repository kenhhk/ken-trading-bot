#!/usr/bin/env python3
"""
End-of-day summary: pull final account state, compute P&L, log to TRADE-LOG.md,
email summary.

Schedule: Mon-Fri 16:15 ET (20:15 UTC) via GitHub Actions.

Env: ALPACA_KEY_B, ALPACA_SECRET_B, GITHUB_TOKEN, SMTP_*
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


TRADE_LOG = Path(__file__).parent.parent / "memory" / "TRADE-LOG.md"
REPO_ROOT = TRADE_LOG.parent.parent.parent

STARTING_CAPITAL = 25000.0


def previous_equity() -> float:
    """Scan TRADE-LOG.md backwards for the most recent equity figure. Fallback to starting cap."""
    if not TRADE_LOG.exists():
        return STARTING_CAPITAL
    text = TRADE_LOG.read_text()
    # Match patterns like "Equity: $25,123" or "today_equity: $25,123"
    matches = re.findall(r"Equity:?\s*\$([\d,]+(?:\.\d+)?)", text)
    if not matches:
        return STARTING_CAPITAL
    try:
        return float(matches[-1].replace(",", ""))
    except ValueError:
        return STARTING_CAPITAL


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[summary] start {today}")

    try:
        account = alpaca.get_account()
        positions = alpaca.get_positions()
    except Exception as e:
        notify.alert("daily summary FAILED", str(e), sms=True)
        return 1

    equity = float(account["equity"])
    cash = float(account["cash"])
    yesterday_equity = previous_equity()
    day_pnl = equity - yesterday_equity
    day_pct = (day_pnl / yesterday_equity * 100) if yesterday_equity else 0
    phase_pnl = equity - STARTING_CAPITAL
    phase_pct = (phase_pnl / STARTING_CAPITAL * 100) if STARTING_CAPITAL else 0

    # Sort positions by market value desc
    positions.sort(key=lambda p: float(p.get("market_value", 0)), reverse=True)

    log_lines = [
        f"\n## {today} — EOD Snapshot",
        f"Equity: ${equity:,.2f} | Cash: ${cash:,.2f}",
        f"Day P&L: ${day_pnl:+,.2f} ({day_pct:+.2f}%) | "
        f"Phase P&L: ${phase_pnl:+,.2f} ({phase_pct:+.2f}%)",
        f"Positions: {len(positions)}",
        "",
        "| Ticker | Qty | Avg Entry | Current | Market Value | Unrealized P&L |",
        "|--------|-----|-----------|---------|--------------|----------------|",
    ]
    for p in positions:
        log_lines.append(
            f"| {p['symbol']} | {p['qty']} | ${float(p['avg_entry_price']):.2f} "
            f"| ${float(p['current_price']):.2f} | ${float(p['market_value']):,.2f} "
            f"| ${float(p['unrealized_pl']):+,.2f} ({float(p['unrealized_plpc']) * 100:+.2f}%) |"
        )

    log_entry = "\n".join(log_lines) + "\n"

    with TRADE_LOG.open("a") as f:
        f.write(log_entry)

    # Email summary
    email_lines = [
        f"Equity: ${equity:,.2f} ({day_pct:+.2f}% day / {phase_pct:+.2f}% phase)",
        f"Cash: ${cash:,.2f}",
        f"Positions: {len(positions)}",
        "",
        "Top 5 by market value:",
    ]
    for p in positions[:5]:
        email_lines.append(
            f"  {p['symbol']:<6} ${float(p['market_value']):>10,.0f} "
            f"({float(p['unrealized_plpc']) * 100:+.2f}%)"
        )
    if len(positions) > 5:
        email_lines.append(f"  ...{len(positions) - 5} more")

    notify.send_email(f"Acct-B EOD {today}", "\n".join(email_lines))

    gitops.commit_and_push(
        [str(TRADE_LOG.relative_to(REPO_ROOT))],
        f"acct-b EOD snapshot {today}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
