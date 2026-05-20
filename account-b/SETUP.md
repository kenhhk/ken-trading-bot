# Account B Setup — AI Nowcasting Strategy

This guide gets the new Account B strategy running. Strategy details are in
`account-b/memory/TRADING-STRATEGY.md`. Theory and source paper are in
`/strategy-brief.md` at the repo root.

## What changed
Account B was previously a long-term THT-indicator strategy. It's been
replaced with a daily-rebalanced top-20 portfolio scored each night by Claude
Sonnet 4.6 with web search. The TradingView webhook receiver on Railway is
NOT used by Account B anymore — Account A still uses it.

## One-time setup

### 1. Add required secrets to the GitHub repo
Already in repo secrets: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`

You need to add:
- `ALPACA_KEY_B` — paper Alpaca key for Account B
- `ALPACA_SECRET_B` — paper Alpaca secret
- `FMP_API_KEY` — Financial Modeling Prep (free tier works, used monthly only)
- `NOTIFY_EMAIL` — kenhhk@gmail.com
- `NOTIFY_PHONE` — +16462343838
- `SMTP_USER` — Gmail address sending notifications
- `SMTP_PASS` — Gmail App Password (NOT your regular password)

Add via: GitHub repo → Settings → Secrets and variables → Actions → New repository secret

### 2. Disable the old Account B alerts (manual, on TradingView)
The THT Fair Value Bands and BX Trender alerts that targeted Account B
should be paused or deleted on TradingView. Account A's CTO alerts stay active.

### 3. Populate the universe
First scoring run needs UNIVERSE.json to have tickers. Trigger the
universe refresh manually:

```
GitHub repo → Actions → "Acct-B Universe Refresh" → Run workflow
```

This will populate `account-b/memory/UNIVERSE.json` with the top 100 US
mega-caps and commit it.

### 4. Test the scoring pipeline (recommended before going live)
```
GitHub repo → Actions → "Acct-B Nightly Scoring" → Run workflow
```

Watch the run. It should take 15-30 min. You'll get an email with the top 10
preview when it finishes. Check `account-b/memory/RANKINGS-LOG.jsonl` —
should have ~100 new rows.

If failure rate is >10%, the run will alert and skip tomorrow's rebalance.

### 5. Verify the rebalance logic dry-run
The rebalance script will run automatically Mon-Fri at 9:25 ET. Before the
first real run, you can manually trigger it after a successful scoring run to
verify it produces sensible output. The script will submit real OPG orders
to the PAPER account.

## Schedule

| Job | When (UTC) | When (ET) | What |
|---|---|---|---|
| account-b-scoring | Mon-Fri 22:00 | Mon-Fri 18:00 EDT / 17:00 EST | Score 100 tickers |
| account-b-rebalance | Mon-Fri 13:25 | Mon-Fri 09:25 EDT / 08:25 EST | Submit OPG orders |
| account-b-summary | Mon-Fri 20:15 | Mon-Fri 16:15 EDT / 15:15 EST | EOD snapshot |
| account-b-weekly | Fri 20:30 | Fri 16:30 EDT / 15:30 EST | Weekly review |
| account-b-universe | 1st of month 22:00 | 1st 18:00 EDT / 17:00 EST | Refresh mega-cap list |

Note: GitHub Actions cron is best-effort and can be delayed 5-15 min during
peak load. The 9:25 ET rebalance is timed early to allow for this. OPG
orders are valid until 9:28 ET cutoff, then fill at 9:30 auction.

## Cost expectations

| Component | Cost |
|---|---|
| Nightly scoring (Sonnet 4.6, 100 stocks, ~3 searches each) | ~$8/night |
| Estimated monthly Anthropic spend | $160-200 |
| GitHub Actions | Free (well under 2,000 min/month) |
| FMP free tier | $0 (250 calls/day, monthly refresh uses ~2) |
| Alpaca paper | $0 |

## Monitoring

- **Every weekday morning**: Check email for "Acct-B scoring complete" (sent ~6:30 PM the night before) and "Acct-B rebalance" (sent ~9:32 AM)
- **Every weekday afternoon**: "Acct-B EOD" email at ~4:20 PM
- **Friday afternoon**: "Acct-B Week [date]" SMS + email at ~4:35 PM
- **Anytime something fails**: SMS alert

## Files to watch

| File | Purpose |
|---|---|
| `account-b/memory/UNIVERSE.json` | Current top-100 mega-cap list |
| `account-b/memory/RANKINGS-LOG.jsonl` | All historical scores (append-only) |
| `account-b/memory/TRADE-LOG.md` | Daily rebalance summaries + EOD snapshots |
| `account-b/memory/WEEKLY-REVIEW.md` | Weekly performance vs SPY/IWB |

## At day 60

The strategy spec says re-evaluate after 60 trading days. Suggested checklist:
- Compare cumulative return vs SPY and IWB
- Compute realized annualized Sharpe
- Estimate FF6 alpha (will need to compute factor returns separately)
- Measure realized slippage vs assumed (rebalance log has fill prices)
- Decide: continue, modify, scale up, or stop

## Killing the bot

If something is going wrong and you want to stop it cold:
1. Go to repo Settings → Actions → General → "Disable Actions" — stops all runs immediately
2. Manually close Alpaca positions if needed (paper account, no real risk)
3. Edit `account-b/memory/TRADING-STRATEGY.md` to note the pause and why
