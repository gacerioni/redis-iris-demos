"""Generated Context Surface models for the Itaú domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Identificador único do cliente",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome completo do cliente",
        index="text",
        weight=2.0,
    )

    cpf_masked: str = ContextField(
        description="CPF mascarado (ex: ***.456.789-**)",
    )

    email: str = ContextField(
        description="Email do cliente",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    phone: str | None = ContextField(
        description="Celular cadastrado",
    )

    account_status: str = ContextField(
        description="Status: active, blocked, in_review",
        index="tag",
    )

    tier: str = ContextField(
        description="Segmento: pf_mass, uniclass, personnalite, private",
        index="tag",
    )

    relationship_years: int = ContextField(
        description="Anos de relacionamento com o banco",
        index="numeric",
        sortable=True,
    )

    city: str = ContextField(
        description="Cidade do cliente",
        index="tag",
    )

    default_address: str | None = ContextField(
        description="Endereço residencial",
    )

    perfil_investidor: str = ContextField(
        description="Perfil de investidor: conservador, moderado, arrojado, sofisticado",
        index="tag",
    )

    credit_score: int = ContextField(
        description="Score interno Itaú (0-1000)",
        index="numeric",
        sortable=True,
    )

    account_created_at: str = ContextField(
        description="Data de abertura de conta (ISO)",
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


class Account(ContextModel):
    """Account entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_account:{account_id}"

    account_id: str = ContextField(
        description="Identificador único da conta",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente titular",
        index="tag",
    )

    agencia: str = ContextField(
        description="Número da agência",
    )

    conta_numero: str = ContextField(
        description="Número da conta com dígito",
    )

    tipo: str = ContextField(
        description="Tipo: corrente, poupanca, cdb",
        index="tag",
    )

    saldo_disponivel: float = ContextField(
        description="Saldo disponível em BRL",
        index="numeric",
        sortable=True,
    )

    saldo_aplicado: float = ContextField(
        description="Saldo aplicado em investimentos (BRL)",
        index="numeric",
    )

    limite_cheque_especial: float = ContextField(
        description="Limite do cheque especial (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: active, blocked",
        index="tag",
    )

    customer: Any = ContextRelationship(
        description="Cliente titular",
        target="Customer",
        source_field="customer_id",
    )


class Card(ContextModel):
    """Card entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_card:{card_id}"

    card_id: str = ContextField(
        description="Identificador único do cartão",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente titular",
        index="tag",
    )

    account_id: str = ContextField(
        description="Conta vinculada",
        index="tag",
    )

    bandeira: str = ContextField(
        description="Bandeira: visa, mastercard, elo",
        index="tag",
    )

    produto: str = ContextField(
        description="Produto: click, itaucard, uniclass, personnalite, mastercard_black, visa_infinite",
        index="tag",
    )

    numero_mascarado: str = ContextField(
        description="Final mascarado (ex: ****1234)",
    )

    limite_total: float = ContextField(
        description="Limite total aprovado (BRL)",
        index="numeric",
    )

    limite_usado: float = ContextField(
        description="Limite atualmente utilizado (BRL)",
        index="numeric",
    )

    limite_disponivel: float = ContextField(
        description="Limite disponível para uso (BRL)",
        index="numeric",
    )

    validade: str = ContextField(
        description="Validade no formato MM/AA",
    )

    status: str = ContextField(
        description="Status: active, blocked, replaced",
        index="tag",
    )

    customer: Any = ContextRelationship(
        description="Cliente titular",
        target="Customer",
        source_field="customer_id",
    )

    account: Any = ContextRelationship(
        description="Conta vinculada",
        target="Account",
        source_field="account_id",
    )


class Transaction(ContextModel):
    """Transaction entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_transaction:{transaction_id}"

    transaction_id: str = ContextField(
        description="Identificador único da transação",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente associado",
        index="tag",
    )

    card_id: str | None = ContextField(
        description="Cartão usado (se for compra com cartão)",
        index="tag",
    )

    account_id: str | None = ContextField(
        description="Conta envolvida (Pix, débito, transferência)",
        index="tag",
    )

    billing_cycle_id: str | None = ContextField(
        description="Fatura à qual pertence",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: compra_credito, pix_envio, pix_recebido, debito, anuidade, juros, estorno",
        index="tag",
    )

    merchant: str = ContextField(
        description="Estabelecimento ou contraparte",
        index="text",
        weight=1.5,
    )

    mcc: str | None = ContextField(
        description="Merchant Category Code",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor (positivo = saída, negativo = entrada)",
        index="numeric",
    )

    parcelas_total: int = ContextField(
        description="Total de parcelas (1 se à vista)",
    )

    parcela_atual: int = ContextField(
        description="Parcela atual",
    )

    status: str = ContextField(
        description="Status: aprovada, contestada, estornada, pendente",
        index="tag",
    )

    data_compra: str = ContextField(
        description="Timestamp ISO da compra",
        sortable=True,
    )

    data_lancamento: str = ContextField(
        description="Timestamp ISO do lançamento na fatura",
        sortable=True,
    )

    is_recurring: str = ContextField(
        description="Flag de recorrência: sim, nao",
        index="tag",
    )

    recurring_label: str | None = ContextField(
        description="Rótulo legível se recorrente (ex: Amazon Prime + Music)",
    )

    location_city: str | None = ContextField(
        description="Cidade da compra",
    )

    dispute_id: str | None = ContextField(
        description="Se contestada, ID da contestação",
        index="tag",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )

    card: Any = ContextRelationship(
        description="Cartão",
        target="Card",
        source_field="card_id",
    )

    account: Any = ContextRelationship(
        description="Conta",
        target="Account",
        source_field="account_id",
    )


