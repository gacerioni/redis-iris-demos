#!/usr/bin/env bash
#
# start_stridelane_storefront.sh — StrideLane retail hybrid-search storefront (port 8060).
#   [1/3] data (generate if missing or --regen)   [2/3] load into Redis + indexes + synonyms + autocomplete
#   [3/3] serve the storefront UI on :8060
#
# Standalone and additive: writes only stridelane_* keys + stridelane_* indexes, never flushes
# the DB, never touches the chat backend (8040) or any other demo. Coexists with everything.
#
# Usage:
#   bash scripts/start_stridelane_storefront.sh            # load (if needed) + serve
#   bash scripts/start_stridelane_storefront.sh --regen    # regenerate the catalog (fresh data) then serve
#
# UI: http://localhost:8060/   ·   Health: http://localhost:8060/api/health

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT"

PORT=8060
HOST=127.0.0.1
REGEN=false
for arg in "$@"; do
  case "$arg" in
    --regen) REGEN=true ;;
    *) echo "Unknown argument: $arg"; exit 2 ;;
  esac
done

echo "━━━ StrideLane storefront ━━━"

# [1/3] data
if [ "$REGEN" = true ] || [ ! -f "output/stridelane/products.jsonl" ]; then
  echo "[1/3] Generating catalog (220 SKUs + variants + stores + policies + features)..."
  uv run python -m domains.stridelane.data_generator
else
  echo "[1/3] Catalog JSONL present (use --regen to rebuild)."
fi

# [2/3] load into Redis + create backend indexes + synonyms + autocomplete (idempotent, additive)
echo "[2/3] Loading into Redis + building indexes (additive, namespaced stridelane_*)..."
uv run python -m domains.stridelane.setup_index

# [3/3] serve
echo "[3/3] Serving storefront on http://$HOST:$PORT ..."
uv run uvicorn backend.app.storefront_app:app --host "$HOST" --port "$PORT" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

if curl -sf --retry 30 --retry-connrefused --retry-delay 1 -m 90 "http://$HOST:$PORT/api/health" >/dev/null 2>&1; then
  echo ""
  echo "Ready. Open:  http://localhost:$PORT/"
  echo "Try the killer beat:  type  'something to keep me warm on a chilly run'  (no keyword match, semantic #1)"
  echo "Then drag the Vector slider up and the Text slider down, watch results re-rank live."
  echo "(Ctrl-C stops the storefront. The chat backend and other demos are untouched.)"
else
  echo "FAILED: storefront did not answer on /api/health." >&2
  exit 1
fi

wait "$SERVER_PID"
