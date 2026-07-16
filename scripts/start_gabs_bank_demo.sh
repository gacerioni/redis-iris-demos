#!/usr/bin/env bash
#
# start_gabs_bank_demo.sh — one-shot boot of the Gabs Bank (Ava) demo, from zero to verified:
#   [1/5] Infra preflight (Redis, OpenAI, Memory API, LangCache, Context Engine)
#   [2/5] .env setup (DEMO_DOMAIN, MEMORY_NAMESPACE, Surface stash)
#   [3/5] Full setup (models, Context Surface, data, LTMs, LangCache) + validation
#   [4/5] Backend (8040) + frontend (3040)
#   [5/5] Health check + demo summary
#
# Scoped flush: setup only deletes gabs_bank_* / gabs_bank:* keys in the shared
# Redis, so it does NOT take down the other demos (itau, banco_inter, serasa, ...).
#
# Usage:
#   bash scripts/start_gabs_bank_demo.sh                # from zero, everything
#   bash scripts/start_gabs_bank_demo.sh --skip-setup   # just boot (env already set)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
source scripts/demo_common.sh

SKIP_SETUP=false
for arg in "$@"; do
  case "$arg" in
    --skip-setup) SKIP_SETUP=true ;;
    *) echo "Unknown argument: $arg"; exit 2 ;;
  esac
done

start_demo_core "gabs_bank" "gabs-bank-demo" "Gabs Bank" "$SKIP_SETUP"
