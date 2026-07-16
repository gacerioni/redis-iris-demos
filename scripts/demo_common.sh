#!/usr/bin/env bash
#
# demo_common.sh — funções compartilhadas pelos start scripts dos domínios BR.
# Source apenas (não executar): source "$(dirname "$0")/demo_common.sh"

# set_env_var KEY VALUE — atualiza ou anexa no .env (sed macOS)
set_env_var() {
  local key="$1" value="$2"
  if grep -qE "^${key}=" .env; then
    sed -i '' "s|^${key}=.*|${key}=${value}|" .env
  else
    echo "${key}=${value}" >> .env
  fi
}

# get_env_var KEY — imprime o valor (vazio se ausente)
get_env_var() {
  grep -E "^$1=" .env | head -1 | cut -d= -f2- || true
}

# stash_surface_id — antes de trocar de domínio, salva o CTX_SURFACE_ID atual
# em CTX_SURFACE_ID_<SLUG> (ex: serasa_limpa_nome → CTX_SURFACE_ID_SERASA_LIMPA_NOME)
# pra permitir voltar sem recriar Surface (via reset light).
stash_surface_id() {
  local cur_domain cur_surface slug
  cur_domain=$(get_env_var DEMO_DOMAIN)
  cur_surface=$(get_env_var CTX_SURFACE_ID)
  if [ -n "$cur_domain" ] && [ -n "$cur_surface" ]; then
    slug=$(echo "$cur_domain" | tr '[:lower:]' '[:upper:]')
    set_env_var "CTX_SURFACE_ID_${slug}" "$cur_surface"
    echo "  Surface do domínio ${cur_domain} salvo em CTX_SURFACE_ID_${slug}"
  fi
}

# wait_healthy URL DOMAIN_ID TIMEOUT_S — espera /api/health responder com o
# domínio esperado. Retorna 0 quando saudável, 1 em timeout.
wait_healthy() {
  local url="$1" expected="$2" timeout="${3:-90}" elapsed=0
  echo -n "  Aguardando backend ficar saudável"
  while [ "$elapsed" -lt "$timeout" ]; do
    local got
    got=$(curl -s --max-time 2 "$url/api/health" 2>/dev/null \
      | python3 -c "import sys,json;print(json.load(sys.stdin).get('domain',''))" 2>/dev/null || true)
    if [ "$got" = "$expected" ]; then
      echo " → OK (domain=$got, ${elapsed}s)"
      return 0
    fi
    echo -n "."
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo " → TIMEOUT após ${timeout}s"
  return 1
}

# post_boot_report URL — resumo da demo no ar: app, tools, starters
post_boot_report() {
  local url="$1"
  curl -s --max-time 5 "$url/api/domain-config" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  App:      {d.get(\"app_name\")} — {d.get(\"subtitle\")}')
print(f'  Starters: {len(d.get(\"starter_prompts\", []))}')
" 2>/dev/null || echo "  (domain-config indisponível)"
  curl -s --max-time 5 "$url/api/health" | python3 -c "
import sys, json
d = json.load(sys.stdin)
tools = d.get('internal_tools') or d.get('tools') or []
if tools:
    print(f'  Tools:    {\", \".join(tools)}')
flags = [k for k in ('mcp_enabled','memory_enabled','langcache_enabled','guardrail_enabled') if d.get(k)]
print(f'  Serviços: {\", \".join(flags)}')
" 2>/dev/null || true
}

# start_demo_core DOMAIN_ID NAMESPACE LABEL SKIP_SETUP — fases completas de boot:
#   [1/5] preflight de infra  [2/5] config .env  [3/5] setup do zero + validação
#   [4/5] backend + frontend  [5/5] health check + resumo
start_demo_core() {
  local domain_id="$1" namespace="$2" label="$3" skip_setup="$4"
  local base_url="http://127.0.0.1:8040"

  echo ""
  echo "$label — bootstrap"
  echo "═══════════════════════════════════"

  if [ ! -f .env ]; then
    echo "ERRO: .env não encontrado. Copia .env.example e preenche as credenciais."
    exit 1
  fi

  echo ""
  echo "[1/5] Preflight de infra..."
  uv run python scripts/preflight.py

  echo ""
  echo "[2/5] Configurando .env..."
  local cur_domain
  cur_domain=$(get_env_var DEMO_DOMAIN)
  if [ "$cur_domain" != "$domain_id" ]; then
    stash_surface_id
    echo "  Trocando DEMO_DOMAIN: ${cur_domain:-"(vazio)"} → $domain_id"
    set_env_var DEMO_DOMAIN "$domain_id"
  else
    echo "  DEMO_DOMAIN já em $domain_id"
  fi
  set_env_var MEMORY_NAMESPACE "$namespace"
  echo "  MEMORY_NAMESPACE=$namespace"

  if [ "$skip_setup" = false ]; then
    echo ""
    echo "[3/5] Setup do zero (modelos, Surface, dados, memórias, LangCache)..."
    make setup DOMAIN="$domain_id"
    stash_surface_id   # registra o Surface novo deste domínio
  else
    echo ""
    echo "[3/5] Setup pulado (--skip-setup)"
  fi
  echo "  Validação anti-drift do domínio..."
  make validate DOMAIN="$domain_id"

  echo ""
  echo "[4/5] Subindo backend (8040) + frontend (3040)..."
  trap 'kill 0' SIGINT SIGTERM
  make dev &
  local dev_pid=$!

  echo ""
  echo "[5/5] Health check..."
  if ! wait_healthy "$base_url" "$domain_id" 90; then
    echo "ERRO: backend não ficou saudável. Logs acima."
    kill "$dev_pid" 2>/dev/null || true
    exit 1
  fi
  post_boot_report "$base_url"

  echo ""
  echo "  Demo pronta → http://localhost:3040"
  echo "  (Ctrl+C derruba backend + frontend)"
  echo ""
  wait "$dev_pid"
}
