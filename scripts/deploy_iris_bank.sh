#!/usr/bin/env bash
#
# deploy_iris_bank.sh
#
# Orquestra deploy do demo itau_assist na VM gabs-iris-bank (GCP).
#
# Pré-requisitos no laptop:
#   - gcloud CLI autenticado (config: account+project corretos)
#   - node + npm (pra build do frontend)
#   - uv (pra generate_data)
#   - rsync
#
# Pré-requisitos na VM (uma vez só — ver deploy/README.md):
#   - /opt/iris-bank/.env preenchido
#   - Caddy do host com bloco do Caddyfile.snippet
#   - Docker + docker compose

set -euo pipefail

# ── Config ────────────────────────────────────────────────
VM_NAME="gabs-iris-bank"
VM_ZONE="us-central1-a"
VM_PROJECT="central-beach-194106"
REMOTE_BASE="/opt/iris-bank"
GCLOUD="${GCLOUD:-/Users/gabriel.cerioni/Downloads/google-cloud-sdk/bin/gcloud}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Cores pra log
B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'
say() { echo "${B}${G}»${N} $*"; }
warn() { echo "${B}${Y}⚠${N} $*"; }
die() { echo "${B}${R}✗${N} $*" >&2; exit 1; }

# ── 1. Validações ─────────────────────────────────────────
say "Validando pré-requisitos..."
command -v "$GCLOUD" >/dev/null || die "gcloud não encontrado em $GCLOUD (ajuste com GCLOUD=path bash $0)"
command -v rsync >/dev/null || die "rsync não instalado"
command -v npm >/dev/null || die "npm não instalado"
command -v uv >/dev/null || die "uv não instalado"

