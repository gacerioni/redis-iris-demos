#!/usr/bin/env bash
#
# reset_leet_bank_light.sh — reseta dados do demo leet_bank SEM recriar Context Surface
#
# O que faz:
#   1. Regenera os modelos do schema
#   2. Regenera os JSONLs de seed
#   3. Faz FLUSHDB SELETIVO (preserva memory keys e index do guardrail)
#   4. Reimporta dados via Context Surface existente
#   5. Reseeda memórias de longo prazo
#   6. Reseeda LangCache
#   7. Reseeda KYC perfil 360 (documento + índice de fatias)
#
# Uso:
#   bash scripts/reset_leet_bank_light.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

DOMAIN="leet_bank"

echo ""
echo "leet_bank — reset light"
echo "═════════════════════"

if ! grep -qE '^CTX_SURFACE_ID=.+' .env; then
  echo "ERRO: CTX_SURFACE_ID não está populado em .env."
  echo "Rode primeiro: bash scripts/start_leet_bank_demo.sh"
  exit 1
fi

if ! grep -qE "^DEMO_DOMAIN=${DOMAIN}$" .env; then
  echo "ERRO: DEMO_DOMAIN ativo não é ${DOMAIN}. Rode start_leet_bank_demo.sh primeiro."
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
echo "[7/7] Reseedando KYC perfil 360..."
DEMO_DOMAIN="$DOMAIN" uv run python -m scripts.seed_kyc360_leet

echo ""
echo "Reset light concluído. Backend deve auto-reload em alguns segundos"
echo "(se estiver rodando com uvicorn --reload)."
