#!/usr/bin/env bash
#
# reset_picpay_light.sh — reseta dados do demo PicPay Assist SEM recriar
# Context Surface. Útil pra iterar no seed/prompt/LTMs sem pagar o custo de
# recriar o Surface.
#
# Uso:
#   bash scripts/reset_picpay_light.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

DOMAIN="picpay_assist"

echo ""
echo "PicPay Assist — reset light"
echo "═══════════════════════════"

if ! grep -qE '^CTX_SURFACE_ID=.+' .env; then
  echo "ERRO: CTX_SURFACE_ID não populado em .env."
  echo "Rode primeiro: bash scripts/start_picpay_demo.sh"
  exit 1
fi

echo "[1/6] Regenerando modelos do schema..."
uv run python scripts/generate_models.py --domain "$DOMAIN"

echo ""
echo "[2/6] Regenerando JSONLs de seed..."
uv run python scripts/generate_data.py --domain "$DOMAIN"

echo ""
echo "[3/6] Flush seletivo do Redis (preserva memórias)..."
uv run python scripts/flush_redis.py

echo ""
echo "[4/6] Reimportando dados no Context Surface existente..."
uv run python scripts/load_data.py --domain "$DOMAIN"

echo ""
echo "[5/6] Reseedando memórias de longo prazo (LTM)..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_memories

echo ""
echo "[6/6] Reseedando LangCache..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_langcache

echo ""
echo "Reset light concluído. Backend auto-reload em alguns segundos."
