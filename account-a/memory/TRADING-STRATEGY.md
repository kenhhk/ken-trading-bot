# Account A — Claude Swing Trade — Trading Strategy
# Every workflow reads this first. Never violate these rules.
# To change any rule: update the Master Blueprint first, then update this file.

## Mission
Beat the S&P 500 via disciplined swing trading. Stocks only. Never options.
Starting capital: $25,000 (paper). Account ID: PA34GSDDFIEO.

## Core Rules
1. STOCKS ONLY — no options, no crypto, no leveraged ETFs
2. Max 50 open positions at a time
3. Max 2% of equity per position (1% in VIX Contrarian Mode 35–49)
4. Max 50 trades per week
5. Target 75–85% of capital deployed (keep 15–25% cash)
6. 10% trailing stop on every new position as a real GTC order — immediately after fill
7. Cut losers at -7% from entry — no exceptions, no averaging down
8. Tighten trail to 7% at +15% gain, to 5% at +20% gain
9. Never tighten a stop within 3% of current price
10. Never move a stop down
11. Exit entire sector after 2 consecutive failed trades in that sector
12. Follow sector momentum — don't fight the tape
13. Patience > activity — zero trades in a week is valid
14. CEO synthesis score must be ≥ 70 before any buy (see VIX tiers below)
15. All orders are LIMIT only — never market orders

## VIX Tier System
| VIX | Mode | Min Score | Max Position |
|-----|------|-----------|--------------|
| <20 | Normal | 70 | 2% |
| 20–34 | Elevated Caution | 75 | 2% |
| 35–49 | CONTRARIAN MODE | 80 | 1% |
| 50+ | PAUSE | No new longs | Hold only |

In CONTRARIAN MODE (VIX 35–49):
- Only buy stocks down ≥15% from recent high
- Sector confirmation required (prefer semis, software, AI infrastructure)
- Sentiment override adds +15 to CEO score when all 4 conditions met:
  AAII bears >50% + Fear&Greed <25 + VIX 35–49 + put/call >1.2

## Buy-Side Gate (ALL must pass before any buy order)
1. Total positions after fill ≤ 50
2. Trades this week + 1 ≤ 50
3. Position cost ≤ 2% of equity (1% in Contrarian Mode)
4. Position cost ≤ available cash
5. PDT day-trade count ≤ 2 (leaves room; sub-$25k rule — but at $25k this is less relevant)
6. Specific catalyst documented in today's RESEARCH-LOG.md
7. Stock (not option, not ETF unless approved)
8. CEO synthesis score ≥ threshold for current VIX tier
9. Macro regime ≠ RISK_OFF, unless score ≥ 85

## Sell-Side Rules
- Unrealized loss ≤ -7%: CLOSE IMMEDIATELY
- Thesis broken (news, sector collapse, catalyst gone): close even before -7%
- Up +20% or more: tighten trailing stop to 5%
- Up +15% or more: tighten trailing stop to 7%
- Sector has 2 consecutive failed trades: exit ALL positions in that sector

## Entry Checklist (document before every trade)
- Specific catalyst today?
- Sector in momentum?
- Stop level (7–10% below entry)?
- Target (minimum 2:1 risk/reward)?
- CTO Line signal on this ticker?
- CEO synthesis score?

## Sector Rotation Scan
Monitor these ETFs for rotation signals in pre-market research:
XLK (Tech), XLE (Energy), XLF (Financials), XLV (Health Care),
XLI (Industrials), XLU (Utilities), XLB (Materials), XLC (Comms),
XLRE (Real Estate), XLP (Staples), XLY (Consumer Discretionary)

When rotation detected: increase scan breadth in gaining sector,
reduce exposure in losing sector.

## Signal Sources
1. CTO Line Advanced (TradingView webhook) — see TV-SIGNALS.md
2. Multi-agent CEO scoring (macro + technicals + sentiment + congress)
3. Perplexity pre-market research
4. Sector rotation detection

## Performance Tracking
Compare weekly vs S&P 500 (SPY). Letter grade assigned each Friday.
Win rate, avg return, profit factor tracked in WEEKLY-REVIEW.md.
