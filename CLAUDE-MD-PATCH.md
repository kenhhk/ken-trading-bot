# CLAUDE.md patch — Account B section rewrite

The Account B portion of CLAUDE.md needs to be updated to reflect the new
strategy. Below is the replacement text for the relevant sections.

---

## REPLACE this in the table:

| B | Claude Long Term | Long-term holds via THT indicators | PA39DCU87MFL |

## WITH:

| B | Claude Long Term | Daily-rebalanced top-20 AI nowcasting | PA39DCU87MFL |

---

## REPLACE the "### Account B Specific" section:

### Account B Specific
- Both THT indicators must confirm within 30 days for any trade.
- 15% trailing stop (wider — long-term holds).
- Cut losers at -15% from entry.
- TradingView alerts set to Once Per Bar Close only.
- Partial signals expire after 30 days without confirmation.

## WITH:

### Account B Specific
- Daily-rebalanced top-20 portfolio scored by Claude Sonnet 4.6 nightly.
- Universe: top 100 US mega-caps (refreshed monthly).
- Holdings: exactly 20 positions, value-weighted by market cap.
- Rebalance: market-on-open (OPG) orders at 9:25 ET trigger.
- NO stops, NO profit targets, NO discretionary overrides.
- Exits happen only via re-ranking (drop out of top 20).
- If scoring pipeline fails (>10% null): HOLD existing portfolio, do not rebalance.
- TradingView webhook receiver is NOT used by Account B.
- 60-day trial period from first scoring run.

---

## ADD a new section about Account B's execution model:

### Account B Architecture (different from Account A)
- Runs entirely on GitHub Actions (cron-scheduled Python scripts).
- NOT a Claude Code Cloud Routine — execution is deterministic Python.
- The LLM is invoked only during nightly scoring (Sonnet 4.6 via API).
- Scripts live in account-b/scripts/, workflows in .github/workflows/account-b-*.yml.
- See account-b/SETUP.md for the deployment guide.
