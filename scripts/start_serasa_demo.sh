#!/usr/bin/env bash
#
# start_serasa_demo.sh — boot one-shot do demo Limpa Nome IA, do zero ao validado:
#   [1/5] Preflight de infra (Redis, OpenAI, Memory API, LangCache, Context Engine)
#   [2/5] Configuração do .env (DEMO_DOMAIN, MEMORY_NAMESPACE, stash de Surface)
#   [3/5] Setup completo (modelos, Context Surface, dados, LTMs, LangCache) + validação
#   [4/5] Backend (8040) + frontend (3040)
#   [5/5] Health check + resumo da demo no ar
#
# Uso:
#   bash scripts/start_serasa_demo.sh                # do zero, com tudo
#   bash scripts/start_serasa_demo.sh --skip-setup   # só sobe (ambiente já setado)
#
# Reset light (re-seed sem recriar Context Surface):
#   bash scripts/reset_serasa_light.sh

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

start_demo_core "serasa_limpa_nome" "serasa-limpa-nome-demo" "Limpa Nome IA (Serasa)" "$SKIP_SETUP"
