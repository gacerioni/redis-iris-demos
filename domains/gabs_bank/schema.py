"""Gabs Bank (Ava) — data model definitions (single source of truth).

Digital bank (Premier segment) with the feature-store differentiator: the
FeatureStore entity holds online features in Redis that the next-best-offer model
reads in real time. Each EntitySpec governs:
  • ContextModel generation
  • Redis Search index creation via the Context Retriever
  • Synthetic data generation
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
    # ── Customer (Gabs Bank Premier client) ───────────────────────
    EntitySpec(
        class_name="Customer",
        redis_key_template="gabs_bank_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Unique client identifier", is_key_component=True),
            FieldSpec("nome", "str", "Full name", index="text", weight=2.0),
            FieldSpec("cpf_masked", "str", "Masked tax ID"),
            FieldSpec("email", "str", "Registered email", index="text", weight=1.5, no_stem=True),
            FieldSpec("cidade", "str", "City", index="tag"),
            FieldSpec("segmento", "str", "Segment: retail, premier, private", index="tag"),
            FieldSpec("agencia", "str", "Branch number"),
            FieldSpec("conta", "str", "Masked account number"),
            FieldSpec("cliente_desde_anos", "int", "Years as a client", index="numeric", sortable=True),
            FieldSpec("renda_mensal", "float", "Declared monthly income (USD)", index="numeric", sortable=True),
            FieldSpec("score_interno", "int", "Internal Gabs Bank score (0-1000)", index="numeric", sortable=True),
            FieldSpec("perfil_investidor", "str", "Profile: conservative, moderate, aggressive", index="tag"),
        ),
        relationships=(
            RelationshipSpec("accounts", "Client accounts", "customer_id", "list[Account]"),
            RelationshipSpec("cards", "Client cards", "customer_id", "list[Card]"),
            RelationshipSpec("features", "Client online features", "customer_id", "FeatureStore"),
        ),
    ),
    # ── Account ───────────────────────────────────────────────────
    EntitySpec(
        class_name="Account",
        redis_key_template="gabs_bank_account:{account_id}",
        file_name="accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Unique account identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Account owner", index="tag"),
            FieldSpec("tipo", "str", "Type: checking, savings, brokerage", index="tag"),
            FieldSpec("saldo", "float", "Current balance (USD)", index="numeric", sortable=True),
            FieldSpec("limite_cheque_especial", "float", "Overdraft limit (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: active, blocked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Client", "customer_id", "Customer"),
        ),
    ),
    # ── Card ──────────────────────────────────────────────────────
    EntitySpec(
        class_name="Card",
        redis_key_template="gabs_bank_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Unique card identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Card owner", index="tag"),
            FieldSpec("produto", "str", "Product: Gabs Black, Gabs Debit, Mastercard Black, etc.", index="text"),
            FieldSpec("tipo", "str", "Type: credit, debit", index="tag"),
            FieldSpec("bandeira", "str", "Network: visa, mastercard, amex", index="tag"),
            FieldSpec("final", "str", "Last 4 digits"),
            FieldSpec("limite", "float", "Credit limit (USD)", index="numeric", sortable=True),
            FieldSpec("fatura_atual", "float", "Current open statement (USD)", index="numeric", sortable=True),
            FieldSpec("vencimento", "str", "Statement due date (ISO)", sortable=True),
            FieldSpec("anuidade", "float", "Annual fee (USD, 0 if waived)", index="numeric"),
            FieldSpec("status", "str", "Status: active, blocked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Client", "customer_id", "Customer"),
        ),
    ),
    # ── Transaction ─────────────────────────────────────────────
    EntitySpec(
        class_name="Transaction",
        redis_key_template="gabs_bank_transaction:{txn_id}",
        file_name="transactions.jsonl",
        id_field="txn_id",
        fields=(
            FieldSpec("txn_id", "str", "Unique transaction identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Client", index="tag"),
            FieldSpec("card_id", "str | None", "Card used (if a purchase)", index="tag"),
            FieldSpec("account_id", "str | None", "Account (if debit/transfer)", index="tag"),
            FieldSpec("tipo", "str", "Type: credit_purchase, debit_purchase, transfer_out, transfer_in, cashback", index="tag"),
            FieldSpec("merchant", "str", "Merchant/counterparty", index="text", weight=1.5),
            FieldSpec("mcc", "str", "Category (MCC)", index="tag"),
            FieldSpec("valor", "float", "Total transaction amount (USD)", index="numeric", sortable=True),
            FieldSpec("data", "str", "ISO timestamp", sortable=True),
            FieldSpec("is_recurring", "str", "Recurring: yes, no", index="tag"),
            FieldSpec("parcela_atual", "int", "Current installment (1 if one-off)", index="numeric"),
            FieldSpec("parcela_total", "int", "Total installments (1 if one-off)", index="numeric", sortable=True),
            FieldSpec("valor_parcela", "float", "Amount per installment (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: approved, pending, disputed", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Client", "customer_id", "Customer"),
        ),
    ),
    # ── BillingCycle (statement) ─────────────────────────────────
    EntitySpec(
        class_name="BillingCycle",
        redis_key_template="gabs_bank_billing_cycle:{cycle_id}",
        file_name="billing_cycles.jsonl",
        id_field="cycle_id",
        fields=(
            FieldSpec("cycle_id", "str", "Unique statement identifier", is_key_component=True),
            FieldSpec("card_id", "str", "Card", index="tag"),
            FieldSpec("customer_id", "str", "Client", index="tag"),
            FieldSpec("mes_referencia", "str", "Reference month (YYYY-MM)", index="tag", sortable=True),
            FieldSpec("valor_total", "float", "Statement total (USD)", index="numeric", sortable=True),
            FieldSpec("valor_minimo", "float", "Minimum payment (USD)", index="numeric"),
            FieldSpec("vencimento", "str", "Statement due date (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: open, closed, paid, late", index="tag"),
        ),
    ),
    # ── Investment (positions) ───────────────────────────────────
    EntitySpec(
        class_name="Investment",
        redis_key_template="gabs_bank_investment:{investment_id}",
        file_name="investments.jsonl",
        id_field="investment_id",
        fields=(
            FieldSpec("investment_id", "str", "Unique position identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Client", index="tag"),
            FieldSpec("produto", "str", "Product: Money Market, CD, Treasury, Fund, Municipal Bonds, Retirement", index="tag"),
            FieldSpec("descricao", "str", "Position description", index="text"),
            FieldSpec("valor_aplicado", "float", "Amount invested (USD)", index="numeric", sortable=True),
            FieldSpec("rentabilidade_cdi_pct", "int", "Yield (% of benchmark rate)", index="numeric"),
            FieldSpec("vencimento", "str", "Maturity (ISO)", sortable=True),
            FieldSpec("liquidez", "str", "Liquidity: daily, at_maturity, T_plus_30", index="tag"),
        ),
    ),
    # ── PixContact (transfer contact) ────────────────────────────
    EntitySpec(
        class_name="PixContact",
        redis_key_template="gabs_bank_pix_contact:{contact_id}",
        file_name="pix_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Unique contact identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Address-book owner", index="tag"),
            FieldSpec("nome", "str", "Contact name", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Masked transfer key"),
            FieldSpec("tipo_chave", "str", "Key type: account, email, phone, random", index="tag"),
            FieldSpec("banco", "str", "Contact's bank", index="text"),
            FieldSpec("is_frequente", "str", "Frequent contact: yes, no", index="tag"),
        ),
    ),
    # ── Dispute ──────────────────────────────────────────────────
    EntitySpec(
        class_name="Dispute",
        redis_key_template="gabs_bank_dispute:{dispute_id}",
        file_name="disputes.jsonl",
        id_field="dispute_id",
        fields=(
            FieldSpec("dispute_id", "str", "Unique dispute identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Client", index="tag"),
            FieldSpec("transaction_id", "str | None", "Disputed transaction", index="tag"),
            FieldSpec("motivo", "str", "Reason", index="text"),
            FieldSpec("valor", "float", "Disputed amount (USD)", index="numeric"),
            FieldSpec("status", "str", "Status: open, in_review, upheld, denied", index="tag"),
            FieldSpec("data", "str", "ISO timestamp", sortable=True),
        ),
    ),
    # ── FeatureStore (online features for the recommendation model) ─
    # This entity is the heart of the differentiator: online features in Redis that
    # the next-best-offer model reads in real time (sub-ms).
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="gabs_bank_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Client (feature-row key)", is_key_component=True),
            FieldSpec("renda_mensal", "float", "Feature: monthly income (USD)", index="numeric", sortable=True),
            FieldSpec("score_interno", "int", "Feature: internal score (0-1000)", index="numeric", sortable=True),
            FieldSpec("utilizacao_cartao_pct", "int", "Feature: % of card limit used", index="numeric"),
            FieldSpec("tenure_meses", "int", "Feature: months as a client", index="numeric"),
            FieldSpec("velocity_gasto_30d", "float", "Feature: spend over the last 30 days (USD)", index="numeric", sortable=True),
            FieldSpec("saldo_medio_3m", "float", "Feature: average balance over the last 3 months (USD)", index="numeric"),
            FieldSpec("num_produtos", "int", "Feature: number of products held", index="numeric"),
            FieldSpec("propensao_investimento", "float", "Feature: propensity to invest (0-1)", index="numeric", sortable=True),
            FieldSpec("propensao_credito", "float", "Feature: propensity for credit (0-1)", index="numeric"),
            FieldSpec("propensao_seguro", "float", "Feature: propensity for insurance/retirement (0-1)", index="numeric"),
            FieldSpec("perfil_digital", "str", "Feature: digital engagement: high, medium, low", index="tag"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp of the last feature update (ISO)", sortable=True),
        ),
        relationships=(
            RelationshipSpec("customer", "Owner of the features", "customer_id", "Customer"),
        ),
    ),
    # ── Policy (Gabs Bank policy / help docs) ────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="gabs_bank_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Unique policy identifier", is_key_component=True),
            FieldSpec("title", "str", "Policy title", index="text", weight=2.0),
            FieldSpec("category", "str", "Category: limits, dispute, card, investment, premier, security, cashback, privacy", index="tag"),
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
