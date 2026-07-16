#!/usr/bin/env bash
# reset_bradesco_irisbia_data.sh — devolve os DADOS do demo Bradesco BIA (na caixa
# irisbia) ao estado pristine de apresentação, SEM flush e SEM re-mintar a surface.
#
# É cirúrgico de propósito: um FLUSHDB derrubaria o índice VSS de políticas (recriado
# só pelo setup_surface) e o índice do guardrail. Aqui só:
#   1) restaura as 3 entidades que as tools mutam (saldo, CDB, limite do cartão)
#   2) apaga os órfãos gerados pelos testes (LCI aplicada, Pix enviados de teste)
# A surface lê esses keys direto do Redis (RediSearch reindexa no write/del), então
# o agente vê o estado novo na hora.
#
# Uso:  EC2_HOST=ubuntu@56.124.109.24 SSH_KEY=~/Downloads/gabs-itau-sa-east-1.pem \
#         bash scripts/reset_bradesco_irisbia_data.sh
set -euo pipefail

EC2_HOST="${EC2_HOST:-ubuntu@56.124.109.24}"
SSH_KEY="${SSH_KEY:-$HOME/Downloads/gabs-itau-sa-east-1.pem}"

# Valores canônicos do seed (domains/bradesco_bia + generate_data).
SALDO_SEED="92300.5"
CDB_SEED="180000"
LIMITE_SEED="80000"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_HOST" \
  "SALDO_SEED='$SALDO_SEED' CDB_SEED='$CDB_SEED' LIMITE_SEED='$LIMITE_SEED' bash -s" <<'EOF'
set -euo pipefail
# Lê só as vars do Redis (não dá source no .env: ele tem valores com espaço, ex. nome do cliente).
ENV=/opt/iris-bia/.env
RH=$(grep -E '^REDIS_HOST=' "$ENV" | cut -d= -f2-)
RP=$(grep -E '^REDIS_PORT=' "$ENV" | cut -d= -f2-)
RPW=$(grep -E '^REDIS_PASSWORD=' "$ENV" | cut -d= -f2-)
RC="redis-cli -h $RH -p $RP -a $RPW --no-auth-warning"

echo "Bradesco BIA (irisbia) — reset de dados pristine"
echo "════════════════════════════════════════════════"

echo "[1/5] saldo conta corrente -> R\$ $SALDO_SEED"
$RC JSON.SET bradesco_bia_account:ACC_001 '$.saldo' "$SALDO_SEED" >/dev/null

echo "[2/5] CDB -> R\$ $CDB_SEED"
$RC JSON.SET bradesco_bia_investment:INV_CDB '$.valor_aplicado' "$CDB_SEED" >/dev/null

echo "[3/5] limite Elo Nanquim -> R\$ $LIMITE_SEED"
$RC JSON.SET bradesco_bia_card:CARD_NANQUIM '$.limite' "$LIMITE_SEED" >/dev/null

echo "[4/5] apagando LCIs aplicadas em teste (INV_LCI_*)"
LCI=$($RC --scan --pattern 'bradesco_bia_investment:INV_LCI_*')
[ -n "$LCI" ] && echo "$LCI" | xargs -r $RC DEL >/dev/null && echo "   removidas: $(echo "$LCI" | wc -l | tr -d ' ')" || echo "   nenhuma"

echo "[5/5] apagando Pix de teste (TXN_PIX_*)"
PIX=$($RC --scan --pattern 'bradesco_bia_transaction:TXN_PIX_*')
[ -n "$PIX" ] && echo "$PIX" | xargs -r $RC DEL >/dev/null && echo "   removidos: $(echo "$PIX" | wc -l | tr -d ' ')" || echo "   nenhum"

echo ""
echo "Estado final:"
echo -n "  saldo  : "; $RC JSON.GET bradesco_bia_account:ACC_001 '$.saldo'
echo -n "  CDB    : "; $RC JSON.GET bradesco_bia_investment:INV_CDB '$.valor_aplicado'
echo -n "  limite : "; $RC JSON.GET bradesco_bia_card:CARD_NANQUIM '$.limite'
echo -n "  invest : "; $RC --scan --pattern 'bradesco_bia_investment:*' | sort | tr '\n' ' '; echo ""
echo -n "  pix tx : "; PIX_COUNT=$($RC --scan --pattern 'bradesco_bia_transaction:TXN_PIX_*' | grep -c 'TXN_PIX_' 2>/dev/null || echo 0); echo "$PIX_COUNT (esperado 0)"
echo ""
echo "Pristine. (memórias LTM e índices VSS/guardrail intactos.)"
EOF
