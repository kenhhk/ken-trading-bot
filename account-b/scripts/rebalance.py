#!/usr/bin/env python3
"""
Morning rebalance to the top-20 portfolio by attractiveness_1d (value-weighted).

Schedule: Mon-Fri 09:25 ET (13:25 UTC) via GitHub Actions.
Runs ~5 min before market open, submits OPG orders that fill at the 9:30 auction.

Reads: RANKINGS-LOG.jsonl (must contain rows for today's session_date)
       UNIVERSE.json (for market cap weights)
Executes: Alpaca paper account B

Env: ALPACA_KEY_B, ALPACA_SECRET_B, GITHUB_TOKEN, SMTP_*
"""

import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib import alpaca, gitops, notify  # noqa: E402


UNIVERSE_FILE = Path(__file__).parent.parent / "memory" / "UNIVERSE.json"
RANKINGS_FILE = Path(__file__).parent.parent / "memory" / "RANKINGS-LOG.jsonl"
TRADE_LOG = Path(__file__).parent.parent / "memory" / "TRADE-LOG.md"
REPO_ROOT = UNIVERSE_FILE.parent.parent.parent

TARGET_HOLDINGS = 20
REBALANCE_THRESHOLD_BPS = 100  # only rebalance an existing holding if weight delta >1%
ORDER_WAIT_SECONDS = 60


def load_todays_scores() -> list[dict]:
    """Return scores for the most recent session_date in the log.

    Using latest session_date rather than today's date handles:
    - Monday holidays (Friday scores labeled Tuesday still get picked up)
    - GitHub Actions cron delays crossing midnight
    - Any timezone edge cases around UTC date boundaries
    """
    all_rows: dict = {}
    with RANKINGS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('{"_schema'):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("attractiveness_1d") is not None:
                sd = row.get("session_date")
                if sd:
                    all_rows.setdefault(sd, []).append(row)
    if not all_rows:
        return []
    latest = max(all_rows.keys())
    print(f"[rebalance] using scores for session_date={latest} ({len(all_rows[latest])} rows)")
    return all_rows[latest]


def load_universe_mcaps() -> dict[str, float]:
    universe = json.loads(UNIVERSE_FILE.read_text())
    return {d["symbol"]: float(d.get("market_cap") or 0) for d in universe.get("details", [])}


def compute_target_portfolio(
    scores: list[dict], mcaps: dict[str, float], equity: float
) -> dict[str, dict]:
    """
    Returns {ticker: {weight, dollar, shares_estimate, score}}.
    Top 20 by attractiveness_1d, ties broken by market cap, value-weighted by mcap.
    """
    enriched = []
    for r in scores:
        mcap = mcaps.get(r["ticker"], 0)
        enriched.append((r["attractiveness_1d"], mcap, r))
    enriched.sort(key=lambda x: (-x[0], -x[1]))
    top = enriched[:TARGET_HOLDINGS]

    total_mcap = sum(x[1] for x in top)
    if total_mcap == 0:
        print("[rebalance] WARNING: no market cap data, using equal weighting")
        for score, mcap, row in top:
            target[row["ticker"]] = {
                "weight": 1 / TARGET_HOLDINGS,
                "dollar": equity / TARGET_HOLDINGS,
                "score": score,
                "mcap": 0,
            }
    else:
        for score, mcap, row in top:
            weight = mcap / total_mcap
            target[row["ticker"]] = {
                "weight": weight,
                "dollar": equity * weight,
                "score": score,
                "mcap": mcap,
            }
    return target


