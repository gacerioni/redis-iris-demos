#!/usr/bin/env bash
#
# start_banco_inter_demo.sh — boot one-shot do demo Banco Inter (Babi), do zero ao validado:
#   [1/5] Preflight de infra (Redis, OpenAI, Memory API, LangCache, Context Engine)
#   [2/5] Configuração do .env (DEMO_DOMAIN, MEMORY_NAMESPACE, stash de Surface)
#   [3/5] Setup completo (modelos, Context Surface, dados, LTMs, LangCache) + validação
#   [4/5] Backend (8040) + frontend (3040)
#   [5/5] Health check + resumo da demo no ar
#
# Flush escopado: o setup só apaga chaves banco_inter_* / banco_inter:* no Redis
# compartilhado, então NÃO derruba as outras demos (itau, serasa, etc.).
#
# Uso:
#   bash scripts/start_banco_inter_demo.sh                # do zero, com tudo
#   bash scripts/start_banco_inter_demo.sh --skip-setup   # só sobe (ambiente já setado)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
source scripts/demo_common.sh

SKIP_SETUP=false
for arg in "$@"; do
  case "$arg" in
    --skip-setup) SKIP_SETUP=true ;;
    *) echo "Argumento desconhecido: $arg"; exit 2 ;;
  esac
done

start_demo_core "banco_inter" "banco-inter-demo" "Banco Inter" "$SKIP_SETUP"
