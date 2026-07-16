"""Itaú Assist — gerador de seed bancário em PT-BR.

Construído pra demo executiva: o caso de uso principal é contestação de
cobrança no cartão de crédito, com padrão recorrente (Amazon Pay LU) que
o agente reconhece via Agent Memory + histórico. Demo secundária: envio
de Pix com confirmação determinística.

Cliente demo é Gabriel Cerioni (Personnalité Nível 5, alta renda, The One + Visa Infinite). Valores
e dados são fictícios mas plausíveis pra contexto SP/Itaú.
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

OUTPUT_DIR = ROOT / "output" / "itau_assist"


def ts(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input=texts, model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in resp.data]


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMERS (5)
# ═══════════════════════════════════════════════════════════════════════════

DEMO_USER_ID = "CUST_DEMO_001"

CUSTOMERS = [
    {
        "customer_id": DEMO_USER_ID,
        "name": "Gabriel Cerioni",
        "cpf_masked": "***.456.789-**",
        "email": "gabriel.cerioni@example.com.br",
        "phone": "+55 11 98765-4321",
        "account_status": "active",
        "tier": "personnalite_nivel_5",
        "relationship_years": 11,
        "city": "São Paulo",
        "default_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP, 05433-010",
        "perfil_investidor": "alta_renda",
        "credit_score": 968,
        "account_created_at": ts(now - timedelta(days=11 * 365)),
    },
    {
        "customer_id": "CUST_002",
        "name": "Janine Marjoub",
        "cpf_masked": "***.123.456-**",
        "email": "janine.marjoub@example.com.br",
        "phone": "+55 11 99123-4567",
        "account_status": "active",
        "tier": "uniclass",
        "relationship_years": 4,
        "city": "São Paulo",
        "default_address": "Av. Brigadeiro Faria Lima, 3200, Itaim Bibi, São Paulo - SP",
        "perfil_investidor": "arrojado",
        "credit_score": 845,
        "account_created_at": ts(now - timedelta(days=4 * 365)),
    },
    {
        "customer_id": "CUST_003",
        "name": "Diego Linke",
        "cpf_masked": "***.987.654-**",
        "email": "diego.linke@example.com.br",
        "phone": "+55 11 98555-0303",
        "account_status": "active",
        "tier": "uniclass",
        "relationship_years": 2,
        "city": "São Paulo",
        "default_address": "Rua Harmonia, 450, Vila Madalena, São Paulo - SP",
        "perfil_investidor": "moderado",
        "credit_score": 798,
        "account_created_at": ts(now - timedelta(days=2 * 365)),
    },
    {
        "customer_id": "CUST_004",
        "name": "Gabriella Candelaria",
        "cpf_masked": "***.234.567-**",
        "email": "gabriella.candelaria@example.com.br",
        "phone": "+55 11 97444-0404",
        "account_status": "active",
        "tier": "private",
        "relationship_years": 12,
        "city": "São Paulo",
        "default_address": "Rua Joaquim Floriano, 800, Itaim Bibi, São Paulo - SP",
        "perfil_investidor": "sofisticado",
        "credit_score": 950,
        "account_created_at": ts(now - timedelta(days=12 * 365)),
    },
    {
        "customer_id": "CUST_005",
        "name": "Miller Moreno",
        "cpf_masked": "***.345.678-**",
        "email": "miller.moreno@example.com.br",
        "phone": "+55 11 96333-0505",
        "account_status": "active",
        "tier": "pf_mass",
        "relationship_years": 1,
        "city": "São Paulo",
        "default_address": "Rua Augusta, 1200, Cerqueira César, São Paulo - SP",
        "perfil_investidor": "conservador",
        "credit_score": 712,
        "account_created_at": ts(now - timedelta(days=400)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  ACCOUNTS — uma conta corrente Personnalité pro Gabriel + 1 conta cada outros
# ═══════════════════════════════════════════════════════════════════════════

ACCOUNTS = [
    # Gabriel — Personnalité
    {
        "account_id": "ACC_001", "customer_id": DEMO_USER_ID,
        "agencia": "3057", "conta_numero": "12345-6", "tipo": "corrente",
        "saldo_disponivel": 28450.00, "saldo_aplicado": 187000.00,
        "limite_cheque_especial": 15000.00, "status": "active",
    },
    {
        "account_id": "ACC_002", "customer_id": "CUST_002",
        "agencia": "0911", "conta_numero": "98765-4", "tipo": "corrente",
        "saldo_disponivel": 12340.00, "saldo_aplicado": 45000.00,
        "limite_cheque_especial": 8000.00, "status": "active",
    },
    {
        "account_id": "ACC_003", "customer_id": "CUST_003",
        "agencia": "1582", "conta_numero": "23456-7", "tipo": "corrente",
        "saldo_disponivel": 4520.00, "saldo_aplicado": 0.00,
        "limite_cheque_especial": 3000.00, "status": "active",
    },
    {
        "account_id": "ACC_004", "customer_id": "CUST_004",
        "agencia": "0067", "conta_numero": "34567-8", "tipo": "corrente",
        "saldo_disponivel": 145000.00, "saldo_aplicado": 2800000.00,
        "limite_cheque_especial": 100000.00, "status": "active",
    },
    {
        "account_id": "ACC_005", "customer_id": "CUST_005",
        "agencia": "2389", "conta_numero": "45678-9", "tipo": "corrente",
        "saldo_disponivel": 1850.00, "saldo_aplicado": 0.00,
        "limite_cheque_especial": 1000.00, "status": "active",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  CARDS — 3 cartões pro Gabriel + 1-2 cada outros
# ═══════════════════════════════════════════════════════════════════════════

CARDS = [
    # Gabriel — Itaú Personnalité The One (top tier, alta renda)
    {
        "card_id": "CARD_001", "customer_id": DEMO_USER_ID, "account_id": "ACC_001",
        "bandeira": "mastercard", "produto": "the_one",
        "numero_mascarado": "****4242",
        "limite_total": 500000.00, "limite_usado": 12450.00, "limite_disponivel": 487550.00,
        "validade": "08/29", "status": "active",
    },
    # Gabriel — Itaucard Click (cartão de gastos do dia a dia)
    {
        "card_id": "CARD_002", "customer_id": DEMO_USER_ID, "account_id": "ACC_001",
        "bandeira": "visa", "produto": "click",
        "numero_mascarado": "****8123",
        "limite_total": 15000.00, "limite_usado": 2340.00, "limite_disponivel": 12660.00,
        "validade": "11/28", "status": "active",
    },
    # Gabriel — Personnalité Visa Infinite (cartão de viagem)
    {
        "card_id": "CARD_003", "customer_id": DEMO_USER_ID, "account_id": "ACC_001",
        "bandeira": "visa", "produto": "visa_infinite",
        "numero_mascarado": "****5511",
        "limite_total": 50000.00, "limite_usado": 0.00, "limite_disponivel": 50000.00,
        "validade": "03/30", "status": "active",
    },
    # Janine
    {
        "card_id": "CARD_004", "customer_id": "CUST_002", "account_id": "ACC_002",
        "bandeira": "mastercard", "produto": "uniclass",
        "numero_mascarado": "****1098",
        "limite_total": 25000.00, "limite_usado": 8900.00, "limite_disponivel": 16100.00,
        "validade": "06/28", "status": "active",
    },
    # Diego
    {
        "card_id": "CARD_005", "customer_id": "CUST_003", "account_id": "ACC_003",
        "bandeira": "visa", "produto": "click",
        "numero_mascarado": "****7766",
        "limite_total": 8000.00, "limite_usado": 3450.00, "limite_disponivel": 4550.00,
        "validade": "09/27", "status": "active",
    },
    # Gabriella — Private (Visa Infinite)
    {
        "card_id": "CARD_006", "customer_id": "CUST_004", "account_id": "ACC_004",
        "bandeira": "visa", "produto": "visa_infinite",
        "numero_mascarado": "****0001",
        "limite_total": 250000.00, "limite_usado": 18700.00, "limite_disponivel": 231300.00,
        "validade": "01/30", "status": "active",
    },
    # Miller
    {
        "card_id": "CARD_007", "customer_id": "CUST_005", "account_id": "ACC_005",
        "bandeira": "mastercard", "produto": "itaucard",
        "numero_mascarado": "****3344",
        "limite_total": 3500.00, "limite_usado": 1200.00, "limite_disponivel": 2300.00,
        "validade": "12/27", "status": "active",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  BILLING CYCLES — 2 ciclos pro Itaú The One (aberto + fechado)
# ═══════════════════════════════════════════════════════════════════════════

# Ciclo atual (aberto)
cycle_current_close = (now + timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0)
cycle_current_due = (now + timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0)

# Ciclo anterior (pago)
cycle_prev_close = (now - timedelta(days=25)).replace(hour=0, minute=0, second=0, microsecond=0)
cycle_prev_due = (now - timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0)

BILLING_CYCLES = [
    {
        "cycle_id": "BILL_001", "card_id": "CARD_001", "customer_id": DEMO_USER_ID,
        "mes_referencia": cycle_current_close.strftime("%Y-%m"),
        "data_fechamento": ts(cycle_current_close),
        "data_vencimento": ts(cycle_current_due),
        "valor_total": 12450.00, "pagamento_minimo": 1867.50, "valor_pago": 0.00,
        "status": "aberta",
    },
    {
        "cycle_id": "BILL_002", "card_id": "CARD_001", "customer_id": DEMO_USER_ID,
        "mes_referencia": cycle_prev_close.strftime("%Y-%m"),
        "data_fechamento": ts(cycle_prev_close),
        "data_vencimento": ts(cycle_prev_due),
        "valor_total": 9870.45, "pagamento_minimo": 1480.57, "valor_pago": 9870.45,
        "status": "paga",
    },
    {
        "cycle_id": "BILL_003", "card_id": "CARD_002", "customer_id": DEMO_USER_ID,
        "mes_referencia": cycle_current_close.strftime("%Y-%m"),
        "data_fechamento": ts(cycle_current_close),
        "data_vencimento": ts(cycle_current_due),
        "valor_total": 2340.00, "pagamento_minimo": 351.00, "valor_pago": 0.00,
        "status": "aberta",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS — núcleo da demo. ~30 transações, incluindo o padrão
#  AMAZON PAY LU recorrente que é o gatilho do caso principal.
# ═══════════════════════════════════════════════════════════════════════════

# Helper: gera data dentro do ciclo atual (entre cycle_prev_close e agora)
def in_current_cycle(days_back: int) -> datetime:
    return now - timedelta(days=days_back)


# Helper: gera data em ciclo passado específico (meses atrás)
def months_ago(months: int, day_of_month: int = 12) -> datetime:
    base = now.replace(day=min(day_of_month, 28))
    for _ in range(months):
        base = (base.replace(day=1) - timedelta(days=1)).replace(day=min(day_of_month, 28))
    return base


TRANSACTIONS = [
    # ─── AMAZON PAY LU — padrão recorrente CRÍTICO PRA DEMO ──────
    # 4 ocorrências: agora (ciclo atual), 3 meses atrás, 6 meses atrás, 9 meses atrás
    {
        "transaction_id": "TXN_001", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "AMAZON PAY LU", "mcc": "5968",
        "valor": 432.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(3)), "data_lancamento": ts(in_current_cycle(2)),
        "is_recurring": "sim",
        "recurring_label": "Amazon Prime + Music Family (anual rateado mensal)",
        "location_city": "Luxembourg", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_002", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "AMAZON PAY LU", "mcc": "5968",
        "valor": 432.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(months_ago(3)), "data_lancamento": ts(months_ago(3) + timedelta(days=1)),
        "is_recurring": "sim",
        "recurring_label": "Amazon Prime + Music Family (anual rateado mensal)",
        "location_city": "Luxembourg", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_003", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "AMAZON PAY LU", "mcc": "5968",
        "valor": 432.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(months_ago(6)), "data_lancamento": ts(months_ago(6) + timedelta(days=1)),
        "is_recurring": "sim",
        "recurring_label": "Amazon Prime + Music Family (anual rateado mensal)",
        "location_city": "Luxembourg", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_004", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "AMAZON PAY LU", "mcc": "5968",
        "valor": 432.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(months_ago(9)), "data_lancamento": ts(months_ago(9) + timedelta(days=1)),
        "is_recurring": "sim",
        "recurring_label": "Amazon Prime + Music Family (anual rateado mensal)",
        "location_city": "Luxembourg", "dispute_id": None,
    },

    # ─── Transações do dia a dia no ciclo atual (Itaú The One) ───
    {
        "transaction_id": "TXN_010", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "NETFLIX.COM", "mcc": "4899",
        "valor": 55.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(8)), "data_lancamento": ts(in_current_cycle(7)),
        "is_recurring": "sim", "recurring_label": "Netflix mensal",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_011", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "SPOTIFY BR", "mcc": "4899",
        "valor": 32.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(6)), "data_lancamento": ts(in_current_cycle(5)),
        "is_recurring": "sim", "recurring_label": "Spotify Family",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_012", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "UBER *TRIP", "mcc": "4121",
        "valor": 47.30, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(5)), "data_lancamento": ts(in_current_cycle(4)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_013", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "RESTAURANTE FASANO", "mcc": "5812",
        "valor": 624.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(4)), "data_lancamento": ts(in_current_cycle(3)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_014", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "POSTO SHELL FARIA LIMA", "mcc": "5541",
        "valor": 312.40, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(3)), "data_lancamento": ts(in_current_cycle(2)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_015", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "RENNER PINHEIROS", "mcc": "5651",
        "valor": 489.90, "parcelas_total": 3, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(10)), "data_lancamento": ts(in_current_cycle(9)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_016", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "PADARIA CASA DO PAO", "mcc": "5462",
        "valor": 86.40, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(2)), "data_lancamento": ts(in_current_cycle(1)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_017", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "DROGARIA SAO PAULO", "mcc": "5912",
        "valor": 134.70, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(1)), "data_lancamento": ts(in_current_cycle(1)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_019A", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "BISTRO CHARLO JARDINS", "mcc": "5812",
        "valor": 287.40, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(7)), "data_lancamento": ts(in_current_cycle(6)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_019B", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "OUTBACK MORUMBI", "mcc": "5812",
        "valor": 198.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(12)), "data_lancamento": ts(in_current_cycle(11)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_019C", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_002", "account_id": None, "billing_cycle_id": "BILL_003",
        "tipo": "compra_credito",
        "merchant": "PADARIA TIA JANE", "mcc": "5462",
        "valor": 58.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(0)), "data_lancamento": ts(in_current_cycle(0)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    # ─── Compras parceladas no The One (caso de uso "parcelados na fatura") ───
    {
        "transaction_id": "TXN_PARC_001", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "APPLE STORE IGUATEMI SP", "mcc": "5732",
        "valor": 1083.25, "parcelas_total": 12, "parcela_atual": 2,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(40)), "data_lancamento": ts(in_current_cycle(15)),
        "is_recurring": "nao", "recurring_label": "iPhone 15 Pro Max em 12x",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_PARC_002", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "CVC ITAIM VIAGENS", "mcc": "4722",
        "valor": 1450.00, "parcelas_total": 10, "parcela_atual": 3,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(70)), "data_lancamento": ts(in_current_cycle(15)),
        "is_recurring": "nao", "recurring_label": "Pacote Disney Family em 10x",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_PARC_003", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "H STERN JARDINS", "mcc": "5944",
        "valor": 720.00, "parcelas_total": 6, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(5)), "data_lancamento": ts(in_current_cycle(4)),
        "is_recurring": "nao", "recurring_label": "Pulseira de ouro 6x",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_018", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "anuidade",
        "merchant": "ITAU ANUIDADE THE ONE", "mcc": None,
        "valor": 5040.00, "parcelas_total": 12, "parcela_atual": 4,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(15)), "data_lancamento": ts(in_current_cycle(15)),
        "is_recurring": "sim", "recurring_label": "Anuidade Itaú The One parcelada em 12x",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Compras no Itaucard Click (cartão day-to-day) ───
    {
        "transaction_id": "TXN_020", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_002", "account_id": None, "billing_cycle_id": "BILL_003",
        "tipo": "compra_credito",
        "merchant": "IFOOD*ALMOCO", "mcc": "5814",
        "valor": 42.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(2)), "data_lancamento": ts(in_current_cycle(1)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_021", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_002", "account_id": None, "billing_cycle_id": "BILL_003",
        "tipo": "compra_credito",
        "merchant": "GLOBOPLAY", "mcc": "4899",
        "valor": 49.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(9)), "data_lancamento": ts(in_current_cycle(8)),
        "is_recurring": "sim", "recurring_label": "Globoplay mensal",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_022", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_002", "account_id": None, "billing_cycle_id": "BILL_003",
        "tipo": "compra_credito",
        "merchant": "STARBUCKS FARIA LIMA", "mcc": "5814",
        "valor": 28.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(4)), "data_lancamento": ts(in_current_cycle(3)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Pix outgoing (conta corrente) ───
    {
        "transaction_id": "TXN_030", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Tia Eulália Cerioni", "mcc": "PIX",
        "valor": 800.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(7)), "data_lancamento": ts(in_current_cycle(7)),
        "is_recurring": "sim", "recurring_label": "Mesada Tia Eulália",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_031", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Carlos Eduardo Souza", "mcc": "PIX",
        "valor": 120.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(11)), "data_lancamento": ts(in_current_cycle(11)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_032", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_recebido",
        "merchant": "PIX < Mariana Schmidt (rateio almoço)", "mcc": "PIX",
        "valor": -85.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(4)), "data_lancamento": ts(in_current_cycle(4)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_033", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Filha (PUC mensalidade)", "mcc": "PIX",
        "valor": 1500.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(6)), "data_lancamento": ts(in_current_cycle(6)),
        "is_recurring": "sim", "recurring_label": "Mensalidade PUC (dia 5)",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Transações de outros clientes (pra dataset ter densidade) ───
    {
        "transaction_id": "TXN_050", "customer_id": "CUST_002",
        "card_id": "CARD_004", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "AMERICAN AIRLINES", "mcc": "3001",
        "valor": 4890.00, "parcelas_total": 6, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(8)), "data_lancamento": ts(in_current_cycle(7)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "Dallas", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_051", "customer_id": "CUST_003",
        "card_id": "CARD_005", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "DROGARIA RAIA", "mcc": "5912",
        "valor": 67.40, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(2)), "data_lancamento": ts(in_current_cycle(1)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_052", "customer_id": "CUST_004",
        "card_id": "CARD_006", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "HOTEL FASANO BOUTIQUE", "mcc": "7011",
        "valor": 18700.00, "parcelas_total": 3, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(in_current_cycle(5)), "data_lancamento": ts(in_current_cycle(4)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "Miami", "dispute_id": None,
    },
    # iFood duplicada do Miller (vai ser referenciada por DSP_003)
    {
        "transaction_id": "TXN_053", "customer_id": "CUST_005",
        "card_id": "CARD_007", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "IFOOD*JANTAR", "mcc": "5814",
        "valor": 89.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "estornada",
        "data_compra": ts(in_current_cycle(20)), "data_lancamento": ts(in_current_cycle(19)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": "DSP_003",
    },

    # ─── Uma transação contestada (histórica, do Gabriel) ───
    {
        "transaction_id": "TXN_060", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "WISH.COM", "mcc": "5969",
        "valor": 234.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "estornada",
        "data_compra": ts(months_ago(2)), "data_lancamento": ts(months_ago(2) + timedelta(days=1)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "Hong Kong", "dispute_id": "DSP_001",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES (3) — uma resolvida do Gabriel + 2 de outros
# ═══════════════════════════════════════════════════════════════════════════

DISPUTES = [
    {
        "dispute_id": "DSP_001", "customer_id": DEMO_USER_ID,
        "transaction_id": "TXN_060",
        "protocolo": "DSP20260315-XYZ123",
        "motivo": "nao_reconheco",
        "status": "resolvida_favoravel",
        "valor_contestado": 234.50,
        "data_abertura": ts(months_ago(2) + timedelta(days=3)),
        "data_resolucao": ts(months_ago(2) + timedelta(days=8)),
        "descricao": "Não reconheço essa compra na Wish.com. Nunca usei esse site.",
        "resolucao": "Estorno integral aprovado em favor do cliente. Charge revertido no ciclo seguinte.",
    },
    {
        "dispute_id": "DSP_002", "customer_id": "CUST_003",
        "transaction_id": "TXN_051",
        "protocolo": "DSP20260520-ABC456",
        "motivo": "valor_divergente",
        "status": "em_analise",
        "valor_contestado": 67.40,
        "data_abertura": ts(in_current_cycle(2)),
        "data_resolucao": None,
        "descricao": "Cobraram R$ 67,40 mas comprei apenas R$ 47,40. Tenho a nota.",
        "resolucao": None,
    },
    {
        "dispute_id": "DSP_003", "customer_id": "CUST_005",
        "transaction_id": "TXN_053",
        "protocolo": "DSP20260418-DEF789",
        "motivo": "duplicada",
        "status": "resolvida_favoravel",
        "valor_contestado": 89.00,
        "data_abertura": ts(in_current_cycle(20)),
        "data_resolucao": ts(in_current_cycle(15)),
        "descricao": "Charge duplicado da iFood no mesmo dia.",
        "resolucao": "Cobrança duplicada confirmada. Valor estornado.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PIX CONTACTS — contatos frequentes do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

PIX_CONTACTS = [
    {
        "contact_id": "PIX_001", "customer_id": DEMO_USER_ID,
        "recipient_name": "Carlos Eduardo Souza",
        "chave_pix": "+5511953332002",
        "chave_tipo": "celular",
        "banco_destino": "Itaú Unibanco",
        "frequencia_uso": 12,
        "ultimo_uso": ts(in_current_cycle(11)),
    },
    {
        "contact_id": "PIX_002", "customer_id": DEMO_USER_ID,
        "recipient_name": "Tia Eulália Cerioni",
        "chave_pix": "eulalia.cerioni@email.com",
        "chave_tipo": "email",
        "banco_destino": "Bradesco",
        "frequencia_uso": 28,
        "ultimo_uso": ts(in_current_cycle(7)),
    },
    {
        "contact_id": "PIX_003", "customer_id": DEMO_USER_ID,
        "recipient_name": "Mariana Schmidt",
        "chave_pix": "***456789**",
        "chave_tipo": "cpf",
        "banco_destino": "Nubank",
        "frequencia_uso": 8,
        "ultimo_uso": ts(in_current_cycle(4)),
    },
    {
        "contact_id": "PIX_004", "customer_id": DEMO_USER_ID,
        "recipient_name": "Filha (Sofia Cerioni)",
        "chave_pix": "sofia.cerioni@example.com.br",
        "chave_tipo": "email",
        "banco_destino": "Itaú Unibanco",
        "frequencia_uso": 14,
        "ultimo_uso": ts(in_current_cycle(6)),
    },
    {
        "contact_id": "PIX_005", "customer_id": DEMO_USER_ID,
        "recipient_name": "Diego Linke",
        "chave_pix": "+5511985550303",
        "chave_tipo": "celular",
        "banco_destino": "Itaú Unibanco",
        "frequencia_uso": 3,
        "ultimo_uso": ts(in_current_cycle(45)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  REWARDS — programa Sempre Presente do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

REWARDS_ACCOUNTS = [
    {
        "rewards_id": "RWD_001", "customer_id": DEMO_USER_ID,
        "programa": "sempre_presente", "saldo_pontos": 187420,
        "pontos_a_vencer": 4500,
        "data_vencimento_proxima": ts(now + timedelta(days=78)),
        "categoria_top": "alimentacao_restaurante",
    },
    {
        "rewards_id": "RWD_002", "customer_id": "CUST_002",
        "programa": "atomos", "saldo_pontos": 42300,
        "pontos_a_vencer": 1200,
        "data_vencimento_proxima": ts(now + timedelta(days=140)),
        "categoria_top": "viagem",
    },
    {
        "rewards_id": "RWD_003", "customer_id": "CUST_004",
        "programa": "latam_pass", "saldo_pontos": 891000,
        "pontos_a_vencer": 12000,
        "data_vencimento_proxima": ts(now + timedelta(days=45)),
        "categoria_top": "viagem",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS — histórico de atendimentos do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

SUPPORT_TICKETS = [
    {
        "ticket_id": "TKT_001", "customer_id": DEMO_USER_ID,
        "categoria": "contestacao", "status": "resolvido",
        "data_abertura": ts(months_ago(2) + timedelta(days=3)),
        "data_resolucao": ts(months_ago(2) + timedelta(days=8)),
        "resumo": "Contestação Wish.com R$ 234,50, não reconheci a compra.",
        "resolucao": "Contestação procedente, valor estornado em ciclo seguinte (DSP20260315-XYZ123).",
    },
    {
        "ticket_id": "TKT_002", "customer_id": DEMO_USER_ID,
        "categoria": "limite", "status": "em_andamento",
        "data_abertura": ts(in_current_cycle(40)),
        "data_resolucao": None,
        "resumo": "Cliente solicitou aumento de limite no Itaú The One de R$ 500.000 pra R$ 800.000 (planejamento de aquisição imobiliária).",
        "resolucao": None,
    },
    {
        "ticket_id": "TKT_003", "customer_id": DEMO_USER_ID,
        "categoria": "pix", "status": "resolvido",
        "data_abertura": ts(months_ago(3) + timedelta(days=10)),
        "data_resolucao": ts(months_ago(3) + timedelta(days=10, hours=2)),
        "resumo": "Cliente reclamou de notificação push duplicada de Pix em 2 cartões.",
        "resolucao": "Ajustada preferência pra SMS em alertas críticos. Confirmado pelo cliente.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — políticas Itaú em PT-BR
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "Política de Contestação de Cobranças", "category": "contestacao",
        "content": (
            "O cliente pode contestar qualquer lançamento na fatura do cartão de crédito em até "
            "120 dias após o vencimento da fatura. A contestação gera um protocolo formal e a "
            "análise é feita em até 7 dias úteis. Em casos claros de fraude (cartão não presente, "
            "compra fora do perfil), o estorno provisório pode ser aplicado em 48h. Para cobranças "
            "que apresentam padrão recorrente identificável (mesmo merchant, mesmo valor, "
            "frequência regular), o sistema sugere ao cliente verificar antes de contestar, "
            "pois contestações em transações reconhecidas pelo histórico costumam ser revertidas "
            "como improcedentes."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Política de Aumento de Limite", "category": "limite",
        "content": (
            "Aumento de limite pode ser solicitado pelo app, gerente Personnalité ou central. "
            "A análise considera score interno, comportamento de pagamento dos últimos 12 ciclos, "
            "renda comprovada e relacionamento com o banco. Clientes Personnalité e Private com "
            "score acima de 850 e histórico de pagamento impecável têm aprovação prioritária. "
            "O aumento, quando aprovado, é aplicado em até 2 ciclos."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Política de Anuidade: Itaú The One e Cartões Premium", "category": "fatura",
        "content": (
            "Itaú The One: anuidade de R$ 5.040,00 ao ano, parcelada em 12x sem juros (R$ 420,00/mês). "
            "Inclui concierge 24h dedicado, acesso ilimitado a lounges em todo o mundo (LoungeKey + "
            "Priority Pass), seguro viagem premium global, e cobertura adicional pra compras internacionais. "
            "Personnalité Visa Infinite: anuidade R$ 1.450,00/ano parcelada em 12x; mesmas vantagens "
            "de lounge e seguro com menor abrangência. Clientes Personnalité Nível 4 e 5 com gasto "
            "anual acima de R$ 200.000 podem solicitar isenção parcial via gerente. Clientes Private "
            "Banking têm isenção integral de anuidade em ambos os cartões."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Política Pix: Limites e Segurança", "category": "pix",
        "content": (
            "Pix Itaú: limite diurno padrão de R$ 5.000 por transação (6h às 20h) e noturno de "
            "R$ 1.000 (20h às 6h), ajustáveis no app. Clientes Personnalité podem solicitar limites "
            "estendidos via gerente. Pix entre contas Itaú é instantâneo; para outros bancos, o "
            "tempo médio é de 10 segundos. Todo Pix gera comprovante e protocolo no formato "
            "PIXAAAAMMDD-XXXXXX. Pix superiores a R$ 1.000 fora do horário habitual do cliente "
            "podem disparar verificação adicional anti-fraude."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Programa Sempre Presente", "category": "pontos",
        "content": (
            "Sempre Presente: 1 ponto a cada R$ 1 gasto no cartão de crédito (multiplicadores "
            "específicos para Personnalité Black: 1,5x em restaurantes, 2x em viagens). Pontos "
            "têm validade de 24 meses a partir do acúmulo. O cliente pode trocar por milhas LATAM, "
            "produtos do shopping de pontos, ou crédito na fatura (R$ 0,02 por ponto). Pontos a "
            "vencer aparecem com 90 dias de antecedência."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Política de Segurança e Fraude", "category": "seguranca",
        "content": (
            "Todas as transações são monitoradas em tempo real por modelo anti-fraude. Compras "
            "fora do perfil habitual (valor, localização, merchant, horário) disparam verificação "
            "via push ou SMS. Em casos de bloqueio preventivo, o cartão é desbloqueado após "
            "confirmação pelo cliente. Cartão clonado é substituído sem custo em até 5 dias úteis "
            "para Personnalité e Private (até 10 dias úteis para demais segmentos)."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Política de Cheque Especial", "category": "conta",
        "content": (
            "O limite de cheque especial é definido conforme score, tempo de conta e movimentação. "
            "Juros do cheque especial são contratados na adesão e seguem regulação do BACEN "
            "(teto vigente). Para clientes Personnalité e Private, há produtos alternativos com "
            "taxa reduzida (LIS Itaú Personnalité). Recomenda-se uso pontual; valores superiores "
            "a 30% do limite por mais de 7 dias disparam alerta no app."
        ),
    },
    {
        "policy_id": "POL_008", "title": "Parcelamento de Fatura", "category": "fatura",
        "content": (
            "O cliente pode parcelar a fatura do cartão em até 24x diretamente pelo app ou central. "
            "Os juros do parcelamento dependem do segmento e do score. Clientes Personnalité têm "
            "acesso a parcelamentos promocionais ao longo do ano (taxa zero em campanhas pontuais). "
            "Para parcelamentos acima de 12x recomenda-se análise com gerente."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Cancelamento de Cartão", "category": "conta",
        "content": (
            "Cancelamento de cartão pode ser solicitado a qualquer momento via app, gerente ou "
            "central. Caso haja saldo devedor, será gerado boleto único para quitação. Pontos "
            "do programa Sempre Presente acumulados ficam disponíveis por mais 60 dias após o "
            "cancelamento. Clientes Personnalité e Private contam com atendimento dedicado para "
            "esse processo."
        ),
    },
    {
        "policy_id": "POL_010", "title": "Cobrança Recorrente em Cartão", "category": "contestacao",
        "content": (
            "Cobranças recorrentes (streaming, assinaturas, software, serviços internacionais) "
            "aparecem na fatura com o nome do prestador internacional (ex: AMAZON PAY LU, "
            "GOOGLE *YOUTUBEPREMIUM, APPLE.COM/BILL, NETFLIX.COM). O Itaú mantém histórico de "
            "padrões recorrentes do cliente e o sistema alerta quando uma cobrança aparenta ser "
            "estranha ou fora do padrão. Cobranças recorrentes legítimas são reconhecidas pela "
            "frequência, valor estável e merchant repetido. Cancelar uma assinatura é "
            "responsabilidade do cliente diretamente com o prestador; o Itaú não tem autonomia "
            "para cancelar charges futuros, apenas estornar lançamentos passados quando aplicável."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — gera embeddings + escreve JSONLs
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} registros")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={safe_value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE (1) — features online do Gabriel, lidas em tempo real pela IARA
#  no modelo de next-best-action. Propensões calibradas pros 2 heróis do flagship:
#  migração CDB->LCI (propensao_investimento + aplicado_cdb alto) e cartão co-branded
#  Palmeiras via cartão branco (propensao_cobranded_clube alta + time_do_coracao).
# ═══════════════════════════════════════════════════════════════════════════

FEATURE_STORE = [
    {
        "customer_id": DEMO_USER_ID,
        "renda_mensal": 95000.00,
        "score_interno": 968,
        "aplicado_cdb": 187000.00,
        "saldo_medio_3m": 64000.00,
        "tenure_meses": 132,
        "num_produtos": 4,
        "propensao_investimento": 0.86,
        "propensao_upgrade_cartao": 0.72,
        "propensao_cobranded_clube": 0.90,
        "propensao_seguro": 0.45,
        "time_do_coracao": "Palmeiras",
        "perfil_digital": "alto",
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]


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
    write_jsonl(resolved_output_dir, "disputes.jsonl", DISPUTES)
    write_jsonl(resolved_output_dir, "pix_contacts.jsonl", PIX_CONTACTS)
    write_jsonl(resolved_output_dir, "rewards_accounts.jsonl", REWARDS_ACCOUNTS)
    write_jsonl(resolved_output_dir, "support_tickets.jsonl", SUPPORT_TICKETS)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['name']} ({demo['customer_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["customer_id"],
            "DEMO_USER_NAME": demo["name"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "customers": len(CUSTOMERS),
            "accounts": len(ACCOUNTS),
            "cards": len(CARDS),
            "transactions": len(TRANSACTIONS),
            "billing_cycles": len(BILLING_CYCLES),
            "disputes": len(DISPUTES),
            "pix_contacts": len(PIX_CONTACTS),
            "rewards_accounts": len(REWARDS_ACCOUNTS),
            "support_tickets": len(SUPPORT_TICKETS),
            "feature_store": len(FEATURE_STORE),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
