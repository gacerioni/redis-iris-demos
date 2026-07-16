#!/usr/bin/env bash
#
# fetch_serasa_brand.sh
#
# Baixa o asset público de mais alta resolução de serasa.com.br (favicon /
# apple-touch-icon) pra usar como logo do demo. Salva como PNG e atualiza
# domain.py.
#
# AVISO: o uso da marca Serasa Experian é responsabilidade do operador.
# Esta demo é de uso interno Redis, sem afiliação oficial com Serasa Experian
# S.A. Se você não tem autorização, NÃO rode este script — o placeholder em
# domains/serasa_limpa_nome/assets/logo.svg cumpre a função visual.
#
# Uso:
#   bash scripts/fetch_serasa_brand.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_DIR="$REPO_ROOT/domains/serasa_limpa_nome/assets"
BACKUP="$ASSET_DIR/logo.placeholder.svg"
DOMAIN_FILE="$REPO_ROOT/domains/serasa_limpa_nome/domain.py"

CANDIDATES=(
  "https://www.serasa.com.br/apple-touch-icon-180x180.png"
  "https://www.serasa.com.br/apple-touch-icon.png"
  "https://www.serasa.com.br/apple-touch-icon-precomposed.png"
  "https://www.serasa.com.br/favicon-96x96.png"
  "https://www.google.com/s2/favicons?domain=serasa.com.br&sz=256"
  "https://www.google.com/s2/favicons?domain=serasa.com.br&sz=128"
)

echo ""
echo "Serasa brand fetcher"
echo "────────────────────"
echo "AVISO: você é responsável pela autorização de uso da marca Serasa Experian."
echo "Uso interno Redis, sem afiliação oficial."
echo ""

SVG_PLACEHOLDER="$ASSET_DIR/logo.svg"
if [ -f "$SVG_PLACEHOLDER" ] && [ ! -f "$BACKUP" ]; then
  cp "$SVG_PLACEHOLDER" "$BACKUP"
  echo "Backup do placeholder salvo: logo.placeholder.svg"
fi

best_file=""
best_size=0
best_mime=""

for URL in "${CANDIDATES[@]}"; do
  echo "Tentando: $URL"
  TMPFILE=$(mktemp)
  if curl -sfL --max-time 10 "$URL" -o "$TMPFILE"; then
    SIZE=$(wc -c < "$TMPFILE" | tr -d ' ')
    MIME=$(file -b --mime-type "$TMPFILE" 2>/dev/null || echo "unknown")
    case "$MIME" in
      image/png|image/jpeg|image/webp|image/svg+xml)
        echo "  OK ($MIME, ${SIZE} bytes)"
        if [ "$SIZE" -gt "$best_size" ]; then
          [ -n "$best_file" ] && rm -f "$best_file"
          best_file="$TMPFILE"
          best_size="$SIZE"
          best_mime="$MIME"
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
  echo ""
  echo "Nenhum candidato funcionou. Mantendo placeholder em logo.svg."
  exit 1
fi

case "$best_mime" in
  image/png) EXT="png" ;;
  image/jpeg) EXT="jpg" ;;
  image/webp) EXT="webp" ;;
  image/svg+xml) EXT="svg" ;;
  *) EXT="png" ;;
esac

TARGET="$ASSET_DIR/logo.$EXT"
mv "$best_file" "$TARGET"
echo ""
echo "✓ Asset salvo: logo.$EXT ($best_size bytes)"

NEW_LOGO_REL="domains/serasa_limpa_nome/assets/logo.$EXT"
CURRENT_LOGO=$(grep -E '^\s*logo_path=' "$DOMAIN_FILE" | head -1 | sed 's/.*logo_path="\([^"]*\)".*/\1/')
if [ "$CURRENT_LOGO" != "$NEW_LOGO_REL" ]; then
  sed -i '' "s|logo_path=\"[^\"]*\"|logo_path=\"$NEW_LOGO_REL\"|" "$DOMAIN_FILE"
  echo "✓ domain.py atualizado: logo_path → $NEW_LOGO_REL"
fi

echo ""
echo "Pra reverter: cp $BACKUP $SVG_PLACEHOLDER"
