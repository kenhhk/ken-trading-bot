# Agentic AI Stock Nowcasting — Strategy Brief

**Source:** Chen, Z. & Pu, D. (Jan 2026). *Autonomous Market Intelligence: Agentic AI Nowcasting Predicts Stock Returns.* Peking University Guanghua School of Management. arXiv:2601.11958. Live updates: https://github.com/mapledust0/AI-Stock-Nowcasting/

**Sample:** April 2025 – January 2026. ~158,000 stock-day predictions across Russell 1000.

---

## Core Thesis

A frontier LLM with live web search, queried nightly to score every Russell 1000 stock on attractiveness (-5 to +5), produces an implementable long-only signal that delivers daily Fama-French 6-factor alpha of 18.4 bps (t = 2.46) and an annualized Sharpe of 2.43. The signal is **strongly asymmetric**: works on the long side, fails on the short side.

---

## The Strategy (Mechanics)

**Universe:** Russell 1000 (median market cap ~$15B, median bid-ask spread ~3.4 bps — fully liquid).

**Signal generation:**
- Query a frontier LLM web interface (search enabled) for every constituent
- Time window: after 4:00 PM ET close on day t-1, before market open on day t
- Standardized prompt asks for an attractiveness score from -5 (Strong Sell) to +5 (Strong Buy), calibrated against the entire historical US equity universe
- Prompt also requests scores at multiple horizons (1d / 1w / 1m / 3m / 6m / 1y), price targets, EPS forecasts, sentiment, and divergence scores
- Model is told to act as an expert portfolio manager and provide reasoning

**Portfolio construction:**
- Rank all stocks by today's daily-horizon attractiveness score
- Hold the **top 20** stocks, value-weighted
- Ties broken by larger market cap (favors liquidity)
- Enter at day t opening auction; exit at day t+1 opening auction
- Rebalance every day — no stops, no profit targets, no trade management beyond re-ranking

**Exit rule:** A holding is sold if and only if it drops out of the top 20 on tonight's re-ranking. There is no other exit logic.

---

## Why Open-to-Open (Not Close-to-Close)

Signal is generated overnight. Trading at the open ensures strict temporal separation between signal and return — no look-ahead bias, no overnight gap capture that wouldn't be tradeable. This is the implementation discipline that lets the alpha survive scrutiny.

---

## Headline Performance

| Metric | Top-20 Daily | Russell 1000 |
|---|---|---|
| Cumulative return (9 mo) | ~50% | ~26% |
| Daily FF6 alpha | 18.4 bps (t=2.46) | — |
| Annualized alpha | ~46% | — |
| Sharpe ratio | 2.43 | ~1.0 typical |
| Median bid-ask spread | ~1.6 bps | — |
| Daily turnover | 57% | — |
| Transaction costs as % of gross alpha | <10% | — |

---

## The Asymmetry (Critical)

- **Long side works.** Top-ranked portfolios generate significant positive alpha at daily/weekly/monthly horizons.
- **Short side fails.** Bottom-ranked portfolios produce alphas statistically indistinguishable from zero. A long-short version is not viable.
- **Concentration matters.** Alpha is concentrated in the very top tier. Top-10 alpha ≈ 0.19% daily; Top-50 ≈ 0.16%; Top-100 ≈ 0.12%. Expanding the basket dilutes the signal fast.
- **Authors' hypothesis:** Positive news produces coherent multi-source signals (strong earnings, contract wins, product launches). Negative news is contaminated by corporate spin, social-media "buy the dip" noise, and strategic obfuscation by managers (Kothari et al. 2009).

**Implication:** Run long-only. Do not short bottom-ranked names.

---

## Factor Profile of Top-20

- **Low market beta** (~0.30) — defensive, not high-beta amplification
- **Strong negative HML** (-0.88) — pronounced growth tilt
- **Near-zero SMB** — mega-cap tilt within Russell 1000
- **Insignificant MOM on top side**, strongly negative MOM on bottom side — the AI screens out recent losers but doesn't simply chase winners
- **Null RMW/CMA** — not capturing profitability or investment anomalies

Alpha survives all six factors, so it's not just a growth-factor bet in disguise — but the style profile is unmistakably "quality mega-cap growth."

---

## Core Holdings (Highest Average Scores)