class BillingCycle(ContextModel):
    """BillingCycle entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_billing_cycle:{cycle_id}"

    cycle_id: str = ContextField(
        description="Identificador único da fatura",
        is_key_component=True,
    )

    card_id: str = ContextField(
        description="Cartão da fatura",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Cliente titular",
        index="tag",
    )

    mes_referencia: str = ContextField(
        description="Mês de referência (YYYY-MM)",
        index="tag",
    )

    data_fechamento: str = ContextField(
        description="Data de fechamento da fatura (ISO)",
    )

    data_vencimento: str = ContextField(
        description="Data de vencimento da fatura (ISO)",
    )

    valor_total: float = ContextField(
        description="Valor total da fatura (BRL)",
        index="numeric",
    )

    pagamento_minimo: float = ContextField(
        description="Valor do pagamento mínimo (BRL)",
        index="numeric",
    )

    valor_pago: float = ContextField(
        description="Valor já pago (BRL, 0 se aberta)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: aberta, fechada_aguardando_pagamento, paga, atrasada",
        index="tag",
    )

    card: Any = ContextRelationship(
        description="Cartão da fatura",
        target="Card",
        source_field="card_id",
    )

    customer: Any = ContextRelationship(
        description="Cliente titular",
        target="Customer",
        source_field="customer_id",
    )


class Dispute(ContextModel):
    """Dispute entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_dispute:{dispute_id}"

    dispute_id: str = ContextField(
        description="Identificador único da contestação",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente que abriu",
        index="tag",
    )

    transaction_id: str = ContextField(
        description="Transação contestada",
        index="tag",
    )

    protocolo: str = ContextField(
        description="Protocolo de atendimento",
        index="text",
    )

    motivo: str = ContextField(
        description="Motivo: nao_reconheco, duplicada, valor_divergente, produto_nao_recebido, fraude",
        index="tag",
    )

    status: str = ContextField(
        description="Status: aberta, em_analise, resolvida_favoravel, resolvida_contraria",
        index="tag",
    )

    valor_contestado: float = ContextField(
        description="Valor da contestação (BRL)",
        index="numeric",
    )

    data_abertura: str = ContextField(
        description="Timestamp ISO de abertura",
    )

    data_resolucao: str | None = ContextField(
        description="Timestamp ISO da resolução",
    )

    descricao: str = ContextField(
        description="Descrição do cliente",
    )

    resolucao: str | None = ContextField(
        description="Conclusão do banco",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )

    transaction: Any = ContextRelationship(
        description="Transação contestada",
        target="Transaction",
        source_field="transaction_id",
    )


