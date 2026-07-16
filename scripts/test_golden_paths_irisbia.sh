#!/usr/bin/env bash
# Golden-paths live test harness for irisbia (Bradesco BIA concierge).
# Reproducible: every prompt lives here, zero ad-hoc in the chat. Runs against the
# DEPLOYED box at https://irisbia.platformengineer.io (basic_auth iris/Secret_42).
#
# Usage:
#   bash scripts/test_golden_paths_irisbia.sh pix         # multi-turn Pix (saldo debita)
#   bash scripts/test_golden_paths_irisbia.sh raiox       # raio-X da conta
#   bash scripts/test_golden_paths_irisbia.sh recomenda   # recomenda -> aplica (multi-turn)
#   bash scripts/test_golden_paths_irisbia.sh multiturn   # raio-X -> recomenda -> aplica (1 thread)
#   bash scripts/test_golden_paths_irisbia.sh limite      # aumento de limite
#   bash scripts/test_golden_paths_irisbia.sh contestacao # cobrança não reconhecida
#   bash scripts/test_golden_paths_irisbia.sh copa        # easter egg Copa 2026
#   bash scripts/test_golden_paths_irisbia.sh saldo <thread>  # só pergunta o saldo numa thread
set -uo pipefail

BASE="${BASE:-https://irisbia.platformengineer.io}"
AUTH="${AUTH:-iris:Secret_42}"
ENDPOINT="$BASE/api/chat/stream"

# Parser do stream SSE escrito num arquivo (pipar curl -> python3 ARQUIVO; um heredoc
# em `python3 - <<EOF` faria o python ler o PROGRAMA do stdin e o stream iria pro vazio).
PARSER="$(mktemp "${TMPDIR:-/tmp}/iris_sse_parse.XXXXXX.py")"
trap 'rm -f "$PARSER"' EXIT
cat > "$PARSER" <<'PY'
import sys, json
tools=[]; text=[]; flags=[]; guard=None
for line in sys.stdin:
    line=line.strip()
    if not line.startswith("data:"): continue
    try: ev=json.loads(line[5:].strip())
    except Exception: continue
    t=ev.get("type")
    if t=="tool-call": tools.append(ev.get("toolName"))
    elif t=="tool-result" and ev.get("toolName")=="guardrail_check":
        guard=ev.get("payload",{})
    elif t=="text-delta": text.append(ev.get("delta",""))
    elif t=="done":
        if ev.get("cacheHit"): flags.append("⚡ CACHE HIT")
        if ev.get("guardrailBlocked"): flags.append("\U0001f6e1 BLOCKED")
if guard: print(f"   guardrail: allowed={guard.get('allowed')} route={guard.get('route')} dist={guard.get('distance')}")
if tools: print("   tools:", " -> ".join(t for t in tools if t))
if flags: print("   " + " | ".join(flags))
print(">>", "".join(text).strip() or "(sem texto)")
PY

ask() {
  local thread="$1"; shift
  local msg="$1"; shift
  echo ""
  echo "────────────────────────────────────────────────────────────────────"
  echo "🧑 [$thread] $msg"
  echo "────────────────────────────────────────────────────────────────────"
  local body
  body="$(python3 -c 'import json,sys; print(json.dumps({"messages":[{"role":"user","content":sys.argv[1]}],"thread_id":sys.argv[2]}))' "$msg" "$thread")"
  curl -sN --max-time 120 -u "$AUTH" -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' -d "$body" \
  | python3 "$PARSER"
}

SCEN="${1:-pix}"
TS="$(date +%s)"

case "$SCEN" in
  pix)
    TH="pix-$TS"
    ask "$TH" "Manda R\$ 200 pro Carlos pelo Pix."
    ask "$TH" "Isso, pode confirmar."
    ask "$TH" "E qual meu saldo agora?"
    ;;
  raiox)
    TH="raiox-$TS"
    ask "$TH" "Me dá um raio-X da minha conta."
    ;;
  recomenda)
    TH="reco-$TS"
    ask "$TH" "Onde meu dinheiro rende mais?"
    ask "$TH" "Gostei, pode aplicar."
    ;;
  multiturn)
    TH="mt-$TS"
    ask "$TH" "Me dá um raio-X da minha conta."
    ask "$TH" "E o que você recomenda que eu faça com o dinheiro parado?"
    ask "$TH" "Fechado, pode aplicar o que você sugeriu."
    ask "$TH" "Confirma quanto sobrou no CDB depois disso?"
    ;;
  limite)
    TH="lim-$TS"
    ask "$TH" "Quero aumentar meu limite do cartão."
    ask "$TH" "Pode seguir."
    ;;
  contestacao)
    TH="cont-$TS"
    ask "$TH" "Tem uma cobrança na minha fatura que eu não reconheço."
    ;;
  copa)
    TH="copa-$TS"
    ask "$TH" "Vou pra Copa do Mundo de 2026, o que o Bradesco tem pra me ajudar?"
    ;;
  saldo)
    ask "${2:-saldo-$TS}" "Qual meu saldo da conta corrente?"
    ;;
  *)
    echo "Cenário desconhecido: $SCEN"; exit 1;;
esac
