#!/usr/bin/env bash
#
# reset_itau_light.sh — reseta dados do demo SEM recriar Context Surface
#
# Cenário: você tá iterando no seed/prompt/LTMs durante a demo, e quer
# voltar pro estado limpo sem o custo de recriar o Context Surface (que
# leva mais tempo e gera novos IDs).
#
# O que faz:
#   1. Regenera os modelos do schema
#   2. Regenera os JSONLs de seed
#   3. Faz FLUSHDB SELETIVO (preserva memory keys e index do guardrail)
#   4. Reimporta dados via Context Surface existente
#   5. Reseeda memórias de longo prazo
#   6. Reseeda LangCache
#
# Uso:
#   bash scripts/reset_itau_light.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

DOMAIN="itau_assist"

echo ""
echo "Itaú Assist — reset light"
echo "═════════════════════════"

if ! grep -qE '^CTX_SURFACE_ID=.+' .env; then
  echo "ERRO: CTX_SURFACE_ID não está populado em .env."
  echo "Rode primeiro: bash scripts/start_itau_demo.sh"
  exit 1
fi

echo "[1/7] Regenerando modelos do schema..."
uv run python scripts/generate_models.py --domain "$DOMAIN"

echo ""
echo "[2/7] Regenerando JSONLs de seed..."
uv run python scripts/generate_data.py --domain "$DOMAIN"

echo ""
echo "[3/7] Flush seletivo do Redis (preserva memórias)..."
uv run python scripts/flush_redis.py

echo ""
echo "[4/7] Reimportando dados no Context Surface existente..."
uv run python scripts/load_data.py --domain "$DOMAIN"

echo ""
echo "[5/7] Reseedando memórias de longo prazo (LTM)..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_memories

echo ""
echo "[6/7] Reseedando LangCache..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_langcache

echo ""
echo "[7/7] Reseedando KYC customer-360 (momento de vida + índice de fatias)..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_kyc360

echo ""
echo "Reset light concluído. Backend deve auto-reload em alguns segundos"
echo "(se estiver rodando com uvicorn --reload)."
