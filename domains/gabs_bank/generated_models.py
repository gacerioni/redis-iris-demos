"""Generated Context Surface models for the Gabs Bank domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Unique client identifier",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Full name",
        index="text",
        weight=2.0,
    )

    cpf_masked: str = ContextField(
        description="Masked tax ID",
    )

    email: str = ContextField(
        description="Registered email",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    cidade: str = ContextField(
        description="City",
        index="tag",
    )

    segmento: str = ContextField(
        description="Segment: retail, premier, private",
        index="tag",
    )

    agencia: str = ContextField(
        description="Branch number",
    )

    conta: str = ContextField(
        description="Masked account number",
    )

    cliente_desde_anos: int = ContextField(
        description="Years as a client",
        index="numeric",
        sortable=True,
    )

    renda_mensal: float = ContextField(
        description="Declared monthly income (USD)",
        index="numeric",
        sortable=True,
    )

    score_interno: int = ContextField(
        description="Internal Gabs Bank score (0-1000)",
        index="numeric",
        sortable=True,
    )

    perfil_investidor: str = ContextField(
        description="Profile: conservative, moderate, aggressive",
        index="tag",
    )

    accounts: Any = ContextRelationship(
        description="Client accounts",
        target="Account",
        source_field="customer_id",
    )

    cards: Any = ContextRelationship(
        description="Client cards",
        target="Card",
        source_field="customer_id",
    )

    features: Any = ContextRelationship(
        description="Client online features",
        target="FeatureStore",
        source_field="customer_id",
    )


class Account(ContextModel):
    """Account entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_account:{account_id}"

    account_id: str = ContextField(
        description="Unique account identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Account owner",
        index="tag",
    )

    tipo: str = ContextField(
        description="Type: checking, savings, brokerage",
        index="tag",
    )

    saldo: float = ContextField(
        description="Current balance (USD)",
        index="numeric",
        sortable=True,
    )

    limite_cheque_especial: float = ContextField(
        description="Overdraft limit (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: active, blocked",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Client",
        target="Customer",
        source_field="customer_id",
    )


class Card(ContextModel):
    """Card entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_card:{card_id}"

    card_id: str = ContextField(
        description="Unique card identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Card owner",
        index="tag",
    )

    produto: str = ContextField(
        description="Product: Gabs Black, Gabs Debit, Mastercard Black, etc.",
        index="text",
    )

    tipo: str = ContextField(
        description="Type: credit, debit",
        index="tag",
    )

    bandeira: str = ContextField(
        description="Network: visa, mastercard, amex",
        index="tag",
    )

    final: str = ContextField(
        description="Last 4 digits",
    )

    limite: float = ContextField(
        description="Credit limit (USD)",
        index="numeric",
        sortable=True,
    )

    fatura_atual: float = ContextField(
        description="Current open statement (USD)",
        index="numeric",
        sortable=True,
    )

    vencimento: str = ContextField(
        description="Statement due date (ISO)",
        sortable=True,
    )

    anuidade: float = ContextField(
        description="Annual fee (USD, 0 if waived)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: active, blocked",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Client",
        target="Customer",
        source_field="customer_id",
    )


class Transaction(ContextModel):
    """Transaction entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_transaction:{txn_id}"

    txn_id: str = ContextField(
        description="Unique transaction identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Client",
        index="tag",
    )

    card_id: str | None = ContextField(
        description="Card used (if a purchase)",
        index="tag",
    )

    account_id: str | None = ContextField(
        description="Account (if debit/transfer)",
        index="tag",
    )

    tipo: str = ContextField(
        description="Type: credit_purchase, debit_purchase, transfer_out, transfer_in, cashback",
        index="tag",
    )

    merchant: str = ContextField(
        description="Merchant/counterparty",
        index="text",
        weight=1.5,
    )

    mcc: str = ContextField(
        description="Category (MCC)",
        index="tag",
    )

    valor: float = ContextField(
        description="Total transaction amount (USD)",
        index="numeric",
        sortable=True,
    )

    data: str = ContextField(
        description="ISO timestamp",
        sortable=True,
    )

    is_recurring: str = ContextField(
        description="Recurring: yes, no",
        index="tag",
    )

    parcela_atual: int = ContextField(
        description="Current installment (1 if one-off)",
        index="numeric",
    )

    parcela_total: int = ContextField(
        description="Total installments (1 if one-off)",
        index="numeric",
        sortable=True,
    )

    valor_parcela: float = ContextField(
        description="Amount per installment (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: approved, pending, disputed",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Client",
        target="Customer",
        source_field="customer_id",
    )


