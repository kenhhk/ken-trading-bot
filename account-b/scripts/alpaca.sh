#!/usr/bin/env bash
# Account B — Claude Long Term — Alpaca API wrapper
# Usage: bash account-b/scripts/alpaca.sh <subcommand> [args...]
# NEVER call curl directly. Always use this script.

set -euo pipefail

: "${ALPACA_KEY_B:?ALPACA_KEY_B not set in environment}"
: "${ALPACA_SECRET_B:?ALPACA_SECRET_B not set in environment}"

API="${ALPACA_ENDPOINT:-https://paper-api.alpaca.markets/v2}"
DATA="${ALPACA_DATA_ENDPOINT:-https://data.alpaca.markets/v2}"
H_KEY="APCA-API-KEY-ID: $ALPACA_KEY_B"
H_SEC="APCA-API-SECRET-KEY: $ALPACA_SECRET_B"

cmd="${1:-}"
shift || true

case "$cmd" in
  account)
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$API/account"
    ;;
  positions)
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$API/positions"
    ;;
  position)
    sym="${1:?usage: position SYM}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$API/positions/$sym"
    ;;
  quote)
    sym="${1:?usage: quote SYM}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$DATA/stocks/$sym/quotes/latest"
    ;;
  orders)
    status="${1:-open}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$API/orders?status=$status&limit=100"
    ;;
  order)
    body="${1:?usage: order '<json>'}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" \
      -H "Content-Type: application/json" \
      -X POST -d "$body" "$API/orders"
    ;;
  cancel)
    oid="${1:?usage: cancel ORDER_ID}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" -X DELETE "$API/orders/$oid"
    ;;
  cancel-all)
    curl -fsS -H "$H_KEY" -H "$H_SEC" -X DELETE "$API/orders"
    ;;
  close)
    sym="${1:?usage: close SYM}"
    curl -fsS -H "$H_KEY" -H "$H_SEC" -X DELETE "$API/positions/$sym"
    ;;
  close-all)
    curl -fsS -H "$H_KEY" -H "$H_SEC" -X DELETE "$API/positions"
    ;;
  portfolio-history)
    curl -fsS -H "$H_KEY" -H "$H_SEC" "$API/account/portfolio/history?period=1M&timeframe=1D"
    ;;
  *)
    echo "Usage: alpaca.sh <account|positions|position|quote|orders|order|cancel|cancel-all|close|close-all|portfolio-history>" >&2
    exit 1
    ;;
esac
echo
