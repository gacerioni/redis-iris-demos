#!/usr/bin/env bash
#
# deploy_iris_serasa.sh
#
# Orquestra deploy da demo serasa_experian num bastion Ubuntu na AWS (sa-east-1),
# servida em https://serasa.platformengineer.io.
#
# Mesmo bastion e estrutura do deploy_iris_bia.sh (irisbia.platformengineer.io),
# mas usa porta 8041 e container iris-serasa-backend para nao colidir com o irisbia.
#
# Uso:
#   EC2_HOST=ubuntu@56.124.109.24 SSH_KEY=~/Downloads/gabs-itau-sa-east-1.pem bash scripts/deploy_iris_serasa.sh
#
# Pre-requisitos no bastion (uma vez so — ver deploy/serasa_experian/README.md):
#   - /opt/iris-serasa/.env preenchido (chmod 600) — ver deploy/serasa_experian/.env.example.prod
#   - STEP 0 (make setup DOMAIN=serasa_experian) ja rodado no bastion (cunha a surface)
#   - nginx vhost serasa.platformengineer.io instalado + certbot cert obtido
#   - DNS serasa.platformengineer.io -> 56.124.109.24

set -euo pipefail

EC2_HOST="${EC2_HOST:-}"
SSH_KEY="${SSH_KEY:-}"
REMOTE_BASE="${REMOTE_BASE:-/opt/iris-serasa}"
DOMAIN="serasa_experian"
COMPOSE_FILE="deploy/serasa_experian/docker-compose.prod.yml"
RESET_SCRIPT="reset_serasa_experian_light.sh"
PUBLIC_URL="https://serasa.platformengineer.io"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'
say() { echo "${B}${G}>>>${N} $*"; }
warn() { echo "${B}${Y}!${N} $*"; }
die() { echo "${B}${R}X${N} $*" >&2; exit 1; }

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
[ -n "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")
rsh() { ssh "${SSH_OPTS[@]}" "$EC2_HOST" "$@"; }
rcp() { scp "${SSH_OPTS[@]}" "$@"; }

say "Validando pre-requisitos..."
[ -n "$EC2_HOST" ] || die "Defina EC2_HOST (ex: EC2_HOST=ubuntu@56.124.109.24 bash $0)"
for c in ssh scp npm uv tar; do command -v "$c" >/dev/null || die "$c nao instalado localmente"; done
rsh "echo ok" >/dev/null 2>&1 || die "Nao consegui SSH em $EC2_HOST (cheque SSH_KEY / security group)"
say "SSH em $EC2_HOST OK"

say "Build do frontend (vite)..."
( cd frontend && npm install --silent && npm run build )
[ -f frontend/dist/index.html ] || die "frontend/dist/index.html nao gerado"
[ -d "frontend/dist/backgrounds/$DOMAIN" ] || warn "frontend/dist/backgrounds/$DOMAIN ausente"
say "Frontend build OK ($(du -sh frontend/dist | cut -f1))"

[ -f "output/$DOMAIN/customers.jsonl" ] || { say "Gerando dados ($DOMAIN)..."; uv run python scripts/generate_data.py --domain "$DOMAIN"; }
[ -f "domains/$DOMAIN/generated_models.py" ] || { say "Gerando models..."; uv run python scripts/generate_models.py --domain "$DOMAIN"; }

say "Enviando frontend/dist -> $REMOTE_BASE/dist/"
DIST_TAR=$(mktemp "$TMPDIR/iris-serasa-dist.XXXXXX.tar.gz")
tar -czf "$DIST_TAR" -C frontend/dist .
rcp "$DIST_TAR" "$EC2_HOST:/tmp/iris-serasa-dist.tar.gz"
rm -f "$DIST_TAR"
rsh "sudo mkdir -p $REMOTE_BASE/dist && sudo find $REMOTE_BASE/dist -mindepth 1 -delete 2>/dev/null || true; \
     sudo tar -xzf /tmp/iris-serasa-dist.tar.gz -C $REMOTE_BASE/dist && sudo rm -f /tmp/iris-serasa-dist.tar.gz && \
     sudo chmod -R a+rX $REMOTE_BASE/dist && echo \"dist: \$(sudo find $REMOTE_BASE/dist -type f | wc -l) arquivos\""

say "Enviando codigo -> $REMOTE_BASE/code/"
CODE_TAR=$(mktemp "$TMPDIR/iris-serasa-code.XXXXXX.tar.gz")
tar -czf "$CODE_TAR" \
    --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.git' --exclude='frontend/dist' --exclude='.env' \
    backend domains scripts deploy output pyproject.toml uv.lock Makefile
rcp "$CODE_TAR" "$EC2_HOST:/tmp/iris-serasa-code.tar.gz"
rm -f "$CODE_TAR"
rsh "sudo mkdir -p $REMOTE_BASE/code && sudo tar -xzf /tmp/iris-serasa-code.tar.gz -C $REMOTE_BASE/code && \
     sudo rm -f /tmp/iris-serasa-code.tar.gz && sudo chown -R \$(whoami):\$(whoami) $REMOTE_BASE/code"
say "Codigo enviado OK"

if [ "$(rsh "[ -f $REMOTE_BASE/.env ] && echo OK || echo MISSING")" != "OK" ]; then
    warn ".env ausente em $REMOTE_BASE/.env."
    die "Crie /opt/iris-serasa/.env (ver deploy/serasa_experian/.env.example.prod) e rode STEP 0 antes."
fi
say ".env presente"

say "Subindo container iris-serasa-backend..."
rsh "cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE up -d --build" 2>&1 | tail -20

say "Esperando backend ficar saudavel..."
OK=0
for i in $(seq 1 12); do
    H=$(rsh "curl -sf http://127.0.0.1:8041/api/health 2>/dev/null || true")
    if echo "$H" | grep -q '"ok":true'; then
        DOM=$(echo "$H" | grep -o '"domain":"[^"]*"' || true)
        say "Backend saudavel ($DOM)"; OK=1; break
    fi
    sleep 5
done
[ "$OK" = 1 ] || warn "Backend nao respondeu. Logs: ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE logs --tail=60'"

echo ""
echo "${B}${G}==========================================${N}"
echo "${B}Deploy concluido.${N}"
echo "${B}==========================================${N}"
echo "Bastion:   $EC2_HOST"
echo "URL:       $PUBLIC_URL"
echo "Logs:      ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE logs -f backend'"
echo "Reset:     ssh $EC2_HOST 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE_FILE exec backend bash scripts/$RESET_SCRIPT'"