# Confirma que a VM existe e tá running
VM_STATUS=$("$GCLOUD" compute instances describe "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --format "value(status)" 2>/dev/null || echo "MISSING")
[ "$VM_STATUS" = "RUNNING" ] || die "VM $VM_NAME não está RUNNING (status: $VM_STATUS)"
say "VM $VM_NAME OK ($VM_STATUS)"

# ── 2. Build frontend ─────────────────────────────────────
say "Build do frontend (vite)..."
( cd frontend && npm install --silent && npm run build )
[ -f frontend/dist/index.html ] || die "frontend/dist/index.html não foi gerado"
say "Frontend build OK ($(du -sh frontend/dist | cut -f1))"

# ── 3. Gerar dados (se output/ não existir) ───────────────
if [ ! -f output/itau_assist/customers.jsonl ]; then
    say "Gerando dados sintéticos (output/itau_assist/...)..."
    uv run python scripts/generate_data.py --domain itau_assist
fi
say "Dados em output/itau_assist OK"

# ── 4. Gerar models (se generated_models.py não existir) ──
if [ ! -f domains/itau_assist/generated_models.py ]; then
    say "Gerando modelos Pydantic..."
    uv run python scripts/generate_models.py --domain itau_assist
fi

# ── 5. Enviar frontend/dist via tar pipe → VM ────────────
say "Enviando frontend/dist → $VM_NAME:$REMOTE_BASE/dist/"
DIST_TAR=$(mktemp /tmp/iris-bank-dist.XXXXXX.tar.gz)
tar -czf "$DIST_TAR" -C frontend/dist .
"$GCLOUD" compute scp --zone "$VM_ZONE" --project "$VM_PROJECT" \
    "$DIST_TAR" "$VM_NAME:/tmp/iris-bank-dist.tar.gz" --quiet
rm -f "$DIST_TAR"

"$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "
    sudo mkdir -p $REMOTE_BASE/dist
    # Limpa dist antiga e descompacta nova
    sudo find $REMOTE_BASE/dist -mindepth 1 -delete 2>/dev/null || true
    sudo tar -xzf /tmp/iris-bank-dist.tar.gz -C $REMOTE_BASE/dist
    sudo rm -f /tmp/iris-bank-dist.tar.gz
    sudo chown -R root:root $REMOTE_BASE/dist
    sudo chmod -R a+rX $REMOTE_BASE/dist
    echo \"dist: \$(sudo find $REMOTE_BASE/dist -type f | wc -l) arquivos, \$(sudo du -sh $REMOTE_BASE/dist | cut -f1)\"
" --quiet

# ── 6. rsync código (backend, domains, scripts, deploy) ──
say "Enviando código → $VM_NAME:$REMOTE_BASE/code/"
TARFILE=$(mktemp /tmp/iris-bank-code.XXXXXX.tar.gz)
tar -czf "$TARFILE" \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='frontend/dist' \
    --exclude='.env' \
    backend domains scripts deploy output pyproject.toml uv.lock Makefile

"$GCLOUD" compute scp --zone "$VM_ZONE" --project "$VM_PROJECT" \
    "$TARFILE" "$VM_NAME:/tmp/iris-bank-code.tar.gz" --quiet
rm -f "$TARFILE"

"$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "
    sudo mkdir -p $REMOTE_BASE/code
    sudo tar -xzf /tmp/iris-bank-code.tar.gz -C $REMOTE_BASE/code
    sudo rm -f /tmp/iris-bank-code.tar.gz
    sudo chown -R \$(whoami):\$(whoami) $REMOTE_BASE/code
" --quiet
say "Código enviado OK"

# ── 7. .env check ─────────────────────────────────────────
ENV_OK=$("$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "
    [ -f $REMOTE_BASE/.env ] && echo OK || echo MISSING
" --quiet 2>&1 | tail -1)

if [ "$ENV_OK" != "OK" ]; then
    warn ".env NÃO existe em $REMOTE_BASE/.env"
    warn "Antes de subir, crie-o copiando o template:"
    warn "  scp deploy/.env.example.prod $VM_NAME:/tmp/.env.prod"
    warn "  ssh $VM_NAME 'sudo mv /tmp/.env.prod $REMOTE_BASE/.env && sudo chmod 600 $REMOTE_BASE/.env'"
    warn "Preencha as credenciais (mesmas do seu .env local)."
    die "Aborting deploy — .env ausente na VM."
fi
say ".env presente em $REMOTE_BASE/.env"

# ── 8. docker compose up -d --build ───────────────────────
say "Subindo backend container..."
"$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "
    cd $REMOTE_BASE/code
    sudo docker compose -f deploy/docker-compose.prod.yml up -d --build
" 2>&1 | tail -20

# ── 9. Health check ───────────────────────────────────────
say "Esperando backend ficar saudável..."
for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 5
    HEALTH=$("$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "
        curl -sf http://127.0.0.1:8040/api/health 2>/dev/null | grep -o '\"ok\":true' || echo FAIL
    " --quiet 2>&1 | tail -1)
    if echo "$HEALTH" | grep -q '"ok":true'; then
        say "Backend saudável ✓"
        break
    fi
    [ $i -eq 10 ] && warn "Backend não respondeu em 50s — checar logs com:"
    [ $i -eq 10 ] && warn "  gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'cd $REMOTE_BASE/code && sudo docker compose -f deploy/docker-compose.prod.yml logs --tail=50'"
done

# ── 10. Resumo ────────────────────────────────────────────
echo ""
echo "${B}${G}════════════════════════════════════════════════${N}"
echo "${B}Deploy concluído.${N}"
echo "${B}════════════════════════════════════════════════${N}"
echo ""
echo "VM:            $VM_NAME ($VM_ZONE)"
echo "URL pública:   https://irisbank.platformengineer.io"
echo "Backend logs:  gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'cd $REMOTE_BASE/code && sudo docker compose -f deploy/docker-compose.prod.yml logs -f backend'"
echo "Caddy log:     gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'sudo tail -f /var/log/caddy/irisbank.log'"
echo ""
echo "Pra reseed live (sem rebuild):"
echo "  gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'cd $REMOTE_BASE/code && sudo docker compose -f deploy/docker-compose.prod.yml exec backend bash scripts/reset_itau_light.sh'"
