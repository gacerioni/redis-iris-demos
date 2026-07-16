#!/usr/bin/env bash
#
# fetch_bs2_brand.sh
#
# Baixa o logo público da BS2 Payments (ex-Adiq) pra usar na demo.
# Salva como PNG e atualiza domain.py.
#
# AVISO: o uso da marca BS2/Adiq é responsabilidade do operador. Esta demo
# é de uso interno Redis, sem afiliação oficial Banco BS2 S.A. / Adiq.
#
# Uso:
#   bash scripts/fetch_bs2_brand.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_DIR="$REPO_ROOT/domains/bs2_adiq/assets"
DOMAIN_FILE="$REPO_ROOT/domains/bs2_adiq/domain.py"
mkdir -p "$ASSET_DIR"

# Wordmark oficial servido pelo CMS do site bs2pay.com.br (2221x1500 RGBA),
# com fallbacks de favicon caso o CDN mude.
CANDIDATES=(
  "https://cms-assets-portal.adiq.io/uploads/BS_2_Payments_b0c232e7a4.png"
  "https://www.bs2pay.com.br/apple-touch-icon.png"
  "https://www.google.com/s2/favicons?domain=bs2pay.com.br&sz=256"
  "https://www.google.com/s2/favicons?domain=bs2.com.br&sz=256"
)

echo ""
echo "BS2 Pay brand fetcher"
echo "─────────────────────"

best_file=""
best_size=0
best_mime="image/png"

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
          best_file="$TMPFILE"; best_size="$SIZE"; best_mime="$MIME"
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

TARGET="$ASSET_DIR/logo.png"
mv "$best_file" "$TARGET"
echo ""
echo "✓ Logo salvo: $TARGET ($best_size bytes, $best_mime)"

NEW_LOGO_REL="domains/bs2_adiq/assets/logo.png"
if grep -q 'logo_path="' "$DOMAIN_FILE" 2>/dev/null; then
  sed -i '' "s|logo_path=\"[^\"]*\"|logo_path=\"$NEW_LOGO_REL\"|" "$DOMAIN_FILE"
  echo "✓ domain.py atualizado: logo_path → $NEW_LOGO_REL"
fi

echo "Pronto. O backend deve auto-reload em alguns segundos."
