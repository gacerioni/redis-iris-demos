#!/usr/bin/env bash
#
# deploy_gabs_bank.sh
#
# Deploys the Gabs Bank (Ava) public English demo to the gabs-iris-bank VM (GCP),
# in an ISOLATED slot (/opt/gabs-bank, host port 8042, container gabs-bank-backend,
# vhost gabsbank.platformengineer.io). Does NOT touch the iris-bank slot or any
# other demo on the shared Caddy.
#
# Laptop prerequisites: gcloud (authed), npm, rsync. Data/models are pre-generated
# locally (output/gabs_bank + generated_models.py) so uv is not required here; the
# backend image builds its own deps in Docker.
#
# VM prerequisites (handled by this script): Docker + host Caddy already installed.

set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# ── Config ────────────────────────────────────────────────
VM_NAME="gabs-iris-bank"
VM_ZONE="us-central1-a"
VM_PROJECT="central-beach-194106"
REMOTE_BASE="/opt/gabs-bank"
DOMAIN="gabs_bank"
HOST_PORT="8042"
SUBDOMAIN="gabsbank.platformengineer.io"
COMPOSE="deploy/gabs_bank/docker-compose.prod.yml"
GCLOUD="${GCLOUD:-/Users/gabriel.cerioni/Downloads/google-cloud-sdk/bin/gcloud}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'
say() { echo "${B}${G}»${N} $*"; }
warn() { echo "${B}${Y}⚠${N} $*"; }
die() { echo "${B}${R}✗${N} $*" >&2; exit 1; }

