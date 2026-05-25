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
| 2026-05-07 | 20:16 UTC | A | VISA | ? | BULLISH_FLIP | 29.52 | D | NEW |
| 2026-05-08 | 20:01 UTC | A | PINS | ? | BULLISH_FLIP | 21.29 | D | NEW |
| 2026-05-08 | 20:01 UTC | A | XYLD | ? | BULLISH_FLIP | 40.58 | D | NEW |
| 2026-05-08 | 20:01 UTC | A | BLK | ? | STRONG_BULL | 1084.8 | D | NEW |
| 2026-05-11 | 20:01 UTC | A | QFIN | CTO Line | STRONG_BEAR | 13.19 | D | EVALUATED 2026-05-11 midday — not a held ticker; STRONG_BEAR blocks buys per signal ref; no exit action required |
| 2026-05-11 | 20:16 UTC | A | GLO | ? | BULLISH_FLIP | 0.83 | D | NEW |
| 2026-05-11 | 20:16 UTC | A | ZURVY | ? | STRONG_BEAR | 35.07 | D | NEW |
| 2026-05-12 | 20:01 UTC | A | PG | ? | STRONG_BEAR | 143.93 | D | EVALUATED 2026-05-12 midday — not a held ticker; STRONG_BEAR blocks any PG buys per signal ref; no exit action required |
| 2026-05-13 | 00:00 UTC | A | SOLUSD | ? | BULLISH_FLIP | 94.27 | D | NEW |
| 2026-05-13 | 20:01 UTC | A | VSEC | ? | STRONG_BEAR | 180.41 | D | EVALUATED 2026-05-13 midday — not a held ticker; STRONG_BEAR blocks any VSEC buys per signal ref; no exit action required |
| 2026-05-13 | 20:16 UTC | A | CSU | ? | STRONG_BEAR | 2467.53 | D | EVALUATED 2026-05-13 midday — non-US ticker (likely Constellation Software TSX, share >$2400 also exceeds 2% cap $500); INELIGIBLE; STRONG_BEAR blocks buys regardless; no exit action required |
| 2026-05-14 | 20:01 UTC | A | DUOL | ? | STRONG_BEAR | 109.06 | D | EVALUATED 2026-05-15 midday — not a held ticker; STRONG_BEAR blocks any DUOL buys per signal ref; no exit action required |
| 2026-05-14 | 20:16 UTC | A | SOBKY | ? | STRONG_BULL | 14.02 | D | EVALUATED 2026-05-15 midday — likely non-US ADR/OTC (Sumitomo/Sobha); INELIGIBLE per stocks-only rule; SKIP |
| 2026-05-14 | 23:01 UTC | A | DXY | ? | STRONG_BEAR | 98.869 | D | EVALUATED 2026-05-15 midday — currency index, not a stock; INELIGIBLE |
| 2026-05-15 | 00:00 UTC | A | ADAUSDT | ? | BULLISH_FLIP | 0.2706 | D | EVALUATED 2026-05-15 midday — crypto (Cardano); INELIGIBLE per stocks-only rule |
| 2026-05-15 | 20:01 UTC | A | SMCI | ? | STRONG_BULL | 31.03 | D | NEW |
| 2026-05-15 | 20:16 UTC | A | MTPLF | ? | STRONG_BEAR | 2.0 | D | NEW |
| 2026-05-15 | 23:01 UTC | A | SPX/TVC:XAU | ? | STRONG_BULL | 20.47 | D | NEW |
| 2026-05-18 | 00:00 UTC | A | BNBUSD | ? | STRONG_BULL | 648.02 | D | NEW |
| 2026-05-18 | 20:01 UTC | A | UAL | ? | STRONG_BEAR | 92.57 | D | NEW |
| 2026-05-19 | 20:01 UTC | A | BXMT | ? | STRONG_BEAR | 17.78 | D | NEW |
| 2026-05-20 | 20:01 UTC | A | ACHR | ? | STRONG_BEAR | 5.78 | D | NEW |
| 2026-05-20 | 20:03 UTC | A | SE | ? | STRONG_BEAR | 86.6 | D | NEW |
| 2026-05-20 | 20:05 UTC | A | GDX | ? | STRONG_BEAR | 86.33 | D | NEW |
| 2026-05-20 | 20:07 UTC | A | BP | ? | STRONG_BULL | 45.14 | D | NEW |
| 2026-05-20 | 20:10 UTC | A | KGC | ? | STRONG_BEAR | 28.64 | D | NEW |
| 2026-05-20 | 20:16 UTC | A | ZURVY | ? | BULLISH_FLIP | 36.39 | D | NEW |
| 2026-05-20 | 20:16 UTC | A | VISA | ? | STRONG_BULL | 30.38 | D | NEW |
| 2026-05-21 | 20:01 UTC | A | SCHW | ? | STRONG_BEAR | 90.4 | D | NEW |
| 2026-05-21 | 20:16 UTC | A | BYDDY | ? | STRONG_BEAR | 11.54 | D | NEW |
| 2026-05-22 | 20:01 UTC | A | RYLD | ? | STRONG_BULL | 15.64 | D | NEW |
| 2026-05-22 | 20:16 UTC | A | GLO | ? | STRONG_BEAR | 0.67 | D | NEW |
| 2026-05-23 | 00:01 UTC | A | BNBUSD | ? | STRONG_BULL | 649.19 | D | NEW |
| 2026-05-25 | 23:01 UTC | A | DXY | ? | BULLISH_FLIP | 99.008 | D | NEW |
