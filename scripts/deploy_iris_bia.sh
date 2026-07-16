#!/usr/bin/env bash
#
# deploy_iris_bia.sh
#
# Orquestra deploy da demo bradesco_bia (BIA) num bastion Ubuntu na AWS (sa-east-1),
# servida em https://irisbia.platformengineer.io.
#
# Diferença pro deploy_iris_bank.sh: aquele usa gcloud (VM GCP); este usa ssh/scp
# puro contra uma EC2. Não toca no deploy do Itaú nem no ambiente local.
#
# Uso:
#   EC2_HOST=ubuntu@SEU-IP-OU-DNS  SSH_KEY=~/.ssh/sua-chave.pem  bash scripts/deploy_iris_bia.sh
#
# Pré-requisitos no laptop: ssh, scp, node+npm, uv, tar.
# Pré-requisitos no bastion (uma vez só — ver deploy/irisbia/README.md):
#   - Docker + docker compose (já tem)
#   - nginx + certbot com o vhost de deploy/irisbia/nginx-irisbia.conf (TLS + basic_auth).
#     A caixa usa NGINX (não Caddy); o vhost keynoteaws já existe, irisbia entra ao lado.
#   - /opt/iris-bia/.env preenchido (chmod 600) — ver deploy/irisbia/.env.example.prod
#   - STEP 0 (make setup, cunha a surface) já rodado NO BASTION (Redis é privado)
#   - DNS irisbia.platformengineer.io -> 56.124.109.24

set -euo pipefail

# ── Config (sobrescreva via env) ──────────────────────────
EC2_HOST="${EC2_HOST:-}"                       # ex: ubuntu@ec2-x-x-x-x.sa-east-1.compute.amazonaws.com
SSH_KEY="${SSH_KEY:-}"                          # ex: ~/.ssh/irisbia.pem (vazio = usa ssh config/agent)
REMOTE_BASE="${REMOTE_BASE:-/opt/iris-bia}"
DOMAIN="bradesco_bia"
COMPOSE_FILE="deploy/irisbia/docker-compose.prod.yml"
RESET_SCRIPT="reset_bradesco_light.sh"
PUBLIC_URL="https://irisbia.platformengineer.io"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'
say() { echo "${B}${G}»${N} $*"; }
warn() { echo "${B}${Y}⚠${N} $*"; }
die() { echo "${B}${R}✗${N} $*" >&2; exit 1; }

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
[ -n "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")
rsh() { ssh "${SSH_OPTS[@]}" "$EC2_HOST" "$@"; }
rcp() { scp "${SSH_OPTS[@]}" "$@"; }

# ── 1. Validações ─────────────────────────────────────────
say "Validando pré-requisitos..."
[ -n "$EC2_HOST" ] || die "Defina EC2_HOST (ex: EC2_HOST=ubuntu@1.2.3.4 bash $0)"
for c in ssh scp npm uv tar; do command -v "$c" >/dev/null || die "$c não instalado"; done
rsh "echo ok" >/dev/null 2>&1 || die "Não consegui SSH em $EC2_HOST (cheque SSH_KEY / security group / IP)"
say "SSH em $EC2_HOST OK"

# ── 2. Build frontend (domain-agnostic; o backend escolhe o domínio) ──
say "Build do frontend (vite)..."
( cd frontend && npm install --silent && npm run build )
[ -f frontend/dist/index.html ] || die "frontend/dist/index.html não gerado"
[ -d "frontend/dist/backgrounds/$DOMAIN" ] || warn "frontend/dist/backgrounds/$DOMAIN ausente (bg do domínio pode não carregar)"
say "Frontend build OK ($(du -sh frontend/dist | cut -f1))"

# ── 3. Gerar dados + models do bradesco (se faltarem) ─────
[ -f "output/$DOMAIN/customers.jsonl" ] || { say "Gerando dados ($DOMAIN)..."; uv run python scripts/generate_data.py --domain "$DOMAIN"; }
[ -f "domains/$DOMAIN/generated_models.py" ] || { say "Gerando models..."; uv run python scripts/generate_models.py --domain "$DOMAIN"; }

