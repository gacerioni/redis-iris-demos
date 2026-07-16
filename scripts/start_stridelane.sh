#!/usr/bin/env bash
#
# start_stridelane.sh — brings up the COMPLETE StrideLane retail demo, both surfaces,
# on DEDICATED ports and the DEDICATED Redis (via .env.stridelane). Never touches the
# serasa/banking demos (their ports 8040/3040 and their Redis are left alone).
#
#   concierge chat backend : http://localhost:8041   (IRIS gauntlet, retail tools)
#   search storefront       : http://localhost:8060   (hybrid search UX)
#   concierge chat UI       : http://localhost:3041   (React, points at 8041)
#
# Prereq (once): the StrideLane Context Surface must exist. If this is a fresh machine
# or the surface is gone, run `make setup DOMAIN=stridelane` first (with .env pointed at
# the dedicated Redis). After that, this script is all you need.
#
# Usage:  bash scripts/start_stridelane.sh        (Ctrl-C stops all three)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -f .env.stridelane ]; then
  echo "ERROR: .env.stridelane not found (dedicated Redis + domain overrides)." >&2
  exit 1
fi

# Load the dedicated overrides as REAL env vars (these win over .env in pydantic-settings),
# so StrideLane always uses the NEW Redis + the stridelane domain, immune to .env churn.
set -a
# shellcheck disable=SC1091
source .env.stridelane
set +a
export PYTHONPATH="$REPO_ROOT"

echo "StrideLane → Redis $REDIS_HOST:$REDIS_PORT  domain=$DEMO_DOMAIN"

# [1/4] data + indexes (idempotent, additive, only stridelane_* keys, never flushes)
echo "[1/4] Ensuring catalog + hybrid index in Redis..."
uv run python -m domains.stridelane.setup_index

PIDS=()
cleanup() { echo; echo "Stopping StrideLane..."; for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup SIGINT SIGTERM EXIT

# [2/4] concierge chat backend (8041)
echo "[2/4] Concierge backend on :8041 ..."
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8041 > /tmp/stridelane_concierge.log 2>&1 &
PIDS+=($!)

# [3/4] search storefront (8060)
echo "[3/4] Storefront on :8060 ..."
uv run uvicorn backend.app.storefront_app:app --host 127.0.0.1 --port 8060 > /tmp/stridelane_storefront.log 2>&1 &
PIDS+=($!)

# [4/4] chat UI (3041) pointed at the concierge backend (8041)
echo "[4/4] Chat UI on :3041 ..."
( cd frontend && VITE_API_BASE_URL=http://127.0.0.1:8041 npm run dev -- --port 3041 --host 127.0.0.1 --strictPort > /tmp/stridelane_chat.log 2>&1 ) &
PIDS+=($!)

echo "Waiting for health..."
ok=1
curl -sf --retry 40 --retry-connrefused --retry-delay 1 -m 120 http://127.0.0.1:8041/api/health >/dev/null 2>&1 && echo "  concierge 8041 OK" || { echo "  concierge 8041 FAILED (see /tmp/stridelane_concierge.log)"; ok=0; }
curl -sf --retry 30 --retry-connrefused --retry-delay 1 -m 60 http://127.0.0.1:8060/api/health >/dev/null 2>&1 && echo "  storefront 8060 OK" || { echo "  storefront 8060 FAILED"; ok=0; }
curl -sf --retry 40 --retry-connrefused --retry-delay 1 -m 90 http://127.0.0.1:3041/ >/dev/null 2>&1 && echo "  chat UI 3041 OK" || { echo "  chat UI 3041 FAILED"; ok=0; }

echo ""
if [ "$ok" = 1 ]; then
  echo "StrideLane is UP. Open:"
  echo "  Storefront (search) : http://localhost:8060"
  echo "  Concierge (chat)    : http://localhost:3041"
  echo ""
  echo "Killer beat (storefront): type 'something to keep me warm on a chilly run' (semantic #1)."
  echo "Concierge: 'Find me a cushioned road running shoe and add it to my cart' (search + cart, shared with storefront)."
  echo "(Ctrl-C stops all three. Serasa/banking demos on 8040/3040 are untouched.)"
else
  echo "One or more services failed to start. Check the /tmp/stridelane_*.log files."
fi

wait
