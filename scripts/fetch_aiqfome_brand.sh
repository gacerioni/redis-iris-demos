#!/usr/bin/env bash
#
# fetch_aiqfome_brand.sh
#
# Baixa o ícone público do aiqfome (mascote, 1024x1024) pra usar na demo.
#
# AVISO: o uso da marca aiqfome é responsabilidade do operador. Esta demo
# é de uso interno Redis, sem afiliação oficial aiqfome/Magazine Luiza.
#
# Uso:
#   bash scripts/fetch_aiqfome_brand.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_DIR="$REPO_ROOT/domains/aiqfome/assets"
DOMAIN_FILE="$REPO_ROOT/domains/aiqfome/domain.py"
mkdir -p "$ASSET_DIR"

CANDIDATES=(
  "https://aiqfome.com/icon.png"
  "https://aiqfome.com/apple-touch-icon.png"
  "https://www.google.com/s2/favicons?domain=aiqfome.com&sz=256"
)

echo ""
echo "aiqfome brand fetcher"
echo "─────────────────────"

best_file=""
best_size=0

for URL in "${CANDIDATES[@]}"; do
  echo "Tentando: $URL"
  TMPFILE=$(mktemp)
  if curl -sfL --max-time 15 "$URL" -o "$TMPFILE"; then
    SIZE=$(wc -c < "$TMPFILE" | tr -d ' ')
    MIME=$(file -b --mime-type "$TMPFILE" 2>/dev/null || echo "unknown")
    case "$MIME" in
      image/png|image/jpeg|image/webp|image/svg+xml)
        echo "  OK ($MIME, ${SIZE} bytes)"
        if [ "$SIZE" -gt "$best_size" ]; then
          if [ -n "$best_file" ]; then rm -f "$best_file"; fi
          best_file="$TMPFILE"; best_size="$SIZE"
          continue
        fi
        ;;
      *) echo "  IGNORADO (tipo $MIME)" ;;
    esac
  else
    echo "  FALHOU"
  fi
  rm -f "$TMPFILE"
done

if [ -z "$best_file" ]; then
  echo "Nenhum candidato funcionou. Mantendo o logo atual."
  exit 1
fi

mv "$best_file" "$ASSET_DIR/logo.png"
echo ""
echo "✓ Logo salvo: $ASSET_DIR/logo.png ($best_size bytes)"

NEW_LOGO_REL="domains/aiqfome/assets/logo.png"
if grep -q 'logo_path="' "$DOMAIN_FILE" 2>/dev/null; then
  sed -i '' "s|logo_path=\"[^\"]*\"|logo_path=\"$NEW_LOGO_REL\"|" "$DOMAIN_FILE"
  echo "✓ domain.py atualizado: logo_path → $NEW_LOGO_REL"
fi

echo "Pronto."