class BillingCycle(ContextModel):
    """BillingCycle entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_billing_cycle:{cycle_id}"

    cycle_id: str = ContextField(
        description="Unique statement identifier",
        is_key_component=True,
    )

    card_id: str = ContextField(
        description="Card",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Client",
        index="tag",
    )

    mes_referencia: str = ContextField(
        description="Reference month (YYYY-MM)",
        index="tag",
        sortable=True,
    )

    valor_total: float = ContextField(
        description="Statement total (USD)",
        index="numeric",
        sortable=True,
    )

    valor_minimo: float = ContextField(
        description="Minimum payment (USD)",
        index="numeric",
    )

    vencimento: str = ContextField(
        description="Statement due date (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: open, closed, paid, late",
        index="tag",
    )


class Investment(ContextModel):
    """Investment entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_investment:{investment_id}"

    investment_id: str = ContextField(
        description="Unique position identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Client",
        index="tag",
    )

    produto: str = ContextField(
        description="Product: Money Market, CD, Treasury, Fund, Municipal Bonds, Retirement",
        index="tag",
    )

    descricao: str = ContextField(
        description="Position description",
        index="text",
    )

    valor_aplicado: float = ContextField(
        description="Amount invested (USD)",
        index="numeric",
        sortable=True,
    )

    rentabilidade_cdi_pct: int = ContextField(
        description="Yield (% of benchmark rate)",
        index="numeric",
    )

    vencimento: str = ContextField(
        description="Maturity (ISO)",
        sortable=True,
    )

    liquidez: str = ContextField(
        description="Liquidity: daily, at_maturity, T_plus_30",
        index="tag",
    )


class PixContact(ContextModel):
    """PixContact entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_pix_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Unique contact identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Address-book owner",
        index="tag",
    )

    nome: str = ContextField(
        description="Contact name",
        index="text",
        weight=2.0,
    )

    chave_pix: str = ContextField(
        description="Masked transfer key",
    )

    tipo_chave: str = ContextField(
        description="Key type: account, email, phone, random",
        index="tag",
    )

    banco: str = ContextField(
        description="Contact's bank",
        index="text",
    )

    is_frequente: str = ContextField(
        description="Frequent contact: yes, no",
        index="tag",
    )


class Dispute(ContextModel):
    """Dispute entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_dispute:{dispute_id}"

    dispute_id: str = ContextField(
        description="Unique dispute identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Client",
        index="tag",
    )

    transaction_id: str | None = ContextField(
        description="Disputed transaction",
        index="tag",
    )

    motivo: str = ContextField(
        description="Reason",
        index="text",
    )

    valor: float = ContextField(
        description="Disputed amount (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: open, in_review, upheld, denied",
        index="tag",
    )

    data: str = ContextField(
        description="ISO timestamp",
        sortable=True,
    )


class FeatureStore(ContextModel):
    """FeatureStore entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_features:{customer_id}"

    customer_id: str = ContextField(
        description="Client (feature-row key)",
        is_key_component=True,
    )

    renda_mensal: float = ContextField(
        description="Feature: monthly income (USD)",
        index="numeric",
        sortable=True,
    )

    score_interno: int = ContextField(
        description="Feature: internal score (0-1000)",
        index="numeric",
        sortable=True,
    )

    utilizacao_cartao_pct: int = ContextField(
        description="Feature: % of card limit used",
        index="numeric",
    )

    tenure_meses: int = ContextField(
        description="Feature: months as a client",
        index="numeric",
    )

    velocity_gasto_30d: float = ContextField(
        description="Feature: spend over the last 30 days (USD)",
        index="numeric",
        sortable=True,
    )

    saldo_medio_3m: float = ContextField(
        description="Feature: average balance over the last 3 months (USD)",
        index="numeric",
    )

    num_produtos: int = ContextField(
        description="Feature: number of products held",
        index="numeric",
    )

    propensao_investimento: float = ContextField(
        description="Feature: propensity to invest (0-1)",
        index="numeric",
        sortable=True,
    )

    propensao_credito: float = ContextField(
        description="Feature: propensity for credit (0-1)",
        index="numeric",
    )

    propensao_seguro: float = ContextField(
        description="Feature: propensity for insurance/retirement (0-1)",
        index="numeric",
    )

    perfil_digital: str = ContextField(
        description="Feature: digital engagement: high, medium, low",
        index="tag",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp of the last feature update (ISO)",
        sortable=True,
    )

    customer: Any = ContextRelationship(
        description="Owner of the features",
        target="Customer",
        source_field="customer_id",
    )


class Policy(ContextModel):
    """Policy entity for the Gabs Bank domain."""

    __redis_key_template__ = "gabs_bank_policy:{policy_id}"

    policy_id: str = ContextField(
        description="Unique policy identifier",
        is_key_component=True,
    )

    title: str = ContextField(
        description="Policy title",
        index="text",
        weight=2.0,
    )

    category: str = ContextField(
        description="Category: limits, dispute, card, investment, premier, security, cashback, privacy",
        index="tag",
    )

    content: str = ContextField(
        description="Full policy text",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
