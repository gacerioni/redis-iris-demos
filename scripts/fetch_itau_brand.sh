#!/usr/bin/env bash
#
# fetch_itau_brand.sh
#
# Tenta baixar o asset público de mais alta resolução disponível em
# itau.com.br pra usar como logo do demo. Salva como PNG (formato
# aceito pelo _logo_src do framework) e atualiza domain.py.
#
# AVISO: o uso da marca Itaú é responsabilidade do operador. Esta demo
# é de uso interno Redis, sem afiliação oficial Itaú Unibanco S.A.
# Se você não tem autorização, NÃO rode este script — o placeholder em
# domains/itau_assist/assets/logo.svg cumpre a função visual.
#
# Uso:
#   bash scripts/fetch_itau_brand.sh
#
# Pré-requisitos: curl, file

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_DIR="$REPO_ROOT/domains/itau_assist/assets"
BACKUP="$ASSET_DIR/logo.placeholder.svg"
DOMAIN_FILE="$REPO_ROOT/domains/itau_assist/domain.py"

# Lista de candidatos em ordem de preferência (maior → menor resolução)
CANDIDATES=(
  "https://www.itau.com.br/apple-touch-icon-180x180.png"
  "https://www.itau.com.br/apple-touch-icon.png"
  "https://www.itau.com.br/apple-touch-icon-precomposed.png"
  "https://www.itau.com.br/favicon-96x96.png"
  "https://www.itau.com.br/favicon-32x32.png"
  "https://www.google.com/s2/favicons?domain=itau.com.br&sz=256"
  "https://www.google.com/s2/favicons?domain=itau.com.br&sz=128"
)

echo ""
echo "Itaú brand fetcher"
echo "──────────────────"
echo "AVISO: você é responsável pela autorização de uso da marca Itaú nesta demo."
echo "Uso interno Redis, sem afiliação oficial Itaú Unibanco S.A."
echo ""

# Backup do SVG placeholder original (uma vez só)
SVG_PLACEHOLDER="$ASSET_DIR/logo.svg"
if [ -f "$SVG_PLACEHOLDER" ] && [ ! -f "$BACKUP" ]; then
  cp "$SVG_PLACEHOLDER" "$BACKUP"
  echo "Backup do placeholder salvo em: logo.placeholder.svg"
fi

best_file=""
best_size=0

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
          if [ -n "$best_file" ]; then rm -f "$best_file"; fi
          best_file="$TMPFILE"
          best_size="$SIZE"
          best_mime="$MIME"
          continue
        fi
        ;;
      *)
        echo "  IGNORADO (tipo $MIME)"
        ;;
    esac
  else
    echo "  FALHOU"
  fi
  rm -f "$TMPFILE"
done

if [ -z "$best_file" ]; then
  echo ""
  echo "Nenhum candidato funcionou. Mantendo placeholder em logo.svg."
  echo "Você pode baixar manualmente e salvar em $ASSET_DIR/logo.{png,svg,jpg}"
  exit 1
fi

# Define extensão de saída
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
echo "✓ Melhor asset salvo: logo.$EXT ($best_size bytes, $best_mime)"

# Atualiza domain.py pra apontar pro novo arquivo
CURRENT_LOGO=$(grep -E '^\s*logo_path=' "$DOMAIN_FILE" | head -1 | sed 's/.*logo_path="\([^"]*\)".*/\1/')
NEW_LOGO_REL="domains/itau_assist/assets/logo.$EXT"
if [ "$CURRENT_LOGO" != "$NEW_LOGO_REL" ]; then
  sed -i '' "s|logo_path=\"[^\"]*\"|logo_path=\"$NEW_LOGO_REL\"|" "$DOMAIN_FILE"
  echo "✓ domain.py atualizado: logo_path → $NEW_LOGO_REL"
else
  echo "  domain.py já aponta pro logo correto"
fi

echo ""
echo "Pronto. O backend deve auto-reload em alguns segundos."
echo "Pra reverter pro placeholder:"
echo "  cp $BACKUP $ASSET_DIR/logo.svg"
echo "  # depois edite domain.py voltando logo_path pra domains/itau_assist/assets/logo.svg"