ssh_vm() { "$GCLOUD" compute ssh "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --command "$1" --quiet 2>&1 | { grep -vE "Warning: Permanently|WARNING:|Updating project|^Waiting|Writing|ssh-keygen|Enter passphrase|passphrase" || true; }; }
scp_vm() { "$GCLOUD" compute scp --zone "$VM_ZONE" --project "$VM_PROJECT" "$1" "$VM_NAME:$2" --quiet; }

# ── 1. Validations ────────────────────────────────────────
say "Validating prerequisites..."
command -v "$GCLOUD" >/dev/null || die "gcloud not found at $GCLOUD"
command -v npm >/dev/null || die "npm not on PATH"
[ -f "output/$DOMAIN/customers.jsonl" ] || die "output/$DOMAIN missing (run setup locally first)"
[ -f "domains/$DOMAIN/generated_models.py" ] || die "domains/$DOMAIN/generated_models.py missing"
VM_STATUS=$("$GCLOUD" compute instances describe "$VM_NAME" --zone "$VM_ZONE" --project "$VM_PROJECT" --format "value(status)" 2>/dev/null || echo MISSING)
[ "$VM_STATUS" = "RUNNING" ] || die "VM not RUNNING ($VM_STATUS)"
say "Prereqs OK, VM $VM_NAME RUNNING"

# ── 2. Build frontend (domain-agnostic; reads /api/domain-config at runtime) ──
say "Building frontend (vite)..."
( cd frontend && npm install --silent && npm run build )
[ -f frontend/dist/index.html ] || die "frontend/dist/index.html not generated"
say "Frontend build OK ($(du -sh frontend/dist | cut -f1))"

# ── 3. Ship dist → VM ────────────────────────────────────
say "Shipping dist → $VM_NAME:$REMOTE_BASE/dist/"
DIST_TAR=$(mktemp /tmp/gabs-dist.XXXXXX.tar.gz)
tar -czf "$DIST_TAR" -C frontend/dist .
scp_vm "$DIST_TAR" "/tmp/gabs-dist.tar.gz"; rm -f "$DIST_TAR"
ssh_vm "
  sudo mkdir -p $REMOTE_BASE/dist
  sudo find $REMOTE_BASE/dist -mindepth 1 -delete 2>/dev/null || true
  sudo tar -xzf /tmp/gabs-dist.tar.gz -C $REMOTE_BASE/dist
  sudo rm -f /tmp/gabs-dist.tar.gz
  sudo chown -R root:root $REMOTE_BASE/dist && sudo chmod -R a+rX $REMOTE_BASE/dist
  echo \"dist: \$(sudo find $REMOTE_BASE/dist -type f | wc -l) files\"
"

# ── 4. Ship code → VM ────────────────────────────────────
say "Shipping code → $VM_NAME:$REMOTE_BASE/code/"
CODE_TAR=$(mktemp /tmp/gabs-code.XXXXXX.tar.gz)
tar -czf "$CODE_TAR" \
  --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.git' --exclude='frontend/dist' --exclude='.env' \
  backend domains scripts deploy output pyproject.toml uv.lock Makefile
scp_vm "$CODE_TAR" "/tmp/gabs-code.tar.gz"; rm -f "$CODE_TAR"
ssh_vm "
  sudo mkdir -p $REMOTE_BASE/code
  sudo find $REMOTE_BASE/code -mindepth 1 -delete 2>/dev/null || true
  sudo tar -xzf /tmp/gabs-code.tar.gz -C $REMOTE_BASE/code
  sudo rm -f /tmp/gabs-code.tar.gz
  sudo chown -R \$(whoami):\$(whoami) $REMOTE_BASE/code
"
say "Code shipped OK"

# ── 5. .env (ship local .env if remote missing) ───────────
ENV_OK=$(ssh_vm "[ -f $REMOTE_BASE/.env ] && echo OK || echo MISSING" | tail -1)
if [ "$ENV_OK" != "OK" ]; then
  say "Shipping local .env → $REMOTE_BASE/.env (gabs_bank config + creds)"
  scp_vm ".env" "/tmp/gabs.env"
  ssh_vm "sudo mv /tmp/gabs.env $REMOTE_BASE/.env && sudo chmod 600 $REMOTE_BASE/.env && sudo chown root:root $REMOTE_BASE/.env"
else
  say ".env already present at $REMOTE_BASE/.env (leaving as-is)"
fi

# ── 6. docker compose up -d --build ───────────────────────
say "Building + starting backend container (gabs-bank-backend, host $HOST_PORT)..."
ssh_vm "cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE up -d --build" | tail -15

# ── 7. Health check (host $HOST_PORT) ─────────────────────
say "Waiting for backend health..."
OK=false
for i in $(seq 1 12); do
  sleep 5
  H=$(ssh_vm "curl -sf http://127.0.0.1:$HOST_PORT/api/health 2>/dev/null || echo FAIL" | tail -1)
  if echo "$H" | grep -q '"ok":true'; then say "Backend healthy ✓"; OK=true; break; fi
done
[ "$OK" = true ] || die "Backend did not become healthy. Logs: sudo docker compose -f $COMPOSE logs --tail=60"

# ── 8. Caddy vhost (backup → append → validate → reload; abort safely) ──
if ssh_vm "grep -q '$SUBDOMAIN' /etc/caddy/Caddyfile && echo YES || echo NO" | grep -q YES; then
  say "Caddy vhost for $SUBDOMAIN already present, skipping."
else
  say "Adding Caddy vhost for $SUBDOMAIN (backup + validate + reload)..."
  scp_vm "deploy/gabs_bank/Caddyfile.snippet" "/tmp/gabs.caddy.snippet"
  ssh_vm "
    TS=\$(date +%Y%m%d-%H%M%S)
    sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.gabsbank-\$TS
    sudo bash -c 'cat /tmp/gabs.caddy.snippet >> /etc/caddy/Caddyfile'
    sudo rm -f /tmp/gabs.caddy.snippet
    if sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile; then
      sudo systemctl reload caddy && echo 'CADDY_RELOADED_OK'
    else
      echo 'CADDY_VALIDATE_FAILED — restoring backup'
      sudo cp /etc/caddy/Caddyfile.bak.gabsbank-\$TS /etc/caddy/Caddyfile
      sudo systemctl reload caddy
      exit 1
    fi
  " | tail -20
fi

# ── 9. Summary ────────────────────────────────────────────
echo ""
echo "${B}${G}════════════════════════════════════════════════${N}"
echo "${B}Gabs Bank deploy done.${N}"
echo "${B}════════════════════════════════════════════════${N}"
echo "URL:        https://$SUBDOMAIN"
echo "Backend:    127.0.0.1:$HOST_PORT (container gabs-bank-backend)"
echo "Logs:       gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'cd $REMOTE_BASE/code && sudo docker compose -f $COMPOSE logs -f backend'"
