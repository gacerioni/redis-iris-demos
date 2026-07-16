"""Bradesco EN, data model definitions (single source of truth).

Premium bank (Prime segment) with the feature store differentiator: the
FeatureStore entity holds online features in Redis that the next-best-offer
model reads in real time. Each EntitySpec governs:
  - ContextModel generation
  - Redis Search index creation via the Context Retriever
  - Synthetic data generation
"""

from __future__ import annotations

from backend.app.core.domain_schema import (
    EntitySpec,
    FieldSpec,
    RelationshipSpec,
    entity_by_class,
    entity_by_file,
)


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    # -- Customer (Bradesco Prime customer) ----------------------
    EntitySpec(
        class_name="Customer",
        redis_key_template="bradesco_en_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Unique customer identifier", is_key_component=True),
            FieldSpec("name", "str", "Full name", index="text", weight=2.0),
            FieldSpec("ssn_masked", "str", "Masked SSN"),
            FieldSpec("email", "str", "Registered email", index="text", weight=1.5, no_stem=True),
            FieldSpec("city", "str", "City", index="tag"),
            FieldSpec("segment", "str", "Segment: retail, exclusive, prime, private", index="tag"),
            FieldSpec("branch", "str", "Branch number"),
            FieldSpec("account_number", "str", "Masked account number"),
            FieldSpec("customer_since_years", "int", "Years of relationship", index="numeric", sortable=True),
            FieldSpec("monthly_income", "float", "Declared monthly income (USD)", index="numeric", sortable=True),
            FieldSpec("internal_score", "int", "Internal Bradesco score (0-1000)", index="numeric", sortable=True),
            FieldSpec("investor_profile", "str", "Profile: conservative, moderate, aggressive", index="tag"),
        ),
        relationships=(
            RelationshipSpec("accounts", "Customer accounts", "customer_id", "list[Account]"),
            RelationshipSpec("cards", "Customer cards", "customer_id", "list[Card]"),
            RelationshipSpec("features", "Customer online features", "customer_id", "FeatureStore"),
        ),
    ),
    # -- Account -------------------------------------------------
    EntitySpec(
        class_name="Account",
        redis_key_template="bradesco_en_account:{account_id}",
        file_name="accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Unique account identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer who owns the account", index="tag"),
            FieldSpec("type", "str", "Type: checking, savings, investment", index="tag"),
            FieldSpec("balance", "float", "Current balance (USD)", index="numeric", sortable=True),
            FieldSpec("overdraft_limit", "float", "Overdraft protection limit (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: active, blocked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Customer", "customer_id", "Customer"),
        ),
    ),
    # -- Card ------------------------------------------------------
    EntitySpec(
        class_name="Card",
        redis_key_template="bradesco_en_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Unique card identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer who owns the card", index="tag"),
            FieldSpec("product", "str", "Product: Visa Infinite, Mastercard Black, etc.", index="text"),
            FieldSpec("type", "str", "Type: credit, debit", index="tag"),
            FieldSpec("network", "str", "Network: visa, mastercard, amex", index="tag"),
            FieldSpec("last4", "str", "Last 4 digits"),
            FieldSpec("credit_limit", "float", "Credit limit (USD)", index="numeric", sortable=True),
            FieldSpec("current_statement", "float", "Current open statement balance (USD)", index="numeric", sortable=True),
            FieldSpec("due_date", "str", "Statement due date (ISO)", sortable=True),
            FieldSpec("annual_fee", "float", "Annual fee (USD, 0 if waived)", index="numeric"),
            FieldSpec("status", "str", "Status: active, locked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Customer", "customer_id", "Customer"),
        ),
    ),
    # -- Transaction -----------------------------------------------
    EntitySpec(
        class_name="Transaction",
        redis_key_template="bradesco_en_transaction:{txn_id}",
        file_name="transactions.jsonl",
        id_field="txn_id",
        fields=(
            FieldSpec("txn_id", "str", "Unique transaction identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer", index="tag"),
            FieldSpec("card_id", "str | None", "Card used (if purchase)", index="tag"),
            FieldSpec("account_id", "str | None", "Account (if debit/Zelle)", index="tag"),
            FieldSpec("type", "str", "Type: credit_purchase, debit_purchase, zelle_sent, zelle_received, cashback", index="tag"),
            FieldSpec("merchant", "str", "Merchant/counterparty", index="text", weight=1.5),
            FieldSpec("mcc", "str", "Category (MCC)", index="tag"),
            FieldSpec("amount", "float", "Total transaction amount (USD)", index="numeric", sortable=True),
            FieldSpec("date", "str", "ISO timestamp", sortable=True),
            FieldSpec("is_recurring", "str", "Recurring: yes, no", index="tag"),
            FieldSpec("installment_current", "int", "Current installment (1 if paid in full)", index="numeric"),
            FieldSpec("installment_total", "int", "Total installments in the payment plan (1 if paid in full)", index="numeric", sortable=True),
            FieldSpec("installment_amount", "float", "Amount of each installment (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: approved, pending, disputed", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Customer", "customer_id", "Customer"),
        ),
    ),
    # -- BillingCycle (card statement) -----------------------------
    EntitySpec(
        class_name="BillingCycle",
        redis_key_template="bradesco_en_billing_cycle:{cycle_id}",
        file_name="billing_cycles.jsonl",
        id_field="cycle_id",
        fields=(
            FieldSpec("cycle_id", "str", "Unique statement identifier", is_key_component=True),
            FieldSpec("card_id", "str", "Card", index="tag"),
            FieldSpec("customer_id", "str", "Customer", index="tag"),
            FieldSpec("reference_month", "str", "Reference month (YYYY-MM)", index="tag", sortable=True),
            FieldSpec("total_amount", "float", "Total statement amount (USD)", index="numeric", sortable=True),
            FieldSpec("minimum_payment", "float", "Minimum payment (USD)", index="numeric"),
            FieldSpec("due_date", "str", "Statement due date (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: open, closed, paid, overdue", index="tag"),
        ),
    ),
    # -- Investment ------------------------------------------------
    EntitySpec(
        class_name="Investment",
        redis_key_template="bradesco_en_investment:{investment_id}",
        file_name="investments.jsonl",
        id_field="investment_id",
        fields=(
            FieldSpec("investment_id", "str", "Unique investment identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer", index="tag"),
            FieldSpec("product", "str", "Product: CD, MunicipalBond, Treasury, MutualFund, IRA", index="tag"),
            FieldSpec("description", "str", "Investment description", index="text"),
            FieldSpec("amount_invested", "float", "Amount invested (USD)", index="numeric", sortable=True),
            FieldSpec("apy_pct", "float", "Yield (% APY)", index="numeric"),
            FieldSpec("maturity_date", "str", "Maturity date (ISO)", sortable=True),
            FieldSpec("liquidity", "str", "Liquidity: daily, at_maturity, T_plus_30", index="tag"),
        ),
    ),
    # -- ZelleContact ----------------------------------------------
    EntitySpec(
        class_name="ZelleContact",
        redis_key_template="bradesco_en_zelle_contact:{contact_id}",
        file_name="zelle_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Unique contact identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer who owns the contact list", index="tag"),
            FieldSpec("name", "str", "Contact name", index="text", weight=2.0),
            FieldSpec("zelle_handle", "str", "Masked Zelle handle (phone or email)"),
            FieldSpec("handle_type", "str", "Type: phone, email", index="tag"),
            FieldSpec("bank", "str", "Contact's bank", index="text"),
            FieldSpec("is_frequent", "str", "Frequent contact: yes, no", index="tag"),
        ),
    ),
    # -- Dispute ---------------------------------------------------
    EntitySpec(
        class_name="Dispute",
        redis_key_template="bradesco_en_dispute:{dispute_id}",
        file_name="disputes.jsonl",
        id_field="dispute_id",
        fields=(
            FieldSpec("dispute_id", "str", "Unique dispute identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer", index="tag"),
            FieldSpec("transaction_id", "str | None", "Disputed transaction", index="tag"),
            FieldSpec("reason", "str", "Reason", index="text"),
            FieldSpec("amount", "float", "Disputed amount (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: open, in_review, upheld, denied", index="tag"),
            FieldSpec("date", "str", "ISO timestamp", sortable=True),
        ),
    ),
    # -- FeatureStore (online features for the recommendation model) --
    # This entity is the heart of the differentiator: online features in Redis
    # that the next-best-offer model reads in real time (sub-ms).
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="bradesco_en_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Customer (feature row key)", is_key_component=True),
            FieldSpec("monthly_income", "float", "Feature: monthly income (USD)", index="numeric", sortable=True),
            FieldSpec("internal_score", "int", "Feature: internal score (0-1000)", index="numeric", sortable=True),
            FieldSpec("card_utilization_pct", "int", "Feature: % of credit limit utilized", index="numeric"),
            FieldSpec("tenure_months", "int", "Feature: months of relationship", index="numeric"),
            FieldSpec("spend_velocity_30d", "float", "Feature: spend over the last 30 days (USD)", index="numeric", sortable=True),
            FieldSpec("avg_balance_3m", "float", "Feature: average balance over the last 3 months (USD)", index="numeric"),
            FieldSpec("num_products", "int", "Feature: number of products held", index="numeric"),
            FieldSpec("investment_propensity", "float", "Feature: propensity to invest (0-1)", index="numeric", sortable=True),
            FieldSpec("credit_propensity", "float", "Feature: propensity to take credit (0-1)", index="numeric"),
            FieldSpec("insurance_propensity", "float", "Feature: propensity to buy insurance/retirement (0-1)", index="numeric"),
            FieldSpec("digital_profile", "str", "Feature: digital engagement: high, medium, low", index="tag"),
            FieldSpec("last_updated", "str", "Timestamp of the last feature update (ISO)", sortable=True),
        ),
        relationships=(
            RelationshipSpec("customer", "Customer who owns the features", "customer_id", "Customer"),
        ),
    ),
    # -- Policy (Bradesco policies / help) -------------------------
    EntitySpec(
        class_name="Policy",
        redis_key_template="bradesco_en_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Unique policy identifier", is_key_component=True),
            FieldSpec("title", "str", "Policy title", index="text", weight=2.0),
            FieldSpec("category", "str", "Category: zelle, dispute, card, investment, security, prime, limits, privacy", index="tag"),
            FieldSpec("content", "str", "Full policy text", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Vector embedding",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
