# TradingView Webhook Signals Log
# Shared by Account A (CTO signals) and Account B (THT signals)
# Updated by webhook-receiver whenever a TradingView alert fires

## Signal Log Format
| Date | Time | Account | Ticker | Indicator | Signal | Close | Timeframe | Status |
|------|------|---------|--------|-----------|--------|-------|-----------|--------|
| 2026-05-04 | 08:31 UTC | A | 2840 | CTO Line | STRONG_BEAR | 3300 | D | ⚠️ UNRECOGNIZED TICKER — not a US stock; verify webhook config |

## Active Partial Signals (Account B — awaiting confirmation)
*Signals waiting for second indicator confirmation within 30-day window*
| Date Received | Ticker | Indicator | Signal | Expires | Notes |
|---------------|--------|-----------|--------|---------|-------|

## Signal Reference

### Account A — CTO Line Advanced Signals
| Signal | Meaning | CEO Score Impact |
|--------|---------|-----------------|
| BULLISH_FLIP | v1 crosses above v2 — bullish momentum | +15 points |
| STRONG_BULL | Bullish + both lines rising + ATR spread confirms | +25 points |
| WEAK_BULL | Bullish direction but not yet strong | +8 points |
| BEARISH_FLIP | v1 crosses below v2 — bearish momentum | Trigger sell evaluation |
| STRONG_BEAR | Bearish + both falling + strong spread | Immediate sell eval + block buys |
| CONFLICT | Mid lines disagree — choppy | -10 points |

### Account B — THT Indicator Signals
| Signal | Indicator | Meaning |
|--------|-----------|---------|
| BULL_BAND | THT Fair Value Bands (Weekly) | Band red→green — strong bullish reversal |
| EARLY_BULL | THT Fair Value Bands (Weekly) | Dark red→light red — early warning |
| BEAR_BAND | THT Fair Value Bands (Weekly) | Band green→red — strong bearish reversal |
| BX_BULL_STRONG | THT BX Trender (Monthly) | Any red→green — full monthly bull confirm |
| BX_BULL_EARLY | THT BX Trender (Monthly) | Dark red→light red — monthly shift beginning |
| BX_BEAR | THT BX Trender (Monthly) | Green→red — monthly bearish confirm |

### Account B Combination Rules (30-day window)
- BULL_BAND + BX_BULL_EARLY or BX_BULL_STRONG = HIGH CONVICTION BUY
- BEAR_BAND + BX_BEAR = HIGH CONVICTION SELL
- Single signal alone = log and monitor, no action
- Signal older than 30 days without confirmation = EXPIRED
| 2026-05-04 | 20:01 UTC | A | QCOM | CTO Line | BULLISH_FLIP | 168.4 | D | WATCH-TOMORROW — bull thesis intact; AI edge + auto record; stock ~$179 post-earnings surge; evaluate entry at open |
| 2026-05-04 | 20:01 UTC | A | GDX | CTO Line | STRONG_BEAR | 85.66 | D | N/A — ETF, not tradeable per rules; no position held |
| 2026-05-04 | 20:03 UTC | A | TEVA | CTO Line | STRONG_BULL | 35.38 | D | WATCH-TOMORROW — bull thesis intact; Q1 beat (EPS $0.53 vs $0.12 est); duvakitug pipeline; target $41.75; evaluate entry at open |
| 2026-05-04 | 20:16 UTC | A | SFBQF | CTO Line | BULLISH_FLIP | 1.45 | D | ⚠️ FLAG — unrecognized ticker (OTC/pink sheet?); not a standard US exchange stock; verify webhook config |
| 2026-05-04 | 21:01 UTC | A | SILVER | CTO Line | STRONG_BEAR | 72.735 | D | ⚠️ FLAG — not a valid US stock ticker (commodity/futures?); no action; verify webhook config |
