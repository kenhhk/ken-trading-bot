# Account B — Claude Long Term — Trading Strategy
# Every job reads this first. Never violate these rules.

## Mission
Daily-rebalanced top-20 long-only portfolio using agentic AI nowcasting.
Adaptation of Chen & Pu (2026) "Autonomous Market Intelligence: Agentic AI
Nowcasting Predicts Stock Returns" (arXiv:2601.11958), scaled to a top-100
mega-cap universe to control API cost while preserving the design.
Starting capital: $25,000 (paper). Account ID: PA39DCU87MFL.

## Trial Period
60 trading days from first scoring run. Re-evaluate against benchmarks before
continuing, modifying, or scaling.

## Core Philosophy
- Every weeknight after close, score the top-100 universe by AI attractiveness.
- Each morning, hold the value-weighted top 20 by score.
- Exits happen via re-ranking only — when a stock drops out of the top 20.
- No stops, no profit targets, no thesis review, no discretionary overrides.
- Fully invested at all times. Cash drag is the enemy.
- The AI's scoring IS the strategy. Do not second-guess individual picks.

## Universe
- Top 100 US stocks by market cap, refreshed monthly (UNIVERSE.json).
- Stocks only — no ETFs, no ADRs that don't trade as ordinary common stock.
- Must be Alpaca-tradeable on the paper API.

## Hard Rules
1. STOCKS ONLY — no options, no crypto, no leveraged ETFs
2. Target exactly 20 positions held at all times (after first trading day)
3. Value-weighted: position size proportional to market cap among held names
4. Daily rebalance at the opening auction using last night's scores
5. MARKET-ON-OPEN orders only (Alpaca limit order with `extended_hours: false`
   submitted before 9:28 AM ET — see rebalance.py)
6. Tie-break for inclusion at rank 20: larger market cap wins
7. No stops, no profit targets, no manual exits
8. If scoring pipeline failed last night: HOLD existing portfolio, do not
   rebalance, send alert email
9. If Alpaca account is in PDT lockout or any restriction: HOLD, alert

## Scoring Protocol
- Job: account-b-scoring (GitHub Actions, Mon-Fri 18:00 ET / 22:00 UTC)
- Model: claude-sonnet-4-6 with web search tool enabled
- Per-stock budget: up to 3 web searches, ~1500 output tokens
- Prompt: standardized per Appendix A of the paper, asking for attractiveness
  scores on 1d/1w/1m/3m/6m/1y horizons, price targets, EPS forecasts, sentiment
  and divergence — but only attractiveness_1d is used for ranking
- Output: append one JSONL row per stock to RANKINGS-LOG.jsonl
- On any per-stock failure: retry once, then record null score and continue
- If >10% of universe fails: abort the run, alert, do not produce a top-20

## Rebalance Protocol
- Job: account-b-rebalance (GitHub Actions, Mon-Fri 09:25 ET / 13:25 UTC)
- Read last night's RANKINGS-LOG.jsonl rows (must be dated today's session)
- Compute target portfolio: top 20 by attractiveness_1d, value-weighted by mcap
- Get current Alpaca positions
- Diff: SELLS = held - target; BUYS = target - held; HOLDS = intersect
- For HOLDS: compute weight delta. Rebalance only if |delta| > 1% of equity
- Submit all SELL market-on-open orders first
- Wait 60 seconds for fills
- Submit all BUY market-on-open orders with rebalanced sizes
- Wait 60 seconds, log fill status
- If any order rejected: alert immediately, do not retry inside this run

## Order Mechanics
- Alpaca does not have a true MOO order type. Use:
  POST /v2/orders {"type":"market", "time_in_force":"opg", ...}
  This is Alpaca's "market-on-open" equivalent — fills at the next open auction
  if submitted before 9:28 AM ET, otherwise rejected.
- All orders must use `time_in_force: "opg"` for the daily rebalance.
- Fractional shares ARE allowed (Alpaca supports them) to hit exact value
  weights on $25K capital.

## Failure Modes (explicit handling)
- Scoring job fails entirely: skip rebalance, hold yesterday's portfolio
- Scoring job partial fail (>10% null): same as above
- Rebalance job fails after some orders sent: alert, manual review required
- Anthropic API outage during scoring: retry 3x with backoff, then null and continue
- Alpaca API outage during rebalance: alert, hold
- Market is closed (holiday): both jobs detect and exit cleanly

## What This Strategy Is NOT
- Not a short-side strategy. The paper found zero alpha on bottom-ranked picks.
- Not a regime-aware strategy in v1. No VIX gating, no stop-out on drawdown.
  This is intentional for the trial; revisit at 60-day review.
- Not a stock-picker's strategy. The AI's reasoning is informational; the
  human (Ken) does not override individual picks during the trial.

## Source Reference
Chen, Z. & Pu, D. (Jan 2026). Autonomous Market Intelligence: Agentic AI
Nowcasting Predicts Stock Returns. arXiv:2601.11958.
Headline result on Russell 1000: 18.4 bps daily FF6 alpha, Sharpe 2.43.
We expect attenuated performance on the smaller top-100 universe.
Strategy brief: see /strategy-brief.md in repo root.
