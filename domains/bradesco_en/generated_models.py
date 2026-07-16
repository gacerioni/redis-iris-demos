"""Generated Context Surface models for the Bradesco domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Unique customer identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Full name",
        index="text",
        weight=2.0,
    )

    ssn_masked: str = ContextField(
        description="Masked SSN",
    )

    email: str = ContextField(
        description="Registered email",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    city: str = ContextField(
        description="City",
        index="tag",
    )

    segment: str = ContextField(
        description="Segment: retail, exclusive, prime, private",
        index="tag",
    )

    branch: str = ContextField(
        description="Branch number",
    )

    account_number: str = ContextField(
        description="Masked account number",
    )

    customer_since_years: int = ContextField(
        description="Years of relationship",
        index="numeric",
        sortable=True,
    )

    monthly_income: float = ContextField(
        description="Declared monthly income (USD)",
        index="numeric",
        sortable=True,
    )

    internal_score: int = ContextField(
        description="Internal Bradesco score (0-1000)",
        index="numeric",
        sortable=True,
    )

    investor_profile: str = ContextField(
        description="Profile: conservative, moderate, aggressive",
        index="tag",
    )

    accounts: Any = ContextRelationship(
        description="Customer accounts",
        target="Account",
        source_field="customer_id",
    )

    cards: Any = ContextRelationship(
        description="Customer cards",
        target="Card",
        source_field="customer_id",
    )

    features: Any = ContextRelationship(
        description="Customer online features",
        target="FeatureStore",
        source_field="customer_id",
    )


class Account(ContextModel):
    """Account entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_account:{account_id}"

    account_id: str = ContextField(
        description="Unique account identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer who owns the account",
        index="tag",
    )

    type: str = ContextField(
        description="Type: checking, savings, investment",
        index="tag",
    )

    balance: float = ContextField(
        description="Current balance (USD)",
        index="numeric",
        sortable=True,
    )

    overdraft_limit: float = ContextField(
        description="Overdraft protection limit (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: active, blocked",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Customer",
        target="Customer",
        source_field="customer_id",
    )


