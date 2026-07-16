#!/usr/bin/env bash
#
# start_token_gateway.sh — sobe o Token Control Plane (Redis como rate limiter de LLM).
#   [1/3] preflight de infra   [2/3] sobe o gateway (uvicorn :8050)   [3/3] health check
#
# Serviço standalone na porta 8050: NÃO encosta no chat (8040) nem em domínio nenhum.
# Não tem etapa de seed (áreas/baldes são config-driven em backend/app/gateway/config.py;
# as keys tcp:* nascem sob demanda e o reset zera só elas via POST /api/gateway/reset).
#
# Uso:
#   bash scripts/start_token_gateway.sh                 # preflight + sobe
#   bash scripts/start_token_gateway.sh --skip-preflight
#
# UI: http://localhost:8050/   ·   Health: http://localhost:8050/api/health
# Parar: Ctrl-C (ou matar o uvicorn da :8050).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PORT=8050
HOST=127.0.0.1
SKIP_PREFLIGHT=false
for arg in "$@"; do
  case "$arg" in
    --skip-preflight) SKIP_PREFLIGHT=true ;;
    *) echo "Argumento desconhecido: $arg"; exit 2 ;;
  esac
done

echo "━━━ Token Control Plane ━━━"

# [1/3] Preflight de infra (Redis alcançável, .env presente). Reusa o checker dos demos.
if [ "$SKIP_PREFLIGHT" = false ]; then
  echo "[1/3] Preflight de infra…"
  uv run python scripts/preflight.py
else
  echo "[1/3] Preflight pulado (--skip-preflight)."
fi

# [2/3] Sobe o gateway em background, espera o /api/health responder.
echo "[2/3] Subindo gateway em http://$HOST:$PORT …"
uv run uvicorn backend.app.gateway.app:app --host "$HOST" --port "$PORT" &
GATEWAY_PID=$!
trap 'kill "$GATEWAY_PID" 2>/dev/null || true' EXIT

# [3/3] Health check (retry sem sleep, tolera connection-refused durante o boot).
echo "[3/3] Aguardando health…"
if curl -sf --retry 30 --retry-connrefused --retry-delay 1 -m 90 \
     "http://$HOST:$PORT/api/health" >/tmp/tcp_health.json 2>/dev/null; then
  echo "    OK: $(cat /tmp/tcp_health.json)"
  echo ""
  echo "Pronto. Abra:  http://localhost:$PORT/"
  echo "Áreas/baldes:  GET  http://localhost:$PORT/api/gateway/config"
  echo "Estado live:   GET  http://localhost:$PORT/api/gateway/state"
  echo "Resetar keys:  POST http://localhost:$PORT/api/gateway/reset"
  echo ""
  echo "(Ctrl-C encerra o gateway.)"
else
  echo "    FALHOU: gateway não respondeu em /api/health." >&2
  exit 1
fi

# Mantém o gateway em foreground até Ctrl-C.
wait "$GATEWAY_PID"
