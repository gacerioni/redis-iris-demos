"""Leet Bank: synthetic banking seed in PT-BR.

Built for the Febraban Tech 2026 executive demo ("Agentes Inteligentes,
lideranca humana"). Flagship journeys for the MarIAm assistant:
  1. Pix scam interception: a Pix request to the unknown key "11 91234-0666"
     (present NOWHERE in this dataset, by design) triggers the anti-scam flow
     backed by the online feature store and the Pix security policy.
  2. Pix Automatico enrollment: the rent (R$ 2.800,00, day 5, Imobiliaria
     Horizonte) is paid manually today and is the candidate to enroll; the
     PUC tuition is the pre-existing example already enrolled.
  3. Smart dispute pushback: "CLOUD DEV PRO" R$ 89,90 recurs on day 12 since
     2024, so a dispute attempt gets a smart is_recurring contestation.
  4. Credito Flash: pre-approved R$ 100.000,00 at 1,337% a.m. with the CDB
     (R$ 133.700,00 at 103,37% of CDI) as tokenized collateral.

Demo customer is Gabriel Cerioni (segment Elite 1337, client since 2016-03,
dev/platform engineer in Sao Paulo). Several figures are intentional leet
easter eggs (31337, 1337, 7331, 133700, 1.337). All data is fictitious;
Leet Bank is not a real institution.

Fixed demo anchor: the storyline is pinned to July 2026 (canonical dates such
as the 2026-07-28 due date and the day-5/day-12 recurrences are part of the
demo script), so the generator uses a fixed "today" instead of datetime.now()
and stays fully deterministic across runs.
"""

from __future__ import annotations

import json
import os
import sys
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "leet_bank"

# Pinned "today" for full determinism (see module docstring).
now = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)

# The scam Pix key used live in the demo. It must NOT exist anywhere in the
# seed: the whole anti-scam journey depends on it being an unknown key.
SCAM_KEY_FRAGMENT = "91234-0666"


def ts(dt: datetime) -> str:
    return dt.isoformat()


