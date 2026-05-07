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
| 2026-05-04 | 20:01 UTC | A | QCOM | CTO Line | BULLISH_FLIP | 168.4 | D | EVALUATED 2026-05-05 — CEO 60/100 (<70); stock ~$179 post-earnings surge, extended +42% past month; needs stabilization; SKIP/WATCH |
| 2026-05-04 | 20:01 UTC | A | GDX | CTO Line | STRONG_BEAR | 85.66 | D | EVALUATED 2026-05-05 — ETF; not tradeable per rules; no position held |
| 2026-05-04 | 20:03 UTC | A | TEVA | CTO Line | STRONG_BULL | 35.38 | D | EVALUATED 2026-05-05 — CEO 66/100 (<70); Q2 earnings 05/06/2026 = skip today; re-evaluate post-print if CEO ≥70 |
| 2026-05-04 | 20:16 UTC | A | SFBQF | CTO Line | BULLISH_FLIP | 1.45 | D | EVALUATED 2026-05-05 — OTC penny stock; SoftBank Corp (Japan); not US stock; SKIP |
| 2026-05-04 | 21:01 UTC | A | SILVER | CTO Line | STRONG_BEAR | 72.735 | D | EVALUATED 2026-05-05 — not a stock (commodity/futures); SKIP |
| 2026-05-05 | 20:01 UTC | A | NET | ? | STRONG_BULL | 244.43 | D | NEW |
| 2026-05-05 | 20:03 UTC | A | DXYZ | ? | STRONG_BULL | 38.31 | D | NEW |
| 2026-05-05 | 20:05 UTC | A | PTON | ? | STRONG_BULL | 5.18 | D | NEW |
| 2026-05-06 | 06:56 UTC | A | 012450 | ? | STRONG_BULL | 1433000 | D | EVALUATED 2026-05-06 — non-US ticker (Hanwha Aerospace KRX); webhook config issue; SKIP |
| 2026-05-06 | 20:01 UTC | A | ARKG | ? | STRONG_BULL | 31.08 | D | EVALUATED 2026-05-06 — ETF (ARK Genomic Revolution); not tradeable per rules; SKIP |
| 2026-05-07 | 20:01 UTC | A | XOVR | ? | STRONG_BULL | 18.88 | D | NEW |