def diff_portfolios(
    current: dict[str, dict], target: dict[str, dict]
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """
    Returns (sells, buys) where each is a list of (ticker, dollar_amount).
    Positive dollar = buy, negative dollar in sells means sell that many dollars.
    """
    sells = []
    buys = []

    for ticker, pos in current.items():
        cur_value = float(pos["market_value"])
        if ticker not in target:
            # Drop entirely
            sells.append((ticker, cur_value))
        else:
            target_value = target[ticker]["dollar"]
            delta = target_value - cur_value
            if abs(delta) / max(target_value, 1) > REBALANCE_THRESHOLD_BPS / 10000:
                if delta < 0:
                    sells.append((ticker, -delta))
                else:
                    buys.append((ticker, delta))

    for ticker, tgt in target.items():
        if ticker not in current:
            buys.append((ticker, tgt["dollar"]))

    return sells, buys


def estimate_shares(dollar: float, last_price: float) -> int:
    if last_price <= 0:
        return 0
    return max(0, int(math.floor(dollar / last_price)))


def get_reference_prices(tickers: list[str]) -> dict[str, float]:
    """Latest quote midpoints for share-count estimation."""
    out = {}
    for t in tickers:
        try:
            q = alpaca.get_latest_quote(t)
            if q:
                bid = float(q.get("bp") or 0)
                ask = float(q.get("ap") or 0)
                if bid > 0 and ask > 0:
                    out[t] = (bid + ask) / 2
                elif ask > 0:
                    out[t] = ask
        except Exception as e:
            print(f"[rebalance] quote fetch failed for {t}: {e}")
    return out


def main() -> int:
    print(f"[rebalance] start {datetime.now(timezone.utc).isoformat()}")

    # Verify today is a trading day (not weekend/holiday)
    # OPG orders can be submitted any time after previous close up to 9:28 AM ET
    try:
        today_str_check = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cal = alpaca.get_calendar(today_str_check, today_str_check)
        if not cal or cal[0].get("date") != today_str_check:
            print("[rebalance] today is not a trading day; exiting")
            return 0
        print(f"[rebalance] confirmed trading day: {today_str_check}")
    except Exception as e:
        notify.alert("rebalance calendar check failed", str(e), sms=True)
        return 1

    # Load today's scores
    scores = load_todays_scores()
    if len(scores) < TARGET_HOLDINGS * 2:
        notify.alert(
            "rebalance SKIPPED",
            f"Only {len(scores)} valid scores for today's session — need >={TARGET_HOLDINGS * 2}. "
            f"Holding existing portfolio.",
            sms=True,
        )
        return 0

    # Pull state
    try:
        account = alpaca.get_account()
        positions = alpaca.get_positions()
    except Exception as e:
        notify.alert("rebalance Alpaca down", str(e), sms=True)
        return 1

    equity = float(account["equity"])
    current = {p["symbol"]: p for p in positions}
    mcaps = load_universe_mcaps()

    target = compute_target_portfolio(scores, mcaps, equity)
    sells, buys = diff_portfolios(current, target)

    print(f"[rebalance] equity ${equity:,.0f}, {len(current)} held, {len(target)} target")
    print(f"[rebalance] {len(sells)} sells, {len(buys)} buys")

    # Cancel any stray open orders first
    try:
        alpaca.cancel_all_open_orders()
    except Exception as e:
        print(f"[rebalance] cancel_all warning: {e}")

    # Sells first to free capital
    reference_prices = get_reference_prices([t for t, _ in sells + buys])
    sell_results = []
    for ticker, dollar in sells:
        last = reference_prices.get(ticker, 0)
        shares = estimate_shares(dollar, last) if ticker in target else int(
            float(current[ticker]["qty"])
        )
        if shares <= 0:
            continue
        result = alpaca.submit_opg_order(ticker, shares, "sell")
        sell_results.append((ticker, shares, result))
        print(f"[rebalance] SELL {ticker} {shares}sh: {result.get('id', result.get('error'))}")

    if sell_results:
        time.sleep(ORDER_WAIT_SECONDS)

    # Buys
    buy_results = []
    for ticker, dollar in buys:
        last = reference_prices.get(ticker, 0)
        shares = estimate_shares(dollar, last)
        if shares <= 0:
            print(f"[rebalance] skipping {ticker}: no price or 0 shares")
            continue
        result = alpaca.submit_opg_order(ticker, shares, "buy")
        buy_results.append((ticker, shares, result))
        print(f"[rebalance] BUY  {ticker} {shares}sh: {result.get('id', result.get('error'))}")

    # Wait for fills
    time.sleep(ORDER_WAIT_SECONDS)
    final_orders = alpaca.list_orders(status="all", limit=200)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    todays_orders = [o for o in final_orders if o.get("submitted_at", "").startswith(today_str)]

    # Summary
    fills = [o for o in todays_orders if o.get("status") == "filled"]
    rejects = [o for o in todays_orders if o.get("status") in ("rejected", "canceled", "expired")]

    summary_lines = [
        f"Equity: ${equity:,.0f}",
        f"Target: {len(target)} positions, sells: {len(sell_results)}, buys: {len(buy_results)}",
        f"Filled: {len(fills)}, Rejected/Cancelled: {len(rejects)}",
        "",
        "Today's target portfolio (top 20 by score, value-weighted by mcap):",
    ]
    for ticker, info in sorted(target.items(), key=lambda x: -x[1]["weight"]):
        summary_lines.append(
            f"  {ticker:<6} score:{info['score']:+.2f} weight:{info['weight'] * 100:5.2f}% "
            f"target: ${info['dollar']:,.0f}"
        )
    if rejects:
        summary_lines.append("\nRejected orders:")
        for o in rejects:
            summary_lines.append(
                f"  {o['symbol']} {o['side']} {o['qty']}: {o.get('status')} {o.get('reason', '')}"
            )

    summary = "\n".join(summary_lines)
    print(summary)

    # Append to TRADE-LOG.md
    with TRADE_LOG.open("a") as f:
        f.write(f"\n## {today_str} — Rebalance\n```\n{summary}\n```\n")

    gitops.commit_and_push(
        [str(TRADE_LOG.relative_to(REPO_ROOT))],
        f"acct-b rebalance {today_str}",
    )

    sms = len(rejects) > 0
    notify.alert(
        f"rebalance {today_str}: {len(fills)} fills",
        summary[:500],
        sms=sms,
    )
    return 0 if not rejects else 2


if __name__ == "__main__":
    sys.exit(main())