Persistent top names through the sample: AVGO, NVDA, MSFT, APP (AppLovin), META, LLY, GOOGL/GOOG (both classes, correctly identified as equivalent), MA, V, AMPH (Amphenol), MU, VRT (Vertiv), GEV, CEG, CRWD, ANET. Heavy AI infrastructure / mega-cap quality concentration.

NVDA appeared in the daily Top-20 on ~61% of trading days; AVGO ~63%; MSFT ~54%.

---

## Implementation Checklist

1. **Build the nightly query pipeline.** Loop over Russell 1000 tickers; submit each to a frontier LLM web interface with search enabled. Use an identical prompt for every stock.
2. **Standardize the prompt.** Ask for: discrete buy/wait/sell decision; attractiveness scores at multiple horizons calibrated to all US stocks historically; price targets; EPS forecasts; market sentiment; divergence; Russell 1000 benchmark attractiveness for normalization. Require structured output (e.g., a 40-item Python list) for clean extraction.
3. **Extract with regex** from chat logs into a panel dataset (ticker, date, score).
4. **Rank and select top 20** each evening.
5. **Execute at the opening auction** — market-on-open orders for entries and exits.
6. **Rebalance daily.** Expect ~11–12 names rotating in/out per session.
7. **Stay in Russell 1000** to keep spreads tight. The economics require liquid execution.
8. **Track turnover and slippage** continuously; gross alpha is ~18 bps daily, so realized costs above ~5 bps materially erode the edge.

---

## Risks and Caveats

- **Sample period is short and bullish.** Nine months in a mega-cap-led AI infrastructure rally. The growth tilt + low beta combination is exactly what worked in 2025. Performance in a value-led tape, a regime shift, or a tech drawdown is untested.
- **High turnover relies on tight spreads.** Strategy is viable in Russell 1000 only. Don't extend down-cap.
- **Single-model dependency.** Authors don't name the LLM. Results may be highly model-specific; switching providers mid-stream is a real risk.
- **Crowding risk if the approach diffuses.** A genuine 46% annualized alpha cannot persist if many participants run the same playbook. Treat as a window of opportunity, not a perpetual edge.
- **Stochastic generation noise.** Same prompt can yield different scores on re-query. Authors validate stability (split-half ρ = 0.94, rank stability ρ = 0.90), but a single-query design has more noise than averaging multiple queries — consider running 2-3 queries per stock and averaging if cost permits.
- **Data contamination risk going forward.** Future model versions will have absorbed the sample period's outcomes into training data, which is precisely why the original dataset is non-reproducible. Don't backtest using a newer model; it knows what happened.
- **Asymmetric capability is a real limit.** The AI tells you what to buy, not what to sell or short. Risk management must come from elsewhere (position sizing, portfolio-level stops, regime filters).
- **No regime filter in the base strategy.** Consider overlaying a macro filter (VIX threshold, breadth indicator, or equity put/call) to size down or exit during stress regimes — the paper does not test this and it could either help or hurt.

---

## Suggested Extensions (Not in Paper)

- **Ensemble across LLMs.** Query 2-3 frontier models and average scores to reduce single-model risk.
- **Multi-query averaging.** Run each stock 2-3 times and average to reduce stochastic noise.
- **Macro overlay.** Pair the long-only signal with a regime filter (e.g., reduce gross exposure when VIX > 25 or when market breadth deteriorates).
- **Position sizing.** Equal-weight or volatility-weight instead of value-weight, to test whether mega-cap concentration is necessary.
- **Confirmation overlay.** Require both a top attractiveness score and a positive sentiment-divergence reading (genuine consensus vs. crowded narrative) to enter.
- **Defensive exits.** Layer a hard stop (e.g., -8% from entry) over the daily re-ranking, since the AI itself doesn't tell you to sell.

---

## Key Reference Points

- Sample: April 2025 – January 2026, ~158,000 stock-day predictions
- Universe: Russell 1000 (~93% of US market cap)
- Top-20 daily FF6 α: 0.184% (t = 2.46), Sharpe 2.43
- Median bid-ask spread: 3.4 bps universe, 1.6 bps top-20
- Daily turnover: 57% (daily horizon)
- Bottom portfolios: alpha statistically indistinguishable from zero
- Authors: Zefeng Chen, Darcy Pu (zefengchen@gsm.pku.edu.cn, darcypu@pku.edu.cn)
