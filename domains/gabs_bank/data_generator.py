"""Gabs Bank (AI concierge) — synthetic seed in English.

Persona: Gabriel Cerioni, Gabs Bank Premier client (high income), 6 years with the
bank, one super app (free checking + Gabs Invest + Gabs Rewards cashback + Gabs
Marketplace). The online feature-store features are calibrated for an interesting
next-best-offer: high propensity to invest + idle cash sitting in a TAXABLE money
market => the model recommends moving into TAX-EXEMPT municipal bonds. Deterministic
tools write at runtime.

Fictional bank. Internal Redis demo, not affiliated with any real institution.
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

OUTPUT_DIR = ROOT / "output" / "gabs_bank"
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
        "cpf_masked": "***-**-6789",
        "email": "gabriel.cerioni@example.com",
        "cidade": "Austin",
        "segmento": "premier",
        "agencia": "0001",
        "conta": "****-**-7",
        "cliente_desde_anos": 6,
        "renda_mensal": 45000.00,
        "score_interno": 920,
        "perfil_investidor": "moderate",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  ACCOUNTS — free checking + Gabs Invest brokerage
# ═══════════════════════════════════════════════════════════════════════════
ACCOUNTS = [
    {"account_id": "ACC_001", "customer_id": DEMO_USER_ID, "tipo": "checking",
     "saldo": 92300.50, "limite_cheque_especial": 50000.00, "status": "active"},
    {"account_id": "ACC_002", "customer_id": DEMO_USER_ID, "tipo": "brokerage",
     "saldo": 220000.00, "limite_cheque_especial": 0.00, "status": "active"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  CARDS — Gabs Black (Mastercard Black, no annual fee) + Gabs debit card
# ═══════════════════════════════════════════════════════════════════════════
CARDS = [
    {"card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID, "produto": "Gabs Black",
     "tipo": "credit", "bandeira": "mastercard", "final": "8821", "limite": 80000.00,
     "fatura_atual": 17850.40, "vencimento": ts(now + timedelta(days=10)), "anuidade": 0.00, "status": "active"},
    {"card_id": "CARD_DEB", "customer_id": DEMO_USER_ID, "produto": "Gabs Debit",
     "tipo": "debit", "bandeira": "mastercard", "final": "3310", "limite": 0.00,
     "fatura_atual": 0.00, "vencimento": ts(now + timedelta(days=30)), "anuidade": 0.00, "status": "active"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _txn(i, card, acc, tipo, merchant, mcc, valor, days_ago, rec="no", status="approved", pa=1, pt=1):
    return {"txn_id": f"TXN_{i:03d}", "customer_id": DEMO_USER_ID, "card_id": card, "account_id": acc,
            "tipo": tipo, "merchant": merchant, "mcc": mcc, "valor": round(valor, 2),
            "data": ts(now - timedelta(days=days_ago)), "is_recurring": rec,
            "parcela_atual": pa, "parcela_total": pt,
            "valor_parcela": round(valor / pt, 2) if pt else round(valor, 2),
            "status": status}

TRANSACTIONS = [
    # ── Installment purchases on the statement ──
    _txn(1, "CARD_BLACK", None, "credit_purchase", "APPLE STORE", "5732", 9600.00, 70, pa=3, pt=12),       # iPhone 12x
    _txn(2, "CARD_BLACK", None, "credit_purchase", "LATAM AIRLINES", "3174", 7200.00, 40, pa=2, pt=6),      # flights 6x
    _txn(3, "CARD_BLACK", None, "credit_purchase", "GABS MARKETPLACE ELECTRONICS", "5712", 4500.00, 130, pa=5, pt=10),  # marketplace 10x
    _txn(4, "CARD_BLACK", None, "credit_purchase", "BEST BUY LAPTOP", "5732", 6400.00, 20, pa=1, pt=8),     # laptop 8x
    # ── Recurring (recognized subscriptions) ──
    _txn(5, "CARD_BLACK", None, "credit_purchase", "NETFLIX.COM", "4899", 55.90, 5, rec="yes"),
    _txn(6, "CARD_BLACK", None, "credit_purchase", "SPOTIFY USA", "4899", 34.90, 6, rec="yes"),
    _txn(7, "CARD_BLACK", None, "credit_purchase", "AMAZON PRIME", "5968", 19.90, 2, rec="yes"),
    # ── One-off (lifestyle: dining, wine, fuel, shopping) ──
    _txn(8, "CARD_BLACK", None, "credit_purchase", "NOBU RESTAURANT", "5812", 1240.00, 4),
    _txn(9, "CARD_BLACK", None, "credit_purchase", "WINE.COM", "5921", 980.00, 12),
    _txn(10, "CARD_BLACK", None, "credit_purchase", "SHELL GAS STATION", "5541", 420.00, 8),
    _txn(11, "CARD_BLACK", None, "credit_purchase", "CVS PHARMACY", "5912", 186.30, 10),
    _txn(12, "CARD_BLACK", None, "credit_purchase", "WESTFIELD MALL", "5651", 2150.00, 14),
    # ── Transfers and account (family, rent, cashback) ──
    _txn(13, None, "ACC_001", "transfer_in", "Rent payment", "XFER", 6500.00, 4, rec="yes"),
    _txn(14, None, "ACC_001", "transfer_out", "Sofia Cerioni (allowance)", "XFER", 3800.00, 5, rec="yes"),
    _txn(15, None, "ACC_001", "transfer_out", "Aunt Eulalia", "XFER", 800.00, 1, rec="yes"),
    _txn(16, None, "ACC_002", "cashback", "Gabs Rewards Cashback", "CASH", 230.00, 2),
]

# ═══════════════════════════════════════════════════════════════════════════
#  BILLING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
BILLING_CYCLES = [
    {"cycle_id": "BILL_BLACK_OPEN", "card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID,
     "mes_referencia": now.strftime("%Y-%m"), "valor_total": 17850.40, "valor_minimo": 2677.56,
     "vencimento": ts(now + timedelta(days=10)), "status": "open"},
    {"cycle_id": "BILL_BLACK_PREVIOUS", "card_id": "CARD_BLACK", "customer_id": DEMO_USER_ID,
     "mes_referencia": (now - timedelta(days=30)).strftime("%Y-%m"), "valor_total": 14230.00,
     "valor_minimo": 2134.50, "vencimento": ts(now - timedelta(days=20)), "status": "paid"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  INVESTMENTS — Gabriel has idle cash in a TAXABLE money market (the NBO hook)
# ═══════════════════════════════════════════════════════════════════════════
INVESTMENTS = [
    {"investment_id": "INV_MM", "customer_id": DEMO_USER_ID, "produto": "Money Market",
     "descricao": "Gabs Invest money market fund (taxable)", "valor_aplicado": 180000.00,
     "rentabilidade_cdi_pct": 100, "vencimento": ts(now + timedelta(days=400)), "liquidez": "daily"},
    {"investment_id": "INV_FUND", "customer_id": DEMO_USER_ID, "produto": "Fund",
     "descricao": "Gabs Invest Core Bond Fund", "valor_aplicado": 40000.00,
     "rentabilidade_cdi_pct": 98, "vencimento": ts(now + timedelta(days=180)), "liquidez": "T_plus_30"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSFER CONTACTS (resolve recipient by name for the natural-banking flagship)
# ═══════════════════════════════════════════════════════════════════════════
PIX_CONTACTS = [
    {"contact_id": "PIX_CARLOS", "customer_id": DEMO_USER_ID, "nome": "Carlos Eduardo Souza",
     "chave_pix": "+1 512 555-2002", "tipo_chave": "phone", "banco": "Gabs Bank", "is_frequente": "yes"},
    {"contact_id": "PIX_EULALIA", "customer_id": DEMO_USER_ID, "nome": "Aunt Eulalia Cerioni",
     "chave_pix": "eulalia.***@email.com", "tipo_chave": "email", "banco": "Chase", "is_frequente": "yes"},
    {"contact_id": "PIX_SOFIA", "customer_id": DEMO_USER_ID, "nome": "Sofia Cerioni",
     "chave_pix": "***-**-2233", "tipo_chave": "account", "banco": "Gabs Bank", "is_frequente": "yes"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES
# ═══════════════════════════════════════════════════════════════════════════
DISPUTES = [
    {"dispute_id": "DSP_HIST", "customer_id": DEMO_USER_ID, "transaction_id": None,
     "motivo": "Duplicate subscription charge, resolved in 2025", "valor": 49.90,
     "status": "upheld", "data": ts(now - timedelta(days=120))},
]

# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE — Gabriel's online features (the heart of the differentiator)
#  Calibrated: high investment propensity + idle cash => NBO = tax-exempt bonds
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
        "perfil_digital": "high",
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — Gabs Bank help/policy docs, embedded at runtime
# ═══════════════════════════════════════════════════════════════════════════
POLICIES_TEXT = [
    {"policy_id": "POL_PIX", "title": "Instant transfer limits by time of day", "category": "limits",
     "content": "Gabs Bank instant transfer limits by time of day. During the day, from 6am to 8pm, the "
                "limit is $10,000 per transaction. Overnight, from 8pm to 6am, the limit drops to $1,000 "
                "per transaction for security. Transfers between Gabs Bank accounts are instant, free and "
                "available 24/7. Premier clients can request extended limits in the app, at no cost."},
    {"policy_id": "POL_CONTESTACAO", "title": "Disputing a charge", "category": "dispute",
     "content": "To dispute a charge: confirm you do not recognize the transaction, open the dispute in "
                "the app or with the assistant, and the amount goes under review with a provisional credit "
                "in eligible cases. Up to 7 business days, with a case number. A recognized recurring charge "
                "(a subscription) tends to be found not valid, so confirm first."},
    {"policy_id": "POL_CARTAO", "title": "Cards and annual fees at Gabs Bank", "category": "card",
     "content": "The Gabs debit card and the Gabs Black card have NO annual fee, ever, with no minimum "
                "spend required. You track your statement, adjust the limit and freeze the card in the app, "
                "instantly. A limit increase goes through a score and usage review. Gabs Black is a "
                "Mastercard Black, with airport lounge access (LoungeKey) and Mastercard benefits."},
    {"policy_id": "POL_INVEST", "title": "Investing with Gabs Invest", "category": "investment",
     "content": "Gabs Invest offers money market funds, CDs, Treasuries, mutual funds and municipal bonds. "
                "Municipal bonds are exempt from federal income tax, which makes them great for someone with "
                "idle cash sitting in a taxable money market. Gabs Invest CDs tend to pay above-market rates. "
                "The recommendation depends on the investor profile and the goal."},
    {"policy_id": "POL_INTER_ONE", "title": "Gabs Bank Premier benefits", "category": "premier",
     "content": "Gabs Bank Premier is the high-income tier: a dedicated investment advisor, exclusive "
                "offers and events, a Gabs Black card with no annual fee, and priority support. Everything "
                "in the app, no branches and no maintenance fees. Premium relationship with the convenience "
                "of digital."},
    {"policy_id": "POL_SEGURANCA", "title": "Security and transfer scams", "category": "security",
     "content": "Be suspicious of brand-new payee accounts, urgent requests and prizes. Gabs Bank flags "
                "transactions with an atypical pattern. If you were the victim of a scam or suspect "
                "unauthorized access, freeze the card in the app, change your password and file a report. "
                "The assistant never asks for your password or one-time code."},
    {"policy_id": "POL_LOOP", "title": "Gabs Rewards, cash back", "category": "cashback",
     "content": "Gabs Rewards is the cash back program: you get real money back (not points) on credit "
                "purchases, debit, Gabs Marketplace and partners. Cash back lands straight in your account "
                "and can compound in a CD, or top up a savings goal. On Gabs Marketplace the cash back is "
                "boosted. You track the running total in the app."},
    {"policy_id": "POL_SEGURO", "title": "Gabs Insurance", "category": "investment",
     "content": "Gabs Insurance offers life, home, travel and card/phone protection. Premier clients and "
                "Gabs Black holders get expanded coverage and premium assistance. You can buy and adjust "
                "coverage in the app to fit your profile."},
    {"policy_id": "POL_LGPD", "title": "Privacy and data protection", "category": "privacy",
     "content": "Your data is protected under applicable privacy law. Gabs Bank does not share your history "
                "with third parties without consent. You can review, export or request deletion of your data "
                "through the official channels in the app."},
    {"policy_id": "POL_INTERNACIONAL", "title": "International card, Gabs Global, FX fees and travel insurance", "category": "card",
     "content": "To use your card abroad, turn on international purchases in the app and set a travel notice "
                "(dates and destination) to avoid a preventive block. International credit purchases carry a "
                "foreign transaction fee, already shown on the statement, no surprises. Always pay in the "
                "local currency, never in dollars, to avoid the merchant's bad exchange rate. Gabs Bank "
                "offers Gabs Global, a multi-currency account with no monthly fee, great to load before a "
                "trip and spend on debit abroad. Gabs Black includes travel insurance (medical and baggage) "
                "and airport lounge access (LoungeKey). You can buy standalone travel insurance with "
                "expanded coverage and request a temporary limit bump for the trip, all in the app. Use "
                "credit abroad rather than plain debit, for security and purchase protection."},
]


def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {filename}: {len(rows)} records")


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

    print("Generating policy embeddings...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Writing JSONL files:")
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
    print(f"\nDemo user: {demo['nome']} ({demo['customer_id']})")
    print("Done.")

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