# ── 4. Enviar frontend/dist → bastion ─────────────────────
say "Enviando frontend/dist → $REMOTE_BASE/dist/"
DIST_TAR=$(mktemp /tmp/iris-bia-dist.XXXXXX.tar.gz)
tar -czf "$DIST_TAR" -C frontend/dist .
rcp "$DIST_TAR" "$EC2_HOST:/tmp/iris-bia-dist.tar.gz"
rm -f "$DIST_TAR"
rsh "sudo mkdir -p $REMOTE_BASE/dist && sudo find $REMOTE_BASE/dist -mindepth 1 -delete 2>/dev/null || true; \
     sudo tar -xzf /tmp/iris-bia-dist.tar.gz -C $REMOTE_BASE/dist && sudo rm -f /tmp/iris-bia-dist.tar.gz && \
     sudo chmod -R a+rX $REMOTE_BASE/dist && echo \"dist: \$(sudo find $REMOTE_BASE/dist -type f | wc -l) arquivos\""

# ── 5. Enviar código → bastion ────────────────────────────
say "Enviando código → $REMOTE_BASE/code/"
CODE_TAR=$(mktemp /tmp/iris-bia-code.XXXXXX.tar.gz)
tar -czf "$CODE_TAR" \
    --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.git' --exclude='frontend/dist' --exclude='.env' \
    backend domains scripts deploy output pyproject.toml uv.lock Makefile
rcp "$CODE_TAR" "$EC2_HOST:/tmp/iris-bia-code.tar.gz"
rm -f "$CODE_TAR"
rsh "sudo mkdir -p $REMOTE_BASE/code && sudo tar -xzf /tmp/iris-bia-code.tar.gz -C $REMOTE_BASE/code && \
     sudo rm -f /tmp/iris-bia-code.tar.gz && sudo chown -R \$(whoami):\$(whoami) $REMOTE_BASE/code"
say "Código enviado OK"

# ── 6. .env check ─────────────────────────────────────────
if [ "$(rsh "[ -f $REMOTE_BASE/.env ] && echo OK || echo MISSING")" != "OK" ]; then
    warn ".env ausente em $REMOTE_BASE/.env. Crie a partir do template:"
    warn "  scp ${SSH_KEY:+-i $SSH_KEY} deploy/irisbia/.env.example.prod $EC2_HOST:/tmp/.env"
    warn "  ssh $EC2_HOST 'sudo mv /tmp/.env $REMOTE_BASE/.env && sudo chmod 600 $REMOTE_BASE/.env'"
    warn "  (preencha REDIS_* do Pro novo + as 3 chaves SaaS + OPENAI_API_KEY; surface_id/agent_key EM BRANCO)"
    die "Aborting — preencha o .env e rode o STEP 0 (make setup) antes. Ver deploy/irisbia/README.md"
fi
say ".env presente"

# ── 7. docker compose up -d --build ───────────────────────
say "Subindo container iris-bia-backend..."
rsh "cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE up -d --build" 2>&1 | tail -20

# ── 8. Health check ───────────────────────────────────────
say "Esperando backend ficar saudável..."
OK=0
for i in $(seq 1 12); do
    H=$(rsh "curl -sf http://127.0.0.1:8040/api/health 2>/dev/null || true")
    if echo "$H" | grep -q '"ok":true'; then
        DOM=$(echo "$H" | grep -o '"domain":"[^"]*"' || true)
        say "Backend saudável ✓ ($DOM)"; OK=1; break
    fi
    sleep 5
done
[ "$OK" = 1 ] || warn "Backend não respondeu. Logs: ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE logs --tail=60'"

# ── 9. Resumo ─────────────────────────────────────────────
echo ""
echo "${B}${G}════════════════════════════════════════${N}"
echo "${B}Deploy concluído.${N}"
echo "${B}════════════════════════════════════════${N}"
echo "Bastion:   $EC2_HOST"
echo "URL:       $PUBLIC_URL  (gated por basic_auth no Caddy)"
echo "Logs:      ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE logs -f backend'"
echo "Reset:     ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE exec backend bash scripts/$RESET_SCRIPT'"
echo ""
echo "IMPORTANTE: na PRIMEIRA subida (Redis novo), o STEP 0 (cunhar a surface + carregar"
echo "dados no Redis novo) roda NO LAPTOP, ANTES deste deploy, contra o .env da irisbia."
echo "O container só SERVE; ele não roda make setup (o sed no .env seria efêmero). Ver"
echo "deploy/irisbia/README.md (STEP 0). Depois é só copiar esse .env já preenchido (com"
echo "CTX_SURFACE_ID + MCP_AGENT_KEY frescos) pra $REMOTE_BASE/.env e rodar este script."
