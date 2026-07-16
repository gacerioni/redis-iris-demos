#!/usr/bin/env bash
#
# reset_serasa_experian_light.sh — reseta dados do demo Serasa Experian SEM
# recriar Context Surface. Útil pra iterar no seed/prompt/LTMs durante o demo,
# sem pagar o custo de recriar o Surface.
#
# O que faz:
#   1. Regenera modelos do schema
#   2. Regenera JSONLs de seed
#   3. Flush seletivo do Redis (preserva memórias e índices do guardrail)
#   4. Reimporta dados no Context Surface existente
#   5. Reseed memórias de longo prazo
#   6. Reseed LangCache
#
# Uso:
#   bash scripts/reset_serasa_experian_light.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

DOMAIN="serasa_experian"

echo ""
echo "Serasa Experian — reset light"
echo "═════════════════════════════"

if ! grep -qE '^CTX_SURFACE_ID=.+' .env; then
  echo "ERRO: CTX_SURFACE_ID não populado em .env."
  echo "Rode primeiro: bash scripts/start_serasa_experian_demo.sh"
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
echo "Reset light concluído. Backend deve auto-reload em alguns segundos"
echo "(se estiver rodando com uvicorn --reload)."