def d(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> datetime:
    """Deterministic UTC timestamp helper for the pinned July 2026 storyline."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


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
#  CUSTOMERS (3) — demo customer + 2 fillers for realism
# ═══════════════════════════════════════════════════════════════════════════

DEMO_USER_ID = "CUST_DEMO_001"

CUSTOMERS = [
    {
        "customer_id": DEMO_USER_ID,
        "name": "Gabriel Cerioni",
        "cpf_masked": "***.456.789-**",
        "email": "gabs@leetbank.com.br",
        "phone_masked": "+55 11 9****-1337",
        "account_status": "active",
        "segmento": "elite_1337",
        "cliente_desde": "2016-03",
        "city": "São Paulo",
        "profissao": "Engenheiro de plataforma (dev)",
        "default_address": "Rua dos Pinheiros, 1024, apto 42, Pinheiros, São Paulo - SP",
    },
    {
        "customer_id": "CUST_002",
        "name": "Larissa Mota",
        "cpf_masked": "***.321.654-**",
        "email": "larissa.mota@example.com.br",
        "phone_masked": "+55 11 9****-2044",
        "account_status": "active",
        "segmento": "dev_pro",
        "cliente_desde": "2021-09",
        "city": "São Paulo",
        "profissao": "Desenvolvedora backend",
        "default_address": "Av. Paulista, 900, Bela Vista, São Paulo - SP",
    },
    {
        "customer_id": "CUST_003",
        "name": "Renan Alves",
        "cpf_masked": "***.789.123-**",
        "email": "renan.alves@example.com.br",
        "phone_masked": "+55 19 9****-8810",
        "account_status": "active",
        "segmento": "starter",
        "cliente_desde": "2024-01",
        "city": "Campinas",
        "profissao": "Estudante de computação",
        "default_address": "Rua Barão de Jaguara, 500, Centro, Campinas - SP",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  ACCOUNTS — one checking account per customer (Gabriel carries the CDB)
# ═══════════════════════════════════════════════════════════════════════════

ACCOUNTS = [
    # Gabriel: saldo 31.337,00 + CDB 133.700,00 a 103,37% do CDI (leet numbers)
    {
        "account_id": "ACC_001", "customer_id": DEMO_USER_ID,
        "agencia": "0101", "conta_masked": "***1337", "tipo": "corrente",
        "saldo_disponivel": 31337.00,
        "saldo_cdb": 133700.00, "cdb_rendimento_cdi_pct": 103.37, "cdb_liquidez": "diaria",
        "cheque_especial_limite": 10000.00, "status": "active",
    },
    {
        "account_id": "ACC_002", "customer_id": "CUST_002",
        "agencia": "0101", "conta_masked": "***2044", "tipo": "corrente",
        "saldo_disponivel": 8420.00,
        "saldo_cdb": 25000.00, "cdb_rendimento_cdi_pct": 100.50, "cdb_liquidez": "diaria",
        "cheque_especial_limite": 3000.00, "status": "active",
    },
    {
        "account_id": "ACC_003", "customer_id": "CUST_003",
        "agencia": "0101", "conta_masked": "***8810", "tipo": "corrente",
        "saldo_disponivel": 1930.00,
        "saldo_cdb": 0.00, "cdb_rendimento_cdi_pct": 0.00, "cdb_liquidez": None,
        "cheque_especial_limite": 500.00, "status": "active",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  CARDS — Gabriel's Leet Black (final 1337) + Leet Virtual (final 4242)
# ═══════════════════════════════════════════════════════════════════════════

CARDS = [
    # Leet Black: limite 61.337,00 / fatura aberta 7.331,00 (~12% de uso)
    {
        "card_id": "CARD_001", "customer_id": DEMO_USER_ID, "account_id": "ACC_001",
        "bandeira": "mastercard", "produto": "leet_black",
        "numero_mascarado": "****1337",
        "limite_total": 61337.00, "limite_usado": 7331.00, "limite_disponivel": 54006.00,
        "fatura_aberta": 7331.00, "fatura_vencimento": "2026-07-28",
        "utilizacao_pct": 12.0,
        "validade": "07/31", "status": "active",
    },
    # Leet Virtual: virtual card for online subscriptions and one-off purchases
    {
        "card_id": "CARD_002", "customer_id": DEMO_USER_ID, "account_id": "ACC_001",
        "bandeira": "visa", "produto": "leet_virtual",
        "numero_mascarado": "****4242",
        "limite_total": 5000.00, "limite_usado": 0.00, "limite_disponivel": 5000.00,
        "fatura_aberta": 0.00, "fatura_vencimento": "2026-07-28",
        "utilizacao_pct": 0.0,
        "validade": "12/27", "status": "active",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  BILLING CYCLES — 2 cycles for the Leet Black (open + previous paid)
#  Cycle window: statements close on day 21 and are due on day 28.
# ═══════════════════════════════════════════════════════════════════════════

BILLING_CYCLES = [
    {
        "cycle_id": "BILL_001", "card_id": "CARD_001", "customer_id": DEMO_USER_ID,
        "mes_referencia": "2026-07",
        "data_fechamento": ts(d(2026, 7, 21, 0, 0)),
        "data_vencimento": ts(d(2026, 7, 28, 0, 0)),
        "valor_total": 7331.00, "pagamento_minimo": 1099.65, "valor_pago": 0.00,
        "status": "aberta",
    },
    {
        "cycle_id": "BILL_002", "card_id": "CARD_001", "customer_id": DEMO_USER_ID,
        "mes_referencia": "2026-06",
        "data_fechamento": ts(d(2026, 6, 21, 0, 0)),
        "data_vencimento": ts(d(2026, 6, 28, 0, 0)),
        "valor_total": 1670.00, "pagamento_minimo": 250.50, "valor_pago": 1670.00,
        "status": "paga",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS — core of the demo (~45 rows for Gabriel).
#  Invariants (asserted at generation time):
#    * BILL_001 card lines sum to exactly 7331.00
#    * BILL_002 card lines sum to exactly 1670.00
#    * CLOUD DEV PRO recurs on day 12 (May/Jun/Jul 2026), is_recurring="sim"
#    * no Pix sent in the last 90 days exceeds R$ 1.500,00
#    * the scam key fragment appears nowhere
# ═══════════════════════════════════════════════════════════════════════════

TRANSACTIONS = [
    # ─── CLOUD DEV PRO: recurring pattern that anchors the smart dispute ───
    {
        "transaction_id": "TXN_001", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "CLOUD DEV PRO", "mcc": "5734",
        "valor": 89.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 12)), "data_lancamento": ts(d(2026, 7, 13)),
        "is_recurring": "sim",
        "recurring_label": "Assinatura CLOUD DEV PRO (IDE na nuvem), todo dia 12, ativa desde 2024",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_002", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "CLOUD DEV PRO", "mcc": "5734",
        "valor": 89.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 12)), "data_lancamento": ts(d(2026, 6, 13)),
        "is_recurring": "sim",
        "recurring_label": "Assinatura CLOUD DEV PRO (IDE na nuvem), todo dia 12, ativa desde 2024",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_003", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "CLOUD DEV PRO", "mcc": "5734",
        "valor": 89.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 12)), "data_lancamento": ts(d(2026, 5, 13)),
        "is_recurring": "sim",
        "recurring_label": "Assinatura CLOUD DEV PRO (IDE na nuvem), todo dia 12, ativa desde 2024",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── JETFLIX BR: second recurring subscription (day 10) ───
    {
        "transaction_id": "TXN_010", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "JETFLIX BR", "mcc": "4899",
        "valor": 55.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 10)), "data_lancamento": ts(d(2026, 7, 11)),
        "is_recurring": "sim", "recurring_label": "Assinatura JETFLIX BR (streaming), todo dia 10",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_011", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "JETFLIX BR", "mcc": "4899",
        "valor": 55.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 10)), "data_lancamento": ts(d(2026, 6, 11)),
        "is_recurring": "sim", "recurring_label": "Assinatura JETFLIX BR (streaming), todo dia 10",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_012", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "JETFLIX BR", "mcc": "4899",
        "valor": 55.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 10)), "data_lancamento": ts(d(2026, 5, 11)),
        "is_recurring": "sim", "recurring_label": "Assinatura JETFLIX BR (streaming), todo dia 10",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Installments: monitor 3/10 and chair 2/6 (consistent history) ───
    {
        "transaction_id": "TXN_020", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "MONITOR ULTRAWIDE KABUM", "mcc": "5732",
        "valor": 412.00, "parcelas_total": 10, "parcela_atual": 3,
        "status": "aprovada",
        "data_compra": ts(d(2026, 4, 26)), "data_lancamento": ts(d(2026, 6, 24)),
        "is_recurring": "nao", "recurring_label": "Monitor ultrawide 34 pol em 10x de R$ 412,00",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_021", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "MONITOR ULTRAWIDE KABUM", "mcc": "5732",
        "valor": 412.00, "parcelas_total": 10, "parcela_atual": 2,
        "status": "aprovada",
        "data_compra": ts(d(2026, 4, 26)), "data_lancamento": ts(d(2026, 5, 24)),
        "is_recurring": "nao", "recurring_label": "Monitor ultrawide 34 pol em 10x de R$ 412,00",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_022", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "CADEIRA ERGO", "mcc": "5712",
        "valor": 350.00, "parcelas_total": 6, "parcela_atual": 2,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 30)), "data_lancamento": ts(d(2026, 6, 26)),
        "is_recurring": "nao", "recurring_label": "Cadeira ergonômica em 6x de R$ 350,00",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_023", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "CADEIRA ERGO", "mcc": "5712",
        "valor": 350.00, "parcelas_total": 6, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 30)), "data_lancamento": ts(d(2026, 6, 1)),
        "is_recurring": "nao", "recurring_label": "Cadeira ergonômica em 6x de R$ 350,00",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Current cycle (BILL_001): dev/tech + day-to-day spend ───
    {
        "transaction_id": "TXN_030", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "KABUM*TECLADO MECANICO", "mcc": "5732",
        "valor": 899.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 2)), "data_lancamento": ts(d(2026, 7, 3)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_031", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "KABUM*SSD NVME 2TB", "mcc": "5732",
        "valor": 1499.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 25)), "data_lancamento": ts(d(2026, 6, 26)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_032", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "KABUM*MONITOR PORTATIL", "mcc": "5732",
        "valor": 999.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 14)), "data_lancamento": ts(d(2026, 7, 15)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_033", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "AMAZON BR", "mcc": "5942",
        "valor": 259.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 6)), "data_lancamento": ts(d(2026, 7, 7)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_034", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "AMAZON BR MARKETPLACE", "mcc": "5999",
        "valor": 749.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 27)), "data_lancamento": ts(d(2026, 6, 28)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_035", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "ALURA CURSOS ONLINE", "mcc": "8299",
        "valor": 690.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 28)), "data_lancamento": ts(d(2026, 6, 29)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_036", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "CAFE ORIGEM", "mcc": "5814",
        "valor": 28.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 1)), "data_lancamento": ts(d(2026, 7, 2)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_037", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "CAFE ORIGEM", "mcc": "5814",
        "valor": 33.80, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 8)), "data_lancamento": ts(d(2026, 7, 9)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_038", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "IFOOD*JANTAR", "mcc": "5814",
        "valor": 124.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 3)), "data_lancamento": ts(d(2026, 7, 4)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_039", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "IFOOD*ALMOCO", "mcc": "5814",
        "valor": 52.40, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 9)), "data_lancamento": ts(d(2026, 7, 10)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_040", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "UBER *TRIP", "mcc": "4121",
        "valor": 37.80, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 11)), "data_lancamento": ts(d(2026, 7, 12)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_041", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "POSTO SHELL PARAISO", "mcc": "5541",
        "valor": 289.70, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 5)), "data_lancamento": ts(d(2026, 7, 6)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_042", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "MERCADO PAO DE ACUCAR", "mcc": "5411",
        "valor": 412.30, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 7)), "data_lancamento": ts(d(2026, 7, 8)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_043", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "HAMBURGUERIA BINARIA", "mcc": "5812",
        "valor": 98.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 4)), "data_lancamento": ts(d(2026, 7, 5)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_044", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_001",
        "tipo": "compra_credito",
        "merchant": "STEAM GAMES", "mcc": "5816",
        "valor": 249.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 13)), "data_lancamento": ts(d(2026, 7, 14)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Previous cycle (BILL_002): paid statement, sums to 1670.00 ───
    {
        "transaction_id": "TXN_050", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "KABUM*HUB USB-C", "mcc": "5732",
        "valor": 199.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 5)), "data_lancamento": ts(d(2026, 6, 6)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_051", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "CAFE ORIGEM", "mcc": "5814",
        "valor": 29.80, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 4)), "data_lancamento": ts(d(2026, 6, 5)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_052", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "IFOOD*JANTAR", "mcc": "5814",
        "valor": 68.50, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 15)), "data_lancamento": ts(d(2026, 6, 16)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_053", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "POSTO SHELL PARAISO", "mcc": "5541",
        "valor": 275.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 7)), "data_lancamento": ts(d(2026, 6, 8)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_054", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": "BILL_002",
        "tipo": "compra_credito",
        "merchant": "AMAZON BR", "mcc": "5942",
        "valor": 189.90, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 3)), "data_lancamento": ts(d(2026, 6, 4)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Pix sent: Carlos history (frequent, R$ 150-450, avg near 317) ───
    {
        "transaction_id": "TXN_060", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Carlos Eduardo Souza", "mcc": "PIX",
        "valor": 317.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 8)), "data_lancamento": ts(d(2026, 7, 8)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_061", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Carlos Eduardo Souza", "mcc": "PIX",
        "valor": 150.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 15)), "data_lancamento": ts(d(2026, 7, 15)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_062", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Carlos Eduardo Souza", "mcc": "PIX",
        "valor": 450.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 2)), "data_lancamento": ts(d(2026, 6, 2)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_063", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Carlos Eduardo Souza", "mcc": "PIX",
        "valor": 260.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 28)), "data_lancamento": ts(d(2026, 5, 28)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_064", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_recebido",
        "merchant": "PIX < Carlos Eduardo Souza (rateio churrasco)", "mcc": "PIX",
        "valor": -95.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 6)), "data_lancamento": ts(d(2026, 7, 6)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Pix sent: Tia Eulália (R$ 800,00 every day 1) ───
    {
        "transaction_id": "TXN_065", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Tia Eulália", "mcc": "PIX",
        "valor": 800.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 1)), "data_lancamento": ts(d(2026, 7, 1)),
        "is_recurring": "sim", "recurring_label": "Pix mensal pra Tia Eulália (todo dia 1)",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_066", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Tia Eulália", "mcc": "PIX",
        "valor": 800.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 1)), "data_lancamento": ts(d(2026, 6, 1)),
        "is_recurring": "sim", "recurring_label": "Pix mensal pra Tia Eulália (todo dia 1)",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Pix Automático executions: PUC tuition (R$ 1.500,00, day 5) ───
    # Largest Pix of the last 90 days by design (maior_pix_90d = 1500.00).
    {
        "transaction_id": "TXN_067", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX AUTOMATICO > PUC-SP (mensalidade Sofia)", "mcc": "PIX",
        "valor": 1500.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 5, 8)), "data_lancamento": ts(d(2026, 7, 5, 8)),
        "is_recurring": "sim", "recurring_label": "Pix Automático: mensalidade PUC da Sofia (todo dia 5)",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_068", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX AUTOMATICO > PUC-SP (mensalidade Sofia)", "mcc": "PIX",
        "valor": 1500.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 5, 8)), "data_lancamento": ts(d(2026, 6, 5, 8)),
        "is_recurring": "sim", "recurring_label": "Pix Automático: mensalidade PUC da Sofia (todo dia 5)",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Pix sent: allowance for Sofia ───
    {
        "transaction_id": "TXN_069", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Sofia Cerioni (mesada)", "mcc": "PIX",
        "valor": 300.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 11)), "data_lancamento": ts(d(2026, 7, 11)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Rent: paid MANUALLY via boleto (Pix Automatico candidate) ───
    # Not a Pix on purpose: keeps maior_pix_90d = 1500.00 truthful.
    {
        "transaction_id": "TXN_070", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "boleto",
        "merchant": "BOLETO ALUGUEL IMOBILIARIA HORIZONTE", "mcc": None,
        "valor": 2800.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 5, 9)), "data_lancamento": ts(d(2026, 7, 5, 9)),
        "is_recurring": "sim",
        "recurring_label": "Aluguel (todo dia 5, pago manualmente, candidato a Pix Automático)",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_071", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "boleto",
        "merchant": "BOLETO ALUGUEL IMOBILIARIA HORIZONTE", "mcc": None,
        "valor": 2800.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 5, 9)), "data_lancamento": ts(d(2026, 6, 5, 9)),
        "is_recurring": "sim",
        "recurring_label": "Aluguel (todo dia 5, pago manualmente, candidato a Pix Automático)",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Salary coming in (negative = inflow) ───
    {
        "transaction_id": "TXN_072", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "salario",
        "merchant": "SALARIO NEOSYS TECNOLOGIA LTDA", "mcc": None,
        "valor": -21000.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 6, 30, 7)), "data_lancamento": ts(d(2026, 6, 30, 7)),
        "is_recurring": "sim", "recurring_label": "Salário mensal (Neosys Tecnologia)",
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_073", "customer_id": DEMO_USER_ID,
        "card_id": None, "account_id": "ACC_001", "billing_cycle_id": None,
        "tipo": "salario",
        "merchant": "SALARIO NEOSYS TECNOLOGIA LTDA", "mcc": None,
        "valor": -21000.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 5, 30, 7)), "data_lancamento": ts(d(2026, 5, 30, 7)),
        "is_recurring": "sim", "recurring_label": "Salário mensal (Neosys Tecnologia)",
        "location_city": "São Paulo", "dispute_id": None,
    },

    # ─── Filler customers (dataset density, itau_assist pattern) ───
    {
        "transaction_id": "TXN_080", "customer_id": "CUST_002",
        "card_id": None, "account_id": "ACC_002", "billing_cycle_id": None,
        "tipo": "pix_envio",
        "merchant": "PIX > Condomínio Edifício Paulista", "mcc": "PIX",
        "valor": 230.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 10)), "data_lancamento": ts(d(2026, 7, 10)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": None,
    },
    {
        "transaction_id": "TXN_081", "customer_id": "CUST_003",
        "card_id": None, "account_id": "ACC_003", "billing_cycle_id": None,
        "tipo": "pix_recebido",
        "merchant": "PIX < República dos Devs (rateio internet)", "mcc": "PIX",
        "valor": -120.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "aprovada",
        "data_compra": ts(d(2026, 7, 12)), "data_lancamento": ts(d(2026, 7, 12)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "Campinas", "dispute_id": None,
    },

    # ─── Historical disputed transaction (resolved in 2025) ───
    {
        "transaction_id": "TXN_090", "customer_id": DEMO_USER_ID,
        "card_id": "CARD_001", "account_id": None, "billing_cycle_id": None,
        "tipo": "compra_credito",
        "merchant": "LOJA GAMER PIXELSTORE", "mcc": "5732",
        "valor": 459.00, "parcelas_total": 1, "parcela_atual": 1,
        "status": "estornada",
        "data_compra": ts(d(2025, 11, 8)), "data_lancamento": ts(d(2025, 11, 9)),
        "is_recurring": "nao", "recurring_label": None,
        "location_city": "São Paulo", "dispute_id": "DSP_001",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES (1) — historical, resolved in Gabriel's favor in 2025
# ═══════════════════════════════════════════════════════════════════════════

DISPUTES = [
    {
        "dispute_id": "DSP_001", "customer_id": DEMO_USER_ID,
        "transaction_id": "TXN_090",
        "protocolo": "DSP20251108-1337AB",
        "motivo": "nao_reconheco",
        "status": "resolvida_favoravel",
        "valor_contestado": 459.00,
        "data_abertura": ts(d(2025, 11, 10)),
        "data_resolucao": ts(d(2025, 11, 16)),
        "descricao": "Não reconheço essa compra na Loja Gamer Pixelstore. Nunca comprei nesse site.",
        "resolucao": "Estorno integral aprovado em favor do cliente. Valor revertido na fatura seguinte.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PIX CONTACTS (4) — Gabriel's trusted contacts.
#  The scam key "11 91234-0666" is deliberately in NO contact.
# ═══════════════════════════════════════════════════════════════════════════

PIX_CONTACTS = [
    {
        "contact_id": "PIX_001", "customer_id": DEMO_USER_ID,
        "recipient_name": "Carlos Eduardo Souza",
        "chave_pix": "+55 11 95333-2002",
        "chave_tipo": "celular",
        "banco_destino": "Leet Bank",
        "contato_desde": "2021-04",
        "frequencia_uso": 23,
        "ultimo_uso": ts(d(2026, 7, 15)),
    },
    {
        "contact_id": "PIX_002", "customer_id": DEMO_USER_ID,
        "recipient_name": "Tia Eulália",
        "chave_pix": "eulalia.cerioni@email.com",
        "chave_tipo": "email",
        "banco_destino": "Banco do Brasil",
        "contato_desde": "2019-08",
        "frequencia_uso": 30,
        "ultimo_uso": ts(d(2026, 7, 1)),
    },
    {
        "contact_id": "PIX_003", "customer_id": DEMO_USER_ID,
        "recipient_name": "Sofia Cerioni",
        "chave_pix": "+55 11 96122-2010",
        "chave_tipo": "celular",
        "banco_destino": "Leet Bank",
        "contato_desde": "2022-02",
        "frequencia_uso": 15,
        "ultimo_uso": ts(d(2026, 7, 11)),
    },
    {
        "contact_id": "PIX_004", "customer_id": DEMO_USER_ID,
        "recipient_name": "Imobiliária Horizonte",
        "chave_pix": "12.345.678/0001-90",
        "chave_tipo": "cnpj",
        "banco_destino": "Bradesco",
        "contato_desde": "2025-01",
        "frequencia_uso": 0,
        "ultimo_uso": None,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PIX AUTOMATICO (1) — pre-existing example: PUC tuition already enrolled.
#  The rent is deliberately NOT enrolled: enrolling it IS the demo journey.
# ═══════════════════════════════════════════════════════════════════════════

PIX_AUTOMATICO = [
    {
        "autorizacao_id": "PIXAUTO_001", "customer_id": DEMO_USER_ID,
        "payee_name": "PUC-SP Mensalidades",
        "chave_pix": "mensalidades@pucsp.example.br",
        "chave_tipo": "email",
        "valor": 1500.00,
        "dia_cobranca": 5,
        "periodicidade": "mensal",
        "status": "ativo",
        "data_criacao": ts(d(2025, 2, 10)),
        "ultima_cobranca": ts(d(2026, 7, 5, 8)),
        "descricao": "Mensalidade da graduação da Sofia na PUC, autorizada uma única vez e debitada automaticamente todo dia 5.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  REWARDS (1) — XP program (leet numbers: 133.700 XP, Elite 1337)
# ═══════════════════════════════════════════════════════════════════════════

REWARDS_ACCOUNTS = [
    {
        "rewards_id": "RWD_001", "customer_id": DEMO_USER_ID,
        "programa": "leet_xp",
        "saldo_xp": 133700,
        "nivel": "Elite 1337",
        "xp_expirando": 4200,
        "expira_em": "2026-09-30",
        "multiplicador_tech": 2,
        "categoria_top": "tech_eletronicos",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS (2) — one in progress + one closed
# ═══════════════════════════════════════════════════════════════════════════

SUPPORT_TICKETS = [
    {
        "ticket_id": "TKT_001", "customer_id": DEMO_USER_ID,
        "categoria": "cartao", "status": "em_andamento",
        "data_abertura": ts(d(2026, 7, 14, 10)),
        "data_resolucao": None,
        "resumo": "Solicitação de 2ª via do cartão Leet Black final 1337 com chip NFC. Cartão em produção.",
        "resolucao": None,
    },
    {
        "ticket_id": "TKT_002", "customer_id": DEMO_USER_ID,
        "categoria": "investimentos", "status": "resolvido",
        "data_abertura": ts(d(2026, 5, 6, 14)),
        "data_resolucao": ts(d(2026, 5, 6, 16)),
        "resumo": "Dúvida sobre o rendimento do CDB Leet (103,37% do CDI) e a liquidez diária.",
        "resolucao": "Explicado o rendimento de 103,37% do CDI com liquidez diária e resgate em D+0. Cliente confirmou entendimento.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — Leet Bank policies in PT-BR
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "Golpes e Segurança no Pix", "category": "seguranca",
        "content": (
            "O Leet Bank monitora todos os Pix em tempo real com modelo antifraude alimentado por "
            "features online do cliente. Sinais clássicos de golpe: chave Pix desconhecida (que não "
            "está nos contatos salvos do cliente), senso de urgência criado por mensagem de WhatsApp "
            "ou ligação, valor fora do padrão histórico do cliente e pedido pra manter a transferência "
            "em segredo. Quando a transação apresenta esses sinais, o banco pode SEGURAR o Pix por até "
            "72 horas pra análise e verificação, notificando o cliente pelo app. A confirmação de "
            "identidade do destinatário deve sempre acontecer por canal oficial (app ou central), "
            "nunca pelo link ou telefone recebido na mensagem suspeita. Em caso de golpe consumado, o "
            "cliente pode acionar o MED (Mecanismo Especial de Devolução) do Banco Central em até 80 "
            "dias pra tentar recuperar os valores. O Leet Bank nunca pede senha, token ou "
            "transferência pra 'conta segura'."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Limites do Pix", "category": "pix",
        "content": (
            "Limites padrão do Pix no Leet Bank: R$ 5.000,00 por transação no período diurno (6h às "
            "20h) e R$ 1.000,00 por transação no período noturno (20h às 6h). Clientes do segmento "
            "Elite 1337 podem solicitar ampliação de limite direto no app, com validação em duas "
            "etapas. Pedidos de aumento de limite passam por análise de segurança e entram em vigor "
            "em até 24 horas (redução é imediata). Pix acima do padrão histórico do cliente pode "
            "disparar verificação adicional antifraude mesmo dentro do limite."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Pix Automático", "category": "pix",
        "content": (
            "O Pix Automático permite autorizar uma recorrência UMA única vez e deixar as cobranças "
            "seguintes acontecerem automaticamente, no estilo débito automático, sem precisar aprovar "
            "cada mês. Ideal pra mensalidades escolares, aluguel, condomínio e assinaturas. O cliente "
            "define o recebedor, o valor e o dia da cobrança; o banco notifica antes de cada débito e "
            "executa no dia agendado. A autorização pode ser pausada ou cancelada a qualquer momento "
            "pelo app, sem custo. Se não houver saldo no dia, o banco tenta novamente conforme a "
            "política de retentativa acordada. Recorrências já pagas manualmente todo mês (como "
            "aluguel) são candidatas naturais à migração pro Pix Automático."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Crédito Flash com Garantia Tokenizada", "category": "credito",
        "content": (
            "O Crédito Flash usa o CDB do cliente como garantia tokenizada: o certificado é "
            "representado como token e bloqueado como colateral da operação, sem precisar resgatar o "
            "investimento. Contratação 100% digital em minutos pelo app. Para clientes Elite 1337 a "
            "taxa é de 1,337% ao mês, com limite pré-aprovado proporcional ao CDB livre de garantias. "
            "O CDB continua rendendo normalmente (por exemplo, 103,37% do CDI) durante toda a "
            "operação. Conforme o cliente amortiza o empréstimo, o colateral é liberado "
            "proporcionalmente e volta a ficar disponível. Em caso de inadimplência, o banco executa "
            "a garantia tokenizada pelo valor devido. Sem tarifas de contratação antecipada."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Programa de Pontos XP", "category": "pontos",
        "content": (
            "O programa XP do Leet Bank credita 1 XP por real gasto no cartão de crédito, com "
            "multiplicador de 2x em compras de tech e eletrônicos. Os níveis do programa são "
            "Iniciante, Hacker e Elite 1337, definidos pelo acúmulo dos últimos 12 meses. XP pode ser "
            "resgatado em experiências (shows, festivais, eventos de tecnologia), cashback na fatura "
            "e produtos do catálogo. Os pontos expiram em 24 meses a partir do acúmulo e o app avisa "
            "com 90 dias de antecedência quando um lote está pra expirar. XP expirado não é "
            "reembolsável."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Contestação de Cobrança no Cartão", "category": "contestacao",
        "content": (
            "O cliente pode contestar qualquer lançamento da fatura em até 90 dias após o vencimento. "
            "Antes de abrir a contestação, o atendimento verifica se a cobrança faz parte de um padrão "
            "recorrente do próprio cliente (mesmo estabelecimento, valor estável, frequência regular, "
            "flag de recorrência no histórico): assinaturas legítimas reconhecidas pelo histórico "
            "costumam ser lembradas e a contestação evitada. Confirmada a intenção, a contestação gera "
            "protocolo formal e análise em até 7 dias úteis. Em fraude clara (cartão não presente, "
            "compra fora do perfil), o estorno provisório pode ser aplicado em 48 horas. Cancelar uma "
            "assinatura é responsabilidade do cliente junto ao prestador; o banco estorna lançamentos "
            "passados quando aplicável, mas não cancela cobranças futuras."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Anuidade do Cartão Leet Black", "category": "fatura",
        "content": (
            "O cartão Leet Black tem anuidade de R$ 1.188,00 por ano (12x de R$ 99,00), com isenção "
            "TOTAL para clientes com fatura mensal acima de R$ 5.000,00 (média dos últimos 3 ciclos). "
            "A isenção é reavaliada automaticamente a cada trimestre e aparece na fatura como "
            "'anuidade isenta'. Benefícios do Leet Black: multiplicador do programa XP, salas VIP em "
            "aeroportos, seguro de compras e acesso antecipado a eventos parceiros. Clientes Elite "
            "1337 têm atendimento prioritário na central."
        ),
    },
    {
        "policy_id": "POL_008", "title": "Cartão Virtual e Segurança", "category": "cartao",
        "content": (
            "O Leet Virtual é um cartão de número próprio (independente do físico) recomendado pra "
            "compras online e assinaturas. O CVV é dinâmico e renovado periodicamente no app. Em caso "
            "de vazamento ou suspeita de fraude, o cartão virtual pode ser bloqueado e substituído "
            "instantaneamente sem afetar o cartão físico nem as compras já aprovadas. Compras no "
            "cartão virtual entram na mesma fatura do titular. Boas práticas: usar o virtual em sites "
            "novos, nunca compartilhar prints com número completo e ativar notificações em tempo real."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Open Finance no Leet Bank", "category": "open_finance",
        "content": (
            "Pelo Open Finance o cliente pode trazer pro Leet Bank os dados de contas, cartões e "
            "investimentos que mantém em outros bancos, com consentimento explícito e revogável a "
            "qualquer momento pelo app. O consentimento padrão vale por 12 meses e pode ser renovado. "
            "Com os dados consolidados, o banco melhora ofertas de crédito, personaliza o "
            "atendimento e mostra uma visão única do patrimônio. O Leet Bank nunca acessa dados sem "
            "consentimento ativo e a revogação interrompe o compartilhamento imediatamente, conforme "
            "as regras do Banco Central."
        ),
    },
    {
        "policy_id": "POL_010", "title": "Experiências e Eventos", "category": "experiencias",
        "content": (
            "O Leet Bank mantém parcerias com grandes festivais, shows e eventos de tecnologia. "
            "Clientes podem resgatar XP em ingressos e experiências, receber cashback em compras de "
            "experiências com o Leet Black e solicitar limite temporário de viagem ou evento pelo app "
            "(vigência de até 30 dias). Alerta de golpe de ingresso: compre SOMENTE em canais oficiais "
            "do evento ou em parceiros listados no app. Ingressos oferecidos por terceiros em redes "
            "sociais com desconto agressivo e pagamento via Pix pra chave desconhecida são o principal "
            "vetor de golpe em época de festival; o banco pode segurar esses Pix pra verificação "
            "conforme a política de segurança."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE (1) — Gabriel's online features, read in real time by MarIAm
#  (anti-scam gate, Credito Flash NBA and XP nudges). Leet literals are canon.
# ═══════════════════════════════════════════════════════════════════════════

FEATURE_STORE = [
    {
        "customer_id": DEMO_USER_ID,
        "saldo": 31337.00,
        "cdb_total": 133700.00,
        "cdb_livre": 133700.00,
        "credito_flash_pre_aprovado": 100000.00,
        "taxa_flash_am": 1.337,
        "pix_ticket_medio": 317.00,
        "maior_pix_90d": 1500.00,
        "contatos_confiaveis": 4,
        "golpe_score": 0.02,
        "utilizacao_cartao_pct": 12,
        "xp_saldo": 133700,
        "xp_expirando": 4200,
        "nivel": "elite_1337",
        "propensao_credito": 0.91,
        "torce_para": "palmeiras",
        "evento_proximo": "rock_in_rio_2026_09_07",
        "ultima_atualizacao": ts(d(2026, 7, 17, 11, 52)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  CONSISTENCY CHECKS — fail loudly at generation time if the canon drifts
# ═══════════════════════════════════════════════════════════════════════════

def _cycle_total(cycle_id: str) -> float:
    return round(sum(t["valor"] for t in TRANSACTIONS if t["billing_cycle_id"] == cycle_id), 2)


def check_consistency() -> None:
    # Open statement must equal the sum of its card lines (canonical 7331.00).
    assert _cycle_total("BILL_001") == 7331.00, f"BILL_001 sum drifted: {_cycle_total('BILL_001')}"
    assert _cycle_total("BILL_002") == 1670.00, f"BILL_002 sum drifted: {_cycle_total('BILL_002')}"

    # CLOUD DEV PRO must recur on day 12 across May/Jun/Jul 2026.
    cloud = [t for t in TRANSACTIONS if t["merchant"] == "CLOUD DEV PRO"]
    assert len(cloud) == 3 and all(t["is_recurring"] == "sim" for t in cloud)
    assert sorted(t["data_compra"][:10] for t in cloud) == ["2026-05-12", "2026-06-12", "2026-07-12"]

    # No Pix sent in the last 90 days above the canonical 1500.00 ceiling.
    pix_values = [t["valor"] for t in TRANSACTIONS if t["tipo"] == "pix_envio"]
    assert max(pix_values) == 1500.00, f"maior Pix drifted: {max(pix_values)}"

    # The scam key must exist NOWHERE in the seed.
    blob = json.dumps(
        [CUSTOMERS, ACCOUNTS, CARDS, BILLING_CYCLES, TRANSACTIONS, DISPUTES,
         PIX_CONTACTS, PIX_AUTOMATICO, REWARDS_ACCOUNTS, SUPPORT_TICKETS,
         FEATURE_STORE, POLICIES_TEXT],
        ensure_ascii=False,
    )
    assert SCAM_KEY_FRAGMENT not in blob, "scam Pix key leaked into the seed"


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — embeds policies + writes JSONLs
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


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed  # dataset is hand-authored and pinned to July 2026; fully deterministic
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    check_consistency()

    print("Gerando embeddings das políticas...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Escrevendo arquivos JSONL:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "accounts.jsonl", ACCOUNTS)
    write_jsonl(resolved_output_dir, "cards.jsonl", CARDS)
    write_jsonl(resolved_output_dir, "billing_cycles.jsonl", BILLING_CYCLES)
    write_jsonl(resolved_output_dir, "transactions.jsonl", TRANSACTIONS)
    write_jsonl(resolved_output_dir, "disputes.jsonl", DISPUTES)
    write_jsonl(resolved_output_dir, "pix_contacts.jsonl", PIX_CONTACTS)
    write_jsonl(resolved_output_dir, "pix_automatico.jsonl", PIX_AUTOMATICO)
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
            "billing_cycles": len(BILLING_CYCLES),
            "transactions": len(TRANSACTIONS),
            "disputes": len(DISPUTES),
            "pix_contacts": len(PIX_CONTACTS),
            "pix_automatico": len(PIX_AUTOMATICO),
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
