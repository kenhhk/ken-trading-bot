# Account B — Claude Long Term — Trading Strategy
# Every workflow reads this first. Never violate these rules.

## Mission
Long-term position trading using THT indicators. Hold months to years.
Starting capital: $25,000 (paper). Account ID: PA39DCU87MFL.

## Core Philosophy
- BOTH indicators must confirm within 30 days — never act on one alone
- Weekly candles for THT Fair Value Bands. Monthly candles for THT BX Trender.
- Hold through noise. Long-term positions not managed on daily swings.
- Exits are deliberate — both indicators must confirm reversal before selling.
- Patience is the entire strategy. Fewer trades, higher conviction, longer hold.

## Core Rules
1. STOCKS ONLY — no options, no crypto
2. Max 50 open positions
3. Max 2% of equity per position
4. Max 50 trades per week
5. BOTH THT indicators must confirm same direction within 30 days
6. TradingView alerts set to Once Per Bar Close ONLY (prevents repainting)
7. 15% trailing stop on every new position (wider for long-term holds)
8. Cut losers at -15% from entry
9. Partial signals expire after 30 days without confirmation
10. All orders are LIMIT only

## Buy Signal (HIGH CONVICTION — BOTH required within 30 days)
### Strong Buy (highest conviction)
- THT Fair Value Bands: band red → green (weekly chart) AND
- THT BX Trender: red → green (monthly chart)

### Standard Buy
- THT Fair Value Bands: band red → green OR dark red → light red (weekly) AND
- THT BX Trender: dark red → light red OR red → green (monthly)

## Sell Signal (BOTH required within 30 days)
- THT Fair Value Bands: band green → red (weekly) AND
- THT BX Trender: green → red (monthly)

## Partial Signal Handling
1. First indicator fires → log to TV-SIGNALS.md with expiry date (30 days)
2. Monitor second indicator daily
3. If second confirms within 30 days → HIGH CONVICTION signal → CEO agent evaluation
4. If 30 days pass with no confirmation → mark EXPIRED, clear from active monitoring
5. Never act on a single indicator alone

## Buy-Side Gate (ALL must pass)
1. Both indicators confirmed in same direction within 30 days
2. CEO synthesis score ≥ 70
3. Total positions after fill ≤ 50
4. Position cost ≤ 2% of equity
5. Position cost ≤ available cash
6. Stock is not already held (no doubling up)

## Stop & Exit Rules
- 15% trailing stop placed immediately as GTC order after fill
- Cut at -15% from entry — no exceptions
- Review positions at weekly/monthly bar closes only (not daily noise)
- Both indicators must confirm reversal before manual exit

## Signal Sources
1. THT Fair Value Bands — TradingView webhook (weekly bar close alerts)
2. THT BX Trender — TradingView webhook (monthly bar close alerts)
3. Signal correlation logic in TV-SIGNALS.md

## THT Indicator Links
- Fair Value Bands: https://www.tradingview.com/v/1KU7Ib7Y/
- BX Trender: https://www.tradingview.com/v/PfVt9iUL/
- Author: pdicarlotrader (both are protected scripts)
- BX Trender REPAINTS on live bars — always use Once Per Bar Close alerts