class Card(ContextModel):
    """Card entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_card:{card_id}"

    card_id: str = ContextField(
        description="Unique card identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer who owns the card",
        index="tag",
    )

    product: str = ContextField(
        description="Product: Visa Infinite, Mastercard Black, etc.",
        index="text",
    )

    type: str = ContextField(
        description="Type: credit, debit",
        index="tag",
    )

    network: str = ContextField(
        description="Network: visa, mastercard, amex",
        index="tag",
    )

    last4: str = ContextField(
        description="Last 4 digits",
    )

    credit_limit: float = ContextField(
        description="Credit limit (USD)",
        index="numeric",
        sortable=True,
    )

    current_statement: float = ContextField(
        description="Current open statement balance (USD)",
        index="numeric",
        sortable=True,
    )

    due_date: str = ContextField(
        description="Statement due date (ISO)",
        sortable=True,
    )

    annual_fee: float = ContextField(
        description="Annual fee (USD, 0 if waived)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: active, locked",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Customer",
        target="Customer",
        source_field="customer_id",
    )


class Transaction(ContextModel):
    """Transaction entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_transaction:{txn_id}"

    txn_id: str = ContextField(
        description="Unique transaction identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer",
        index="tag",
    )

    card_id: str | None = ContextField(
        description="Card used (if purchase)",
        index="tag",
    )

    account_id: str | None = ContextField(
        description="Account (if debit/Zelle)",
        index="tag",
    )

    type: str = ContextField(
        description="Type: credit_purchase, debit_purchase, zelle_sent, zelle_received, cashback",
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

    amount: float = ContextField(
        description="Total transaction amount (USD)",
        index="numeric",
        sortable=True,
    )

    date: str = ContextField(
        description="ISO timestamp",
        sortable=True,
    )

    is_recurring: str = ContextField(
        description="Recurring: yes, no",
        index="tag",
    )

    installment_current: int = ContextField(
        description="Current installment (1 if paid in full)",
        index="numeric",
    )

    installment_total: int = ContextField(
        description="Total installments in the payment plan (1 if paid in full)",
        index="numeric",
        sortable=True,
    )

    installment_amount: float = ContextField(
        description="Amount of each installment (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: approved, pending, disputed",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Customer",
        target="Customer",
        source_field="customer_id",
    )


class BillingCycle(ContextModel):
    """BillingCycle entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_billing_cycle:{cycle_id}"

    cycle_id: str = ContextField(
        description="Unique statement identifier",
        is_key_component=True,
    )

    card_id: str = ContextField(
        description="Card",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Customer",
        index="tag",
    )

    reference_month: str = ContextField(
        description="Reference month (YYYY-MM)",
        index="tag",
        sortable=True,
    )

    total_amount: float = ContextField(
        description="Total statement amount (USD)",
        index="numeric",
        sortable=True,
    )

    minimum_payment: float = ContextField(
        description="Minimum payment (USD)",
        index="numeric",
    )

    due_date: str = ContextField(
        description="Statement due date (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: open, closed, paid, overdue",
        index="tag",
    )


class Investment(ContextModel):
    """Investment entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_investment:{investment_id}"

    investment_id: str = ContextField(
        description="Unique investment identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer",
        index="tag",
    )

    product: str = ContextField(
        description="Product: CD, MunicipalBond, Treasury, MutualFund, IRA",
        index="tag",
    )

    description: str = ContextField(
        description="Investment description",
        index="text",
    )

    amount_invested: float = ContextField(
        description="Amount invested (USD)",
        index="numeric",
        sortable=True,
    )

    apy_pct: float = ContextField(
        description="Yield (% APY)",
        index="numeric",
    )

    maturity_date: str = ContextField(
        description="Maturity date (ISO)",
        sortable=True,
    )

    liquidity: str = ContextField(
        description="Liquidity: daily, at_maturity, T_plus_30",
        index="tag",
    )


class ZelleContact(ContextModel):
    """ZelleContact entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_zelle_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Unique contact identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer who owns the contact list",
        index="tag",
    )

    name: str = ContextField(
        description="Contact name",
        index="text",
        weight=2.0,
    )

    zelle_handle: str = ContextField(
        description="Masked Zelle handle (phone or email)",
    )

    handle_type: str = ContextField(
        description="Type: phone, email",
        index="tag",
    )

    bank: str = ContextField(
        description="Contact's bank",
        index="text",
    )

    is_frequent: str = ContextField(
        description="Frequent contact: yes, no",
        index="tag",
    )


class Dispute(ContextModel):
    """Dispute entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_dispute:{dispute_id}"

    dispute_id: str = ContextField(
        description="Unique dispute identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer",
        index="tag",
    )

    transaction_id: str | None = ContextField(
        description="Disputed transaction",
        index="tag",
    )

    reason: str = ContextField(
        description="Reason",
        index="text",
    )

    amount: float = ContextField(
        description="Disputed amount (USD)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: open, in_review, upheld, denied",
        index="tag",
    )

    date: str = ContextField(
        description="ISO timestamp",
        sortable=True,
    )


class FeatureStore(ContextModel):
    """FeatureStore entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_features:{customer_id}"

    customer_id: str = ContextField(
        description="Customer (feature row key)",
        is_key_component=True,
    )

    monthly_income: float = ContextField(
        description="Feature: monthly income (USD)",
        index="numeric",
        sortable=True,
    )

    internal_score: int = ContextField(
        description="Feature: internal score (0-1000)",
        index="numeric",
        sortable=True,
    )

    card_utilization_pct: int = ContextField(
        description="Feature: % of credit limit utilized",
        index="numeric",
    )

    tenure_months: int = ContextField(
        description="Feature: months of relationship",
        index="numeric",
    )

    spend_velocity_30d: float = ContextField(
        description="Feature: spend over the last 30 days (USD)",
        index="numeric",
        sortable=True,
    )

    avg_balance_3m: float = ContextField(
        description="Feature: average balance over the last 3 months (USD)",
        index="numeric",
    )

    num_products: int = ContextField(
        description="Feature: number of products held",
        index="numeric",
    )

    investment_propensity: float = ContextField(
        description="Feature: propensity to invest (0-1)",
        index="numeric",
        sortable=True,
    )

    credit_propensity: float = ContextField(
        description="Feature: propensity to take credit (0-1)",
        index="numeric",
    )

    insurance_propensity: float = ContextField(
        description="Feature: propensity to buy insurance/retirement (0-1)",
        index="numeric",
    )

    digital_profile: str = ContextField(
        description="Feature: digital engagement: high, medium, low",
        index="tag",
    )

    last_updated: str = ContextField(
        description="Timestamp of the last feature update (ISO)",
        sortable=True,
    )

    customer: Any = ContextRelationship(
        description="Customer who owns the features",
        target="Customer",
        source_field="customer_id",
    )


class Policy(ContextModel):
    """Policy entity for the Bradesco domain."""

    __redis_key_template__ = "bradesco_en_policy:{policy_id}"

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
        description="Category: zelle, dispute, card, investment, security, prime, limits, privacy",
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
