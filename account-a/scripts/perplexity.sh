#!/usr/bin/env bash
# Perplexity research wrapper — shared by both accounts
# Usage: bash account-a/scripts/perplexity.sh "<query>"
# Exits with code 3 if PERPLEXITY_API_KEY is unset (caller falls back to WebSearch)

set -euo pipefail

query="${1:-}"
if [[ -z "$query" ]]; then
  echo "usage: perplexity.sh \"<query>\"" >&2
  exit 1
fi

if [[ -z "${PERPLEXITY_API_KEY:-}" ]]; then
  echo "WARNING: PERPLEXITY_API_KEY not set. Fall back to WebSearch." >&2
  exit 3
fi

MODEL="${PERPLEXITY_MODEL:-sonar-pro}"

payload="$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [
    {
      'role': 'system',
      'content': 'You are a precise financial research assistant. Cite every claim with sources. Be concise and factual. Focus on actionable market data.'
    },
    {'role': 'user', 'content': sys.argv[2]},
  ],
}))
" "$MODEL" "$query")"

curl -fsS https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload"
echo
