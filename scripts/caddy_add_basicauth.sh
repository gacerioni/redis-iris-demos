#!/usr/bin/env bash
#
# caddy_add_basicauth.sh — add HTTP basic_auth to specific Caddy vhosts, safely.
#
# Runs ON THE VM as root:
#   sudo bash caddy_add_basicauth.sh <user> <plaintext_pw> <host1> [host2 ...]
#
# Idempotent (skips a vhost that already has basic_auth). Backs up the Caddyfile,
# inserts the block right after each `<host> {` line, runs `caddy validate`, and
# only reloads if valid; otherwise restores the backup. Never touches vhosts not
# listed. No `log` directive involved. Password is hashed with bcrypt via caddy,
# never stored in plaintext in the Caddyfile.

set -euo pipefail

USER_NAME="${1:?usage: caddy_add_basicauth.sh <user> <password> <host...>}"
PLAIN="${2:?password required}"
shift 2
HOSTS=("$@")
[ ${#HOSTS[@]} -gt 0 ] || { echo "no hosts given"; exit 2; }

CADDYFILE=/etc/caddy/Caddyfile
HASH="$(caddy hash-password --plaintext "$PLAIN")"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$CADDYFILE.bak.basicauth-$TS"
cp "$CADDYFILE" "$BACKUP"
echo "backup: $BACKUP"

CADDY_USER="$USER_NAME" CADDY_HASH="$HASH" python3 - "${HOSTS[@]}" <<'PYEOF'
import os, sys
user = os.environ["CADDY_USER"]
h = os.environ["CADDY_HASH"]
hosts = sys.argv[1:]
path = "/etc/caddy/Caddyfile"
s = open(path).read()
block = "    basic_auth {\n        %s %s\n    }\n" % (user, h)
for host in hosts:
    marker = host + " {\n"
    i = s.find(marker)
    if i < 0:
        print("WARN: host block not found:", host)
        continue
    # idempotent: skip if this block already has basic_auth near its top
    if "basic_auth" in s[i:i + 500]:
        print("already protected, skipping:", host)
        continue
    j = i + len(marker)
    s = s[:j] + block + s[j:]
    print("protected:", host)
open(path, "w").write(s)
PYEOF

echo "validating..."
if caddy validate --config "$CADDYFILE" --adapter caddyfile; then
    systemctl reload caddy
    echo "BASICAUTH_APPLIED_OK"
else
    echo "VALIDATE_FAILED — restoring backup and reloading"
    cp "$BACKUP" "$CADDYFILE"
    systemctl reload caddy
    exit 1
fi
