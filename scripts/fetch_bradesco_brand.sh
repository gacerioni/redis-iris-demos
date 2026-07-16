#!/usr/bin/env bash
#
# fetch_bradesco_brand.sh — baixa o logo oficial do Bradesco pra usar no demo.
# Executado SOB RESPONSABILIDADE DO OPERADOR (uso interno/demo). O domain.py já
# aponta pra domains/bradesco_bia/assets/logo_oficial.png.
#
# Uso: bash scripts/fetch_bradesco_brand.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO_ROOT/domains/bradesco_bia/assets"
mkdir -p "$DEST"

echo "Baixando logo oficial do Bradesco..."
for url in \
  "https://logo.clearbit.com/bradesco.com.br?size=256" \
  "https://www.google.com/s2/favicons?domain=bradesco.com.br&sz=256"; do
  if curl -fsSL --compressed --max-time 15 -A "Mozilla/5.0" "$url" -o "$DEST/logo_oficial.png" 2>/dev/null; then
    if file -b "$DEST/logo_oficial.png" | grep -qiE "PNG image"; then
      echo "  salvo em $DEST/logo_oficial.png (de $url)"; exit 0
    fi
  fi
done
echo "  não consegui baixar automaticamente. Pegue o asset oficial manualmente."
exit 1
