#!/usr/bin/env bash
#
# fetch_picpay_brand.sh — baixa o favicon/ícone oficial do PicPay pra usar como
# logo do demo. Executado SOB RESPONSABILIDADE DO OPERADOR (uso interno/demo).
# Por padrão o demo usa um placeholder genérico em assets/logo.svg.
#
# Uso:
#   bash scripts/fetch_picpay_brand.sh        # baixa pra assets/logo_oficial.png
#   (depois aponte branding.logo_path pro arquivo baixado, se quiser)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO_ROOT/domains/picpay_assist/assets"
mkdir -p "$DEST"

echo "Baixando ícone oficial do PicPay (apple-touch-icon)..."
if curl -fsSL "https://picpay.com/apple-touch-icon.png" -o "$DEST/logo_oficial.png" 2>/dev/null; then
  echo "  salvo em $DEST/logo_oficial.png"
elif curl -fsSL "https://www.picpay.com/favicon.ico" -o "$DEST/logo_oficial.ico" 2>/dev/null; then
  echo "  favicon salvo em $DEST/logo_oficial.ico"
else
  echo "  não consegui baixar automaticamente — pegue o asset oficial manualmente."
  exit 1
fi
echo "Pronto. Pra usar: ajuste branding.logo_path no domain.py pro arquivo baixado."