class PixContact(ContextModel):
    """PixContact entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_pix_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Identificador único do contato",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono do contato",
        index="tag",
    )

    recipient_name: str = ContextField(
        description="Nome do destinatário",
        index="text",
        weight=2.0,
    )

    chave_pix: str = ContextField(
        description="Chave Pix (cpf, email, celular ou aleatória)",
        index="text",
    )

    chave_tipo: str = ContextField(
        description="Tipo da chave: cpf, email, celular, aleatoria",
        index="tag",
    )

    banco_destino: str = ContextField(
        description="Banco do destinatário",
    )

    frequencia_uso: int = ContextField(
        description="Quantas vezes o cliente já enviou pra este contato",
        index="numeric",
    )

    ultimo_uso: str | None = ContextField(
        description="Timestamp do último Pix enviado",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class RewardsAccount(ContextModel):
    """RewardsAccount entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_rewards:{rewards_id}"

    rewards_id: str = ContextField(
        description="Identificador único da conta de pontos",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono",
        index="tag",
    )

    programa: str = ContextField(
        description="Programa: sempre_presente, atomos, latam_pass",
        index="tag",
    )

    saldo_pontos: int = ContextField(
        description="Saldo atual de pontos",
        index="numeric",
    )

    pontos_a_vencer: int = ContextField(
        description="Pontos que vencem nos próximos 90 dias",
        index="numeric",
    )

    data_vencimento_proxima: str | None = ContextField(
        description="Próxima data de vencimento de pontos (ISO)",
    )

    categoria_top: str | None = ContextField(
        description="Categoria de maior acúmulo (alimentacao, viagem, supermercado, etc)",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class SupportTicket(ContextModel):
    """SupportTicket entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_support_ticket:{ticket_id}"

    ticket_id: str = ContextField(
        description="Identificador único do chamado",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    categoria: str = ContextField(
        description="Categoria: contestacao, limite, cartao_bloqueado, pix, fatura, outros",
        index="tag",
    )

    status: str = ContextField(
        description="Status: aberto, em_andamento, resolvido",
        index="tag",
    )

    data_abertura: str = ContextField(
        description="Timestamp ISO de abertura",
    )

    data_resolucao: str | None = ContextField(
        description="Timestamp ISO de resolução",
    )

    resumo: str = ContextField(
        description="Resumo do chamado",
        index="text",
    )

    resolucao: str | None = ContextField(
        description="Como foi resolvido",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class FeatureStore(ContextModel):
    """FeatureStore entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_features:{customer_id}"

    customer_id: str = ContextField(
        description="Cliente (chave da feature row)",
        is_key_component=True,
    )

    renda_mensal: float = ContextField(
        description="Feature: renda mensal estimada (BRL)",
    )

    score_interno: int = ContextField(
        description="Feature: score interno Itaú (0-1000)",
    )

    aplicado_cdb: float = ContextField(
        description="Feature: total aplicado em CDB tributado (BRL)",
    )

    saldo_medio_3m: float = ContextField(
        description="Feature: saldo médio dos últimos 3 meses (BRL)",
    )

    tenure_meses: int = ContextField(
        description="Feature: meses de relacionamento Personnalité",
    )

    num_produtos: int = ContextField(
        description="Feature: nº de produtos contratados",
    )

    propensao_investimento: float = ContextField(
        description="Feature: propensão a investir (0-1)",
    )

    propensao_upgrade_cartao: float = ContextField(
        description="Feature: propensão a upgrade de cartão premium (0-1)",
    )

    propensao_cobranded_clube: float = ContextField(
        description="Feature: afinidade com cartão co-branded do time do coração (0-1)",
    )

    propensao_seguro: float = ContextField(
        description="Feature: propensão a seguro/previdência (0-1)",
    )

    time_do_coracao: str = ContextField(
        description="Feature: clube de futebol (base do cartão co-branded via cartão branco)",
    )

    perfil_digital: str = ContextField(
        description="Feature: engajamento digital: alto, medio, baixo",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização (ISO)",
    )

    customer: Any = ContextRelationship(
        description="Cliente dono das features",
        target="Customer",
        source_field="customer_id",
    )


class Policy(ContextModel):
    """Policy entity for the Itaú domain."""

    __redis_key_template__ = "itau_assist_policy:{policy_id}"

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
        description="Categoria: contestacao, limite, fatura, pix, pontos, seguranca, conta",
        index="tag",
    )

    content: str = ContextField(
        description="Texto completo da política",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Embedding vetorial do conteúdo",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
