# Ken's AI Trading Bot

Autonomous dual-account trading system using Claude Code Cloud Routines.

## Accounts
| Account | Nickname | Strategy |
|---------|----------|----------|
| PA34GSDDFIEO | Claude Swing Trade | Short-term swing + CTO Line signals |
| PA39DCU87MFL | Claude Long Term | Long-term holds via THT indicators |

## Architecture
- **Scheduler**: Claude Code Cloud Routines (cron-based, ephemeral containers)
- **Memory**: Git commits to main (markdown files)
- **Research**: Perplexity API (sonar-pro)
- **Execution**: Alpaca paper trading API
- **Signals**: TradingView webhooks → Railway receiver → TV-SIGNALS.md
- **Notifications**: SMTP email + email-to-SMS

## Security
- No API keys in any committed file
- All secrets in Claude Code Routine environment variables
- Webhook secret validates all TradingView signals
- See env.template for required variables

## Master Blueprint
Full system design documented in Master Blueprint (Google Docs).
To change any rule or parameter: update the Blueprint first, then update the corresponding memory file.

## Quick Reference — Wrapper Scripts
```bash
bash account-a/scripts/alpaca.sh account          # Account A portfolio
bash account-b/scripts/alpaca.sh account          # Account B portfolio
bash account-a/scripts/perplexity.sh "query"      # Market research
bash account-a/scripts/notify.sh "message"        # SMS + Email alert
```
