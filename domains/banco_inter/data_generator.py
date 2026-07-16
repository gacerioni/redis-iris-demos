"""Banco Inter (Babi) — seed sintético em PT-BR.

Persona: Gabriel Cerioni, cliente Inter One (alta renda), 6 anos de Inter, super
app (conta digital gratuita + Inter Invest + Loop cashback + Inter Shop). Features
online no feature store calibradas pra um next-best-offer interessante: alta
propensão a investimento + caixa parado em CDB tributado => o modelo recomenda
migrar pra LCI isenta. As tools determinísticas escrevem em runtime.

Demo interna Redis, sem afiliação oficial com o Banco Inter S.A.
"""

from __future__ import annotations

import json
import os
import sys
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "banco_inter"
now = datetime.now(timezone.utc)


def ts(dt: datetime) -> str:
    return dt.isoformat()


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(t) for t in texts]
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input=texts, model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in resp.data]


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


DEMO_USER_ID = "CUST_DEMO_001"

# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMER
# ═══════════════════════════════════════════════════════════════════════════
CUSTOMERS = [
    {
        "customer_id": DEMO_USER_ID,
        "nome": "Gabriel Cerioni",
        "cpf_masked": "***.456.789-**",
        "email": "gabriel.cerioni@example.com.br",
        "cidade": "São Paulo",
        "segmento": "inter_one",
        "agencia": "0001",
        "conta": "***.***-7",
        "cliente_desde_anos": 6,
        "renda_mensal": 45000.00,
        "score_interno": 920,
        "perfil_investidor": "moderado",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  ACCOUNTS — conta digital gratuita + conta Inter Invest
# ═══════════════════════════════════════════════════════════════════════════
ACCOUNTS = [
    {"account_id": "ACC_001", "customer_id": DEMO_USER_ID, "tipo": "corrente",
     "saldo": 92300.50, "limite_cheque_especial": 50000.00, "status": "ativa"},
    {"account_id": "ACC_002", "customer_id": DEMO_USER_ID, "tipo": "investimento",
     "saldo": 220000.00, "limite_cheque_especial": 0.00, "status": "ativa"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  CARDS — Inter Black (Mastercard Black, anuidade zero) + cartão de débito Inter
# ═══════════════════════════════════════════════════════════════════════════
CARDS = [
    {"card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID, "produto": "Inter Black",
     "tipo": "credito", "bandeira": "mastercard", "final": "8821", "limite": 80000.00,
     "fatura_atual": 17850.40, "vencimento": ts(now + timedelta(days=10)), "anuidade": 0.00, "status": "ativo"},
    {"card_id": "CARD_DEB", "customer_id": DEMO_USER_ID, "produto": "Cartão Inter",
     "tipo": "debito", "bandeira": "mastercard", "final": "3310", "limite": 0.00,
     "fatura_atual": 0.00, "vencimento": ts(now + timedelta(days=30)), "anuidade": 0.00, "status": "ativo"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _txn(i, card, acc, tipo, merchant, mcc, valor, days_ago, rec="nao", status="aprovada", pa=1, pt=1):
    return {"txn_id": f"TXN_{i:03d}", "customer_id": DEMO_USER_ID, "card_id": card, "account_id": acc,
            "tipo": tipo, "merchant": merchant, "mcc": mcc, "valor": round(valor, 2),
            "data": ts(now - timedelta(days=days_ago)), "is_recurring": rec,
            "parcela_atual": pa, "parcela_total": pt,
            "valor_parcela": round(valor / pt, 2) if pt else round(valor, 2),
            "status": status}

TRANSACTIONS = [
    # ── Parcelados na fatura (o use case que faltava) ──
    _txn(1, "CARD_BLACK", None, "compra_credito", "APPLE STORE IGUATEMI", "5732", 9600.00, 70, pa=3, pt=12),      # iPhone 12x
    _txn(2, "CARD_BLACK", None, "compra_credito", "LATAM AIRLINES MIAMI", "3174", 7200.00, 40, pa=2, pt=6),       # passagem 6x
    _txn(3, "CARD_BLACK", None, "compra_credito", "INTER SHOP ELETRONICOS", "5712", 4500.00, 130, pa=5, pt=10),   # Inter Shop 10x
    _txn(4, "CARD_BLACK", None, "compra_credito", "FAST SHOP NOTEBOOK", "5732", 6400.00, 20, pa=1, pt=8),         # notebook 8x
    # ── Recorrentes (assinaturas reconhecidas) ──
    _txn(5, "CARD_BLACK", None, "compra_credito", "NETFLIX.COM", "4899", 55.90, 5, rec="sim"),
    _txn(6, "CARD_BLACK", None, "compra_credito", "SPOTIFY BR", "4899", 34.90, 6, rec="sim"),
    _txn(7, "CARD_BLACK", None, "compra_credito", "AMAZON PRIME BR", "5968", 19.90, 2, rec="sim"),
    # ── À vista (lifestyle: restaurante, vinho, combustível, shopping) ──
    _txn(8, "CARD_BLACK", None, "compra_credito", "RESTAURANTE DOM", "5812", 1240.00, 4),
    _txn(9, "CARD_BLACK", None, "compra_credito", "WINE.COM.BR", "5921", 980.00, 12),
    _txn(10, "CARD_BLACK", None, "compra_credito", "POSTO SHELL SELECT", "5541", 420.00, 8),
    _txn(11, "CARD_BLACK", None, "compra_credito", "DROGARIA SAO PAULO", "5912", 186.30, 10),
    _txn(12, "CARD_BLACK", None, "compra_credito", "IGUATEMI SP", "5651", 2150.00, 14),
    # ── Pix e conta (família, aluguel, cashback Loop) ──
    _txn(13, None, "ACC_001", "pix_recebido", "Aluguel Imóvel SP", "PIX", 6500.00, 4, rec="sim"),
    _txn(14, None, "ACC_001", "pix_enviado", "Sofia Cerioni (mensalidade)", "PIX", 3800.00, 5, rec="sim"),
    _txn(15, None, "ACC_001", "pix_enviado", "Tia Eulália", "PIX", 800.00, 1, rec="sim"),
    _txn(16, None, "ACC_002", "cashback", "Loop Cashback Inter", "CASH", 230.00, 2),
]

# ═══════════════════════════════════════════════════════════════════════════
#  BILLING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
BILLING_CYCLES = [
    {"cycle_id": "BILL_BLACK_ABERTA", "card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID,
     "mes_referencia": now.strftime("%Y-%m"), "valor_total": 17850.40, "valor_minimo": 2677.56,
     "vencimento": ts(now + timedelta(days=10)), "status": "aberta"},
    {"cycle_id": "BILL_BLACK_ANTERIOR", "card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID,
     "mes_referencia": (now - timedelta(days=30)).strftime("%Y-%m"), "valor_total": 14230.00,
     "valor_minimo": 2134.50, "vencimento": ts(now - timedelta(days=20)), "status": "paga"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  INVESTMENTS — Gabriel tem caixa parado em CDB tributado (gancho do NBO)
# ═══════════════════════════════════════════════════════════════════════════
INVESTMENTS = [
    {"investment_id": "INV_CDB", "customer_id": DEMO_USER_ID, "produto": "CDB",
     "descricao": "CDB Inter pós-fixado 100% CDI", "valor_aplicado": 180000.00,
     "rentabilidade_cdi_pct": 100, "vencimento": ts(now + timedelta(days=400)), "liquidez": "diaria"},
    {"investment_id": "INV_FUNDO", "customer_id": DEMO_USER_ID, "produto": "Fundo",
     "descricao": "Inter Invest FIC Renda Fixa", "valor_aplicado": 40000.00,
     "rentabilidade_cdi_pct": 98, "vencimento": ts(now + timedelta(days=180)), "liquidez": "D_mais_30"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  PIX CONTACTS
# ═══════════════════════════════════════════════════════════════════════════
PIX_CONTACTS = [
    {"contact_id": "PIX_CARLOS", "customer_id": DEMO_USER_ID, "nome": "Carlos Eduardo Souza",
     "chave_pix": "+55 11 95333-2002", "tipo_chave": "celular", "banco": "Inter", "is_frequente": "sim"},
    {"contact_id": "PIX_EULALIA", "customer_id": DEMO_USER_ID, "nome": "Tia Eulália Cerioni",
     "chave_pix": "eulalia.***@email.com", "tipo_chave": "email", "banco": "Itaú", "is_frequente": "sim"},
    {"contact_id": "PIX_SOFIA", "customer_id": DEMO_USER_ID, "nome": "Sofia Cerioni",
     "chave_pix": "***.111.222-**", "tipo_chave": "cpf", "banco": "Inter", "is_frequente": "sim"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES
# ═══════════════════════════════════════════════════════════════════════════
DISPUTES = [
    {"dispute_id": "DSP_HIST", "customer_id": DEMO_USER_ID, "transaction_id": None,
     "motivo": "Cobrança duplicada em assinatura, resolvida em 2025", "valor": 49.90,
     "status": "procedente", "data": ts(now - timedelta(days=120))},
]

# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE — features online do Gabriel (o coração do diferencial)
#  Calibrado: alta propensão a investimento + caixa parado => NBO = LCI isenta
# ═══════════════════════════════════════════════════════════════════════════
FEATURE_STORE = [
    {
        "customer_id": DEMO_USER_ID,
        "renda_mensal": 45000.00,
        "score_interno": 920,
        "utilizacao_cartao_pct": 22,
        "tenure_meses": 72,
        "velocity_gasto_30d": 28500.00,
        "saldo_medio_3m": 88000.00,
        "num_produtos": 4,
        "propensao_investimento": 0.88,
        "propensao_credito": 0.31,
        "propensao_seguro": 0.64,
        "perfil_digital": "alto",
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — ajuda/políticas do Inter, embedding em runtime
# ═══════════════════════════════════════════════════════════════════════════
POLICIES_TEXT = [
    {"policy_id": "POL_PIX", "title": "Limites de Pix por horário", "category": "limites",
     "content": "Limites do Pix Inter por horário. Durante o dia, das 6h às 20h, o limite é de "
                "R$ 10.000 por transação. À noite e de madrugada, das 20h às 6h, o limite noturno cai "
                "para R$ 1.000 por transação, por segurança. Pix entre contas Inter é instantâneo, "
                "gratuito e disponível 24 horas. Clientes Inter One podem solicitar limites estendidos "
                "pelo app, sem tarifa."},
    {"policy_id": "POL_CONTESTACAO", "title": "Contestação de cobranças", "category": "contestacao",
     "content": "Pra contestar uma cobrança: confirme que não reconhece a transação, abra a contestação "
                "pelo app ou com a Babi, e o valor entra em análise com estorno provisório em casos "
                "elegíveis. Prazo de até 7 dias úteis, com protocolo. Cobrança recorrente reconhecida "
                "(assinatura) tende a ser analisada como improcedente, então confirme antes."},
    {"policy_id": "POL_CARTAO", "title": "Cartões e anuidade Inter", "category": "cartao",
     "content": "O cartão Inter e o Inter Black têm anuidade ZERO, sempre, sem exigência de gasto mínimo. "
                "Você acompanha a fatura, ajusta o limite e bloqueia o cartão pelo app, na hora. Aumento "
                "de limite passa por análise de score e uso. O Inter Black é um Mastercard Black, com "
                "acesso a salas VIP (LoungeKey) e benefícios Mastercard."},
    {"policy_id": "POL_INVEST", "title": "Investimentos na Inter Invest", "category": "investimento",
     "content": "A Inter Invest oferece CDB, LCI, LCA, Tesouro Direto, fundos e previdência (PGBL/VGBL). "
                "LCI e LCA são isentas de IR pra pessoa física, ótimas pra quem tem caixa parado em CDB "
                "tributado. Os CDBs do Inter costumam pagar acima de 100% do CDI. A previdência PGBL tem "
                "benefício fiscal pra quem declara no completo. A recomendação depende do perfil de "
                "investidor e do objetivo."},
    {"policy_id": "POL_INTER_ONE", "title": "Benefícios Inter One", "category": "inter_one",
     "content": "O Inter One é o segmento de alta renda do Inter: assessor de investimentos dedicado, "
                "ofertas e eventos exclusivos, cartão Inter Black sem anuidade e atendimento prioritário. "
                "Tudo pelo app, sem agência e sem tarifa de manutenção. É relacionamento premium com a "
                "praticidade do digital."},
    {"policy_id": "POL_SEGURANCA", "title": "Segurança e golpe do Pix", "category": "seguranca",
     "content": "Desconfie de chaves Pix recém-criadas, pedidos urgentes e prêmios. O Inter sinaliza "
                "transações com padrão atípico. Se você foi vítima de golpe ou suspeita de acesso indevido, "
                "bloqueie o cartão pelo app, troque a senha e registre a ocorrência. A Babi nunca pede sua "
                "senha nem código de acesso."},
    {"policy_id": "POL_LOOP", "title": "Loop, o cashback do Inter", "category": "cashback",
     "content": "O Loop é o programa de cashback do Inter: você ganha dinheiro de volta (não pontos) em "
                "compras no crédito, no débito, no Inter Shop e em parceiros. O cashback cai direto na sua "
                "conta e pode render junto no CDB, ou virar aporte no Meu Porquinho. No Inter Shop o "
                "cashback é ampliado. Você acompanha o acumulado pelo app."},
    {"policy_id": "POL_SEGURO", "title": "Seguros Inter", "category": "investimento",
     "content": "A Inter Seguros oferece seguro de vida, residencial, viagem e proteção de cartão e "
                "celular. Clientes Inter One e portadores do Inter Black têm coberturas ampliadas e "
                "assistências premium. Dá pra contratar pelo app e ajustar a cobertura conforme o perfil."},
    {"policy_id": "POL_LGPD", "title": "Privacidade e LGPD", "category": "lgpd",
     "content": "Seus dados são protegidos pela LGPD. O Inter não compartilha seu histórico com terceiros "
                "sem consentimento. Você pode consultar, exportar ou solicitar exclusão dos seus dados "
                "pelos canais oficiais do app."},
    {"policy_id": "POL_INTERNACIONAL", "title": "Cartão internacional, Conta Global, IOF e seguro viagem", "category": "cartao",
     "content": "Pra usar o cartão no exterior, ative as compras internacionais pelo app e avise sua "
                "viagem (datas e destino) pra evitar bloqueio preventivo. Compras internacionais no crédito "
                "têm IOF de 3,38% sobre o valor convertido, já embutido na fatura, sem surpresa. Pague "
                "sempre em moeda local, nunca em real, pra fugir do câmbio ruim do estabelecimento. O Inter "
                "tem a Conta Global, uma conta em dólar sem mensalidade, ótima pra carregar antes da viagem "
                "e gastar no débito lá fora. O Inter Black inclui seguro viagem (cobertura médica e de "
                "bagagem) e acesso a salas VIP em aeroportos (LoungeKey). Dá pra contratar seguro viagem "
                "avulso com cobertura ampliada e pedir folga temporária de limite pro período da viagem, "
                "tudo pelo app. Use o crédito no exterior em vez do débito comum, por segurança e proteção "
                "de compra."},
]


def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {filename}: {len(rows)} registros")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    print("Gerando embeddings das políticas...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Escrevendo arquivos JSONL:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "accounts.jsonl", ACCOUNTS)
    write_jsonl(resolved_output_dir, "cards.jsonl", CARDS)
    write_jsonl(resolved_output_dir, "transactions.jsonl", TRANSACTIONS)
    write_jsonl(resolved_output_dir, "billing_cycles.jsonl", BILLING_CYCLES)
    write_jsonl(resolved_output_dir, "investments.jsonl", INVESTMENTS)
    write_jsonl(resolved_output_dir, "pix_contacts.jsonl", PIX_CONTACTS)
    write_jsonl(resolved_output_dir, "disputes.jsonl", DISPUTES)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["nome"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['nome']} ({demo['customer_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["customer_id"],
            "DEMO_USER_NAME": demo["nome"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "customers": len(CUSTOMERS),
            "accounts": len(ACCOUNTS),
            "cards": len(CARDS),
            "transactions": len(TRANSACTIONS),
            "billing_cycles": len(BILLING_CYCLES),
            "investments": len(INVESTMENTS),
            "pix_contacts": len(PIX_CONTACTS),
            "disputes": len(DISPUTES),
            "feature_store": len(FEATURE_STORE),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
