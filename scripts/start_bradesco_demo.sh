#!/usr/bin/env bash
#
# start_bradesco_demo.sh — boot one-shot do demo Bradesco BIA, do zero ao validado:
#   [1/5] Preflight de infra  [2/5] config .env  [3/5] setup do zero + validação
#   [4/5] backend + frontend  [5/5] health check + resumo
#
# Uso:
#   bash scripts/start_bradesco_demo.sh                # do zero
#   bash scripts/start_bradesco_demo.sh --skip-setup   # só sobe (já setado)
#
# Reset light: bash scripts/reset_bradesco_light.sh

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

start_demo_core "bradesco_bia" "bradesco-bia-demo" "Bradesco BIA" "$SKIP_SETUP"
