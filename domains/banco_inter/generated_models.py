"""Generated Context Surface models for the Babi domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Identificador único do cliente",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Nome completo",
        index="text",
        weight=2.0,
    )

    cpf_masked: str = ContextField(
        description="CPF mascarado",
    )

    email: str = ContextField(
        description="Email cadastrado",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    cidade: str = ContextField(
        description="Cidade",
        index="tag",
    )

    segmento: str = ContextField(
        description="Segmento: varejo, inter_one, private",
        index="tag",
    )

    agencia: str = ContextField(
        description="Número da agência",
    )

    conta: str = ContextField(
        description="Número da conta mascarado",
    )

    cliente_desde_anos: int = ContextField(
        description="Anos de relacionamento",
        index="numeric",
        sortable=True,
    )

    renda_mensal: float = ContextField(
        description="Renda mensal declarada (BRL)",
        index="numeric",
        sortable=True,
    )

    score_interno: int = ContextField(
        description="Score interno Inter (0-1000)",
        index="numeric",
        sortable=True,
    )

    perfil_investidor: str = ContextField(
        description="Perfil: conservador, moderado, arrojado",
        index="tag",
    )

    accounts: Any = ContextRelationship(
        description="Contas do cliente",
        target="Account",
        source_field="customer_id",
    )

    cards: Any = ContextRelationship(
        description="Cartões do cliente",
        target="Card",
        source_field="customer_id",
    )

    features: Any = ContextRelationship(
        description="Features online do cliente",
        target="FeatureStore",
        source_field="customer_id",
    )


class Account(ContextModel):
    """Account entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_account:{account_id}"

    account_id: str = ContextField(
        description="Identificador único da conta",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono da conta",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: corrente, poupanca, investimento",
        index="tag",
    )

    saldo: float = ContextField(
        description="Saldo atual (BRL)",
        index="numeric",
        sortable=True,
    )

    limite_cheque_especial: float = ContextField(
        description="Limite do cheque especial (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: ativa, bloqueada",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class Card(ContextModel):
    """Card entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_card:{card_id}"

    card_id: str = ContextField(
        description="Identificador único do cartão",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono do cartão",
        index="tag",
    )

    produto: str = ContextField(
        description="Produto: Inter Black, Cartão Inter, Mastercard Black, etc.",
        index="text",
    )

    tipo: str = ContextField(
        description="Tipo: credito, debito",
        index="tag",
    )

    bandeira: str = ContextField(
        description="Bandeira: visa, mastercard, elo",
        index="tag",
    )

    final: str = ContextField(
        description="4 últimos dígitos",
    )

    limite: float = ContextField(
        description="Limite de crédito (BRL)",
        index="numeric",
        sortable=True,
    )

    fatura_atual: float = ContextField(
        description="Fatura atual em aberto (BRL)",
        index="numeric",
        sortable=True,
    )

    vencimento: str = ContextField(
        description="Data de vencimento da fatura (ISO)",
        sortable=True,
    )

    anuidade: float = ContextField(
        description="Anuidade anual (BRL, 0 se isenta)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: ativo, bloqueado",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class Transaction(ContextModel):
    """Transaction entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_transaction:{txn_id}"

    txn_id: str = ContextField(
        description="Identificador único da transação",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    card_id: str | None = ContextField(
        description="Cartão usado (se compra)",
        index="tag",
    )

    account_id: str | None = ContextField(
        description="Conta (se débito/Pix)",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: compra_credito, compra_debito, pix_enviado, pix_recebido, cashback",
        index="tag",
    )

    merchant: str = ContextField(
        description="Estabelecimento/contraparte",
        index="text",
        weight=1.5,
    )

    mcc: str = ContextField(
        description="Categoria (MCC)",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor total da transação (BRL)",
        index="numeric",
        sortable=True,
    )

    data: str = ContextField(
        description="Timestamp ISO",
        sortable=True,
    )

    is_recurring: str = ContextField(
        description="Recorrente: sim, nao",
        index="tag",
    )

    parcela_atual: int = ContextField(
        description="Parcela atual (1 se à vista)",
        index="numeric",
    )

    parcela_total: int = ContextField(
        description="Total de parcelas (1 se à vista)",
        index="numeric",
        sortable=True,
    )

    valor_parcela: float = ContextField(
        description="Valor de cada parcela (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: aprovada, pendente, contestada",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class BillingCycle(ContextModel):
    """BillingCycle entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_billing_cycle:{cycle_id}"

    cycle_id: str = ContextField(
        description="Identificador único da fatura",
        is_key_component=True,
    )

    card_id: str = ContextField(
        description="Cartão",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    mes_referencia: str = ContextField(
        description="Mês de referência (YYYY-MM)",
        index="tag",
        sortable=True,
    )

    valor_total: float = ContextField(
        description="Valor total da fatura (BRL)",
        index="numeric",
        sortable=True,
    )

    valor_minimo: float = ContextField(
        description="Pagamento mínimo (BRL)",
        index="numeric",
    )

    vencimento: str = ContextField(
        description="Vencimento da fatura (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: aberta, fechada, paga, atrasada",
        index="tag",
    )


class Investment(ContextModel):
    """Investment entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_investment:{investment_id}"

    investment_id: str = ContextField(
        description="Identificador único da aplicação",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    produto: str = ContextField(
        description="Produto: CDB, LCI, LCA, Tesouro, Fundo, Previdência",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição da aplicação",
        index="text",
    )

    valor_aplicado: float = ContextField(
        description="Valor aplicado (BRL)",
        index="numeric",
        sortable=True,
    )

    rentabilidade_cdi_pct: int = ContextField(
        description="Rentabilidade (% do CDI)",
        index="numeric",
    )

    vencimento: str = ContextField(
        description="Vencimento (ISO)",
        sortable=True,
    )

    liquidez: str = ContextField(
        description="Liquidez: diaria, no_vencimento, D_mais_30",
        index="tag",
    )


class PixContact(ContextModel):
    """PixContact entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_pix_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Identificador único do contato",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono da agenda",
        index="tag",
    )

    nome: str = ContextField(
        description="Nome do contato",
        index="text",
        weight=2.0,
    )

    chave_pix: str = ContextField(
        description="Chave Pix mascarada",
    )

    tipo_chave: str = ContextField(
        description="Tipo: cpf, email, celular, aleatoria",
        index="tag",
    )

    banco: str = ContextField(
        description="Banco do contato",
        index="text",
    )

    is_frequente: str = ContextField(
        description="Contato frequente: sim, nao",
        index="tag",
    )


class Dispute(ContextModel):
    """Dispute entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_dispute:{dispute_id}"

    dispute_id: str = ContextField(
        description="Identificador único da contestação",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    transaction_id: str | None = ContextField(
        description="Transação contestada",
        index="tag",
    )

    motivo: str = ContextField(
        description="Motivo",
        index="text",
    )

    valor: float = ContextField(
        description="Valor contestado (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: aberta, em_analise, procedente, improcedente",
        index="tag",
    )

    data: str = ContextField(
        description="Timestamp ISO",
        sortable=True,
    )


class FeatureStore(ContextModel):
    """FeatureStore entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_features:{customer_id}"

    customer_id: str = ContextField(
        description="Cliente (chave da feature row)",
        is_key_component=True,
    )

    renda_mensal: float = ContextField(
        description="Feature: renda mensal (BRL)",
        index="numeric",
        sortable=True,
    )

    score_interno: int = ContextField(
        description="Feature: score interno (0-1000)",
        index="numeric",
        sortable=True,
    )

    utilizacao_cartao_pct: int = ContextField(
        description="Feature: % de utilização do limite do cartão",
        index="numeric",
    )

    tenure_meses: int = ContextField(
        description="Feature: meses de relacionamento",
        index="numeric",
    )

    velocity_gasto_30d: float = ContextField(
        description="Feature: gasto nos últimos 30 dias (BRL)",
        index="numeric",
        sortable=True,
    )

    saldo_medio_3m: float = ContextField(
        description="Feature: saldo médio dos últimos 3 meses (BRL)",
        index="numeric",
    )

    num_produtos: int = ContextField(
        description="Feature: nº de produtos contratados",
        index="numeric",
    )

    propensao_investimento: float = ContextField(
        description="Feature: propensão a investir (0-1)",
        index="numeric",
        sortable=True,
    )

    propensao_credito: float = ContextField(
        description="Feature: propensão a crédito (0-1)",
        index="numeric",
    )

    propensao_seguro: float = ContextField(
        description="Feature: propensão a seguro/previdência (0-1)",
        index="numeric",
    )

    perfil_digital: str = ContextField(
        description="Feature: engajamento digital: alto, medio, baixo",
        index="tag",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização das features (ISO)",
        sortable=True,
    )

    customer: Any = ContextRelationship(
        description="Cliente dono das features",
        target="Customer",
        source_field="customer_id",
    )


class Policy(ContextModel):
    """Policy entity for the Babi domain."""

    __redis_key_template__ = "banco_inter_policy:{policy_id}"

    policy_id: str = ContextField(
        description="Identificador único da política",
        is_key_component=True,
    )

    title: str = ContextField(
        description="Título da política",
        index="text",
        weight=2.0,
    )

    category: str = ContextField(
        description="Categoria: limites, contestacao, cartao, investimento, inter_one, seguranca, cashback, lgpd",
        index="tag",
    )

    content: str = ContextField(
        description="Texto completo da política",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Embedding vetorial",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
