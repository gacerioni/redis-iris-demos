"""Bradesco EN, synthetic seed in EN-US.

Persona: Gabriel Cerioni, Bradesco Prime (affluent segment), 11 years with the
bank, based in Austin, Texas. Online features in the feature store are
calibrated for an interesting next-best-offer: high investment propensity plus
idle cash in a taxable CD, so the model recommends moving into tax-exempt
municipal bonds or retirement products. Deterministic tools write at runtime.
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

OUTPUT_DIR = ROOT / "output" / "bradesco_en"

# Fixed demo anchor: the storyline is pinned to July 2026 (the open billing
# cycle, the statement due date, and the monthly AMZN DIGITAL*SVCS recurrence
# are part of the demo script), so the generator uses a fixed "today" instead
# of datetime.now() and stays fully deterministic across runs.
now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)


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
        "name": "Gabriel Cerioni",
        "ssn_masked": "***-**-6789",
        "email": "gabriel.cerioni@example.com",
        "city": "Austin",
        "segment": "prime",
        "branch": "1234",
        "account_number": "***-***-7",
        "customer_since_years": 11,
        "monthly_income": 45000.00,
        "internal_score": 920,
        "investor_profile": "moderate",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════
ACCOUNTS = [
    {"account_id": "ACC_001", "customer_id": DEMO_USER_ID, "type": "checking",
     "balance": 92300.50, "overdraft_limit": 50000.00, "status": "active"},
    {"account_id": "ACC_002", "customer_id": DEMO_USER_ID, "type": "investment",
     "balance": 220000.00, "overdraft_limit": 0.00, "status": "active"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  CARDS
# ═══════════════════════════════════════════════════════════════════════════
CARDS = [
    {"card_id": "CARD_INFINITE", "customer_id": DEMO_USER_ID, "product": "Bradesco Visa Infinite",
     "type": "credit", "network": "visa", "last4": "8821", "credit_limit": 80000.00,
     "current_statement": 17850.40, "due_date": ts(now + timedelta(days=10)), "annual_fee": 0.00, "status": "active"},
    {"card_id": "CARD_DEB", "customer_id": DEMO_USER_ID, "product": "Bradesco Visa Debit",
     "type": "debit", "network": "visa", "last4": "3310", "credit_limit": 0.00,
     "current_statement": 0.00, "due_date": ts(now + timedelta(days=30)), "annual_fee": 0.00, "status": "active"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _txn(i, card, acc, type_, merchant, mcc, amount, days_ago, rec="no", status="approved", ic=1, it=1):
    return {"txn_id": f"TXN_{i:03d}", "customer_id": DEMO_USER_ID, "card_id": card, "account_id": acc,
            "type": type_, "merchant": merchant, "mcc": mcc, "amount": round(amount, 2),
            "date": ts(now - timedelta(days=days_ago)), "is_recurring": rec,
            "installment_current": ic, "installment_total": it,
            "installment_amount": round(amount / it, 2) if it else round(amount, 2),
            "status": status}

TRANSACTIONS = [
    # -- Statement payment plans (the use case that was missing) --
    _txn(1, "CARD_INFINITE", None, "credit_purchase", "APPLE STORE DOMAIN NORTHSIDE", "5732", 9600.00, 70, ic=3, it=12),  # iPhone + iPad, 12-month plan
    _txn(2, "CARD_INFINITE", None, "credit_purchase", "AMERICAN AIRLINES DALLAS", "3174", 7200.00, 40, ic=2, it=6),       # flights, 6-month plan
    _txn(3, "CARD_INFINITE", None, "credit_purchase", "POTTERY BARN DOMAIN", "5712", 4500.00, 130, ic=5, it=10),          # furniture, 10-month plan
    _txn(4, "CARD_INFINITE", None, "credit_purchase", "BEST BUY LAPTOP", "5732", 6400.00, 20, ic=1, it=8),                # laptop, 8-month plan
    # -- Recurring (recognized subscriptions) --
    _txn(5, "CARD_INFINITE", None, "credit_purchase", "NETFLIX.COM", "4899", 55.90, 5, rec="yes"),
    _txn(6, "CARD_INFINITE", None, "credit_purchase", "SPOTIFY USA", "4899", 34.90, 6, rec="yes"),
    _txn(7, "CARD_INFINITE", None, "credit_purchase", "AMZN DIGITAL*SVCS", "5968", 19.90, 2, rec="yes"),
    # Prior month of the same subscription: the same-amount monthly history is
    # the anchor for the smart-dispute journey (recurring charge the customer
    # does not recognize at first glance).
    _txn(17, "CARD_INFINITE", None, "credit_purchase", "AMZN DIGITAL*SVCS", "5968", 19.90, 32, rec="yes"),
    # -- One-time (Prime lifestyle: steakhouse, wine, fuel, shopping) --
    _txn(8, "CARD_INFINITE", None, "credit_purchase", "PAPPAS BROS STEAKHOUSE", "5812", 1240.00, 4),
    _txn(9, "CARD_INFINITE", None, "credit_purchase", "TOTAL WINE AND MORE", "5921", 980.00, 12),
    _txn(10, "CARD_INFINITE", None, "credit_purchase", "SHELL OIL", "5541", 420.00, 8),
    _txn(11, "CARD_INFINITE", None, "credit_purchase", "CVS PHARMACY", "5912", 186.30, 10),
    _txn(12, "CARD_INFINITE", None, "credit_purchase", "NORDSTROM DOMAIN NORTHSIDE", "5651", 2150.00, 14),
    # -- Zelle and account (family, rent income, cash rewards) --
    _txn(13, None, "ACC_001", "zelle_received", "Rent Payment (Austin rental property)", "ZELLE", 6500.00, 4, rec="yes"),
    _txn(14, None, "ACC_001", "zelle_sent", "Sofia Cerioni (college tuition)", "ZELLE", 3800.00, 5, rec="yes"),
    _txn(15, None, "ACC_001", "zelle_sent", "Aunt Emma", "ZELLE", 800.00, 1, rec="yes"),
    _txn(16, None, "ACC_002", "cashback", "Bradesco Cash Rewards", "CASH", 230.00, 2),
]

# ═══════════════════════════════════════════════════════════════════════════
#  BILLING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
BILLING_CYCLES = [
    {"cycle_id": "BILL_INFINITE_OPEN", "card_id": "CARD_INFINITE", "customer_id": DEMO_USER_ID,
     "reference_month": now.strftime("%Y-%m"), "total_amount": 17850.40, "minimum_payment": 2677.56,
     "due_date": ts(now + timedelta(days=10)), "status": "open"},
    {"cycle_id": "BILL_INFINITE_PREVIOUS", "card_id": "CARD_INFINITE", "customer_id": DEMO_USER_ID,
     "reference_month": (now - timedelta(days=30)).strftime("%Y-%m"), "total_amount": 14230.00,
     "minimum_payment": 2134.50, "due_date": ts(now - timedelta(days=20)), "status": "paid"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  INVESTMENTS: Gabriel has idle cash in a taxable CD (the NBO hook)
# ═══════════════════════════════════════════════════════════════════════════
INVESTMENTS = [
    {"investment_id": "INV_CD", "customer_id": DEMO_USER_ID, "product": "CD",
     "description": "Bradesco 12-month Certificate of Deposit, taxable interest, no-penalty",
     "amount_invested": 180000.00,
     "apy_pct": 4.50, "maturity_date": ts(now + timedelta(days=400)), "liquidity": "daily"},
    {"investment_id": "INV_FUND", "customer_id": DEMO_USER_ID, "product": "MutualFund",
     "description": "Bradesco Fixed Income Fund", "amount_invested": 40000.00,
     "apy_pct": 4.25, "maturity_date": ts(now + timedelta(days=180)), "liquidity": "T_plus_30"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ZELLE CONTACTS
# ═══════════════════════════════════════════════════════════════════════════
ZELLE_CONTACTS = [
    {"contact_id": "ZELLE_CARLOS", "customer_id": DEMO_USER_ID, "name": "Carlos Souza",
     "zelle_handle": "+1 (512) 555-2002", "handle_type": "phone", "bank": "Chase", "is_frequent": "yes"},
    {"contact_id": "ZELLE_EMMA", "customer_id": DEMO_USER_ID, "name": "Aunt Emma Cerioni",
     "zelle_handle": "emma.***@email.com", "handle_type": "email", "bank": "Bank of America", "is_frequent": "yes"},
    {"contact_id": "ZELLE_SOFIA", "customer_id": DEMO_USER_ID, "name": "Sofia Cerioni",
     "zelle_handle": "+1 (214) 555-0111", "handle_type": "phone", "bank": "Wells Fargo", "is_frequent": "yes"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES
# ═══════════════════════════════════════════════════════════════════════════
DISPUTES = [
    {"dispute_id": "DSP_HIST", "customer_id": DEMO_USER_ID, "transaction_id": None,
     "reason": "Duplicate subscription charge, resolved in 2025", "amount": 49.90,
     "status": "upheld", "date": ts(now - timedelta(days=120))},
]

# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE: Gabriel's online features (the heart of the differentiator)
#  Calibrated: high investment propensity + idle cash => NBO = munis/retirement
# ═══════════════════════════════════════════════════════════════════════════
FEATURE_STORE = [
    {
        "customer_id": DEMO_USER_ID,
        "monthly_income": 45000.00,
        "internal_score": 920,
        "card_utilization_pct": 22,
        "tenure_months": 132,
        "spend_velocity_30d": 28500.00,
        "avg_balance_3m": 88000.00,
        "num_products": 4,
        "investment_propensity": 0.88,
        "credit_propensity": 0.31,
        "insurance_propensity": 0.64,
        "digital_profile": "high",
        "last_updated": ts(now - timedelta(minutes=8)),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10): Bradesco help/policies, embedded at generation time
# ═══════════════════════════════════════════════════════════════════════════
POLICIES_TEXT = [
    {"policy_id": "POL_ZELLE", "title": "Zelle transfer limits by time of day", "category": "limits",
     "content": "Bradesco Zelle limits by time of day. During the day, from 6 AM to 8 PM, the limit is "
                "$10,000 per transfer. At night, from 8 PM to 6 AM, the nighttime limit drops to $1,000 "
                "per transfer for security. Prime customers can request extended limits. Zelle between "
                "Bradesco accounts is instant and free."},
    {"policy_id": "POL_DISPUTE", "title": "Disputing charges", "category": "dispute",
     "content": "To dispute a charge: confirm you do not recognize the transaction, open the dispute in "
                "the app or with BIA, and the amount goes under review with a provisional credit in "
                "eligible cases. Resolution within 7 business days, with a case number. A recognized "
                "recurring charge (a subscription) tends to be reviewed as not eligible, so confirm "
                "before filing."},
    {"policy_id": "POL_CARD", "title": "Bradesco cards and annual fees", "category": "card",
     "content": "The Visa Infinite and other Bradesco premium cards have an annual fee that can be waived "
                "based on your investments and spending. You can track your statement, adjust your limit, "
                "and lock the card in the app. Credit limit increases go through a score and relationship "
                "review."},
    {"policy_id": "POL_INVEST", "title": "Bradesco investments", "category": "investment",
     "content": "Bradesco offers CDs, municipal bonds, Treasuries, mutual funds, and retirement accounts "
                "(Traditional and Roth IRA). Municipal bonds are exempt from federal income tax, a great "
                "fit for anyone with idle cash sitting in a taxable CD. Traditional IRA contributions may "
                "be tax deductible for those who itemize eligible retirement savings. The recommendation "
                "depends on your investor profile and your goal."},
    {"policy_id": "POL_PRIME", "title": "Bradesco Prime benefits", "category": "prime",
     "content": "Bradesco Prime offers a dedicated relationship manager, airport VIP lounges, investment "
                "advisory, premium cards with preferred annual fee terms, and special credit conditions. "
                "Prime service has priority and exclusive channels."},
    {"policy_id": "POL_SECURITY", "title": "Security and Zelle scams", "category": "security",
     "content": "Be suspicious of newly registered Zelle recipients, urgent requests, and prize offers. "
                "Zelle payments are like cash and usually cannot be reversed. Bradesco flags transactions "
                "with atypical patterns. If you were scammed or suspect unauthorized access, lock your "
                "card, change your password, and file a report. BIA never asks for your password."},
    {"policy_id": "POL_RETIREMENT", "title": "Retirement accounts (IRA)", "category": "investment",
     "content": "Bradesco retirement accounts (Traditional and Roth IRA) are built for long-term goals "
                "and estate planning. Traditional IRA contributions may be deducted from your taxable "
                "income up to the annual IRS limit. A Roth IRA is funded with after-tax dollars and grows "
                "tax free, better for those who expect higher taxes later. Rollovers between plans carry "
                "no cost."},
    {"policy_id": "POL_INSURANCE", "title": "Bradesco insurance", "category": "investment",
     "content": "Bradesco Insurance offers life, home, travel, and card protection coverage. Prime "
                "customers get expanded coverage and premium assistance services. You can enroll in the "
                "app and adjust coverage to your profile."},
    {"policy_id": "POL_PRIVACY", "title": "Privacy and data protection", "category": "privacy",
     "content": "Your data is protected under US financial privacy regulations, including the "
                "Gramm-Leach-Bliley Act. Bradesco does not share your history with third parties without "
                "consent. You can view, export, or request deletion of your data through official "
                "channels."},
    {"policy_id": "POL_WORLDCUP", "title": "World Cup 2026 in Dallas: card perks and game day tips", "category": "card",
     "content": "The 2026 FIFA World Cup is being played in the United States, and Dallas is a host "
                "city: AT&T Stadium in Arlington hosts nine matches, including a semifinal. Going to a "
                "match? Set a travel notice in the app (dates and destination) to avoid a preventive "
                "block while you travel. The stadium is fully cashless, so use your credit card or "
                "contactless wallet instead of debit, for security and purchase protection. Prime "
                "customers have premium cards with travel insurance included (medical and baggage "
                "coverage) and access to airport VIP lounges, and can request a temporary credit limit "
                "increase for the trip. Buy tickets only through official FIFA channels, and never pay "
                "an unknown reseller with Zelle: those payments are like cash. If you follow the "
                "tournament to matches in Mexico or Canada, enable international purchases in the app "
                "and always pay in local currency, never in dollars, to avoid the merchant's bad "
                "exchange rate."},
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
    write_jsonl(resolved_output_dir, "zelle_contacts.jsonl", ZELLE_CONTACTS)
    write_jsonl(resolved_output_dir, "disputes.jsonl", DISPUTES)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nDemo user: {demo['name']} ({demo['customer_id']})")
    print("Done.")

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
            "investments": len(INVESTMENTS),
            "zelle_contacts": len(ZELLE_CONTACTS),
            "disputes": len(DISPUTES),
            "feature_store": len(FEATURE_STORE),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
