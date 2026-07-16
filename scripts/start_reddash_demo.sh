#!/usr/bin/env bash
#
# start_reddash_demo.sh — boot one-shot do demo Reddash (Delivery Support, EN):
#   [1/5] Preflight  [2/5] config .env (DEMO_DOMAIN + MEMORY_NAMESPACE)
#   [3/5] setup do zero + validação  [4/5] backend + frontend  [5/5] health
#
# Uso:
#   bash scripts/start_reddash_demo.sh                # do zero
#   bash scripts/start_reddash_demo.sh --skip-setup   # só sobe (já setado)

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

start_demo_core "reddash" "reddash-demo" "Reddash" "$SKIP_SETUP"
