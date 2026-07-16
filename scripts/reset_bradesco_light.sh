#!/usr/bin/env bash
#
# reset_bradesco_light.sh — reseta dados do demo Bradesco BIA SEM recriar o
# Context Surface. Útil pra iterar no seed/prompt/LTMs.
#
# Uso: bash scripts/reset_bradesco_light.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
DOMAIN="bradesco_bia"

echo ""
echo "Bradesco BIA — reset light"
echo "══════════════════════════"

if ! grep -qE '^CTX_SURFACE_ID=.+' .env; then
  echo "ERRO: CTX_SURFACE_ID não populado. Rode: bash scripts/start_bradesco_demo.sh"
  exit 1
fi

echo "[1/6] Regenerando modelos..."
uv run python scripts/generate_models.py --domain "$DOMAIN"
echo "[2/6] Regenerando JSONLs..."
uv run python scripts/generate_data.py --domain "$DOMAIN"
echo "[3/6] Flush seletivo do Redis (preserva memórias)..."
uv run python scripts/flush_redis.py
echo "[4/6] Reimportando dados no Surface existente..."
uv run python scripts/load_data.py --domain "$DOMAIN"
echo "[5/6] Reseedando memórias (LTM)..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_memories
echo "[6/6] Reseedando LangCache..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_langcache
echo ""
echo "Reset light concluído."
