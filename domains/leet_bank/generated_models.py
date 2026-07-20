"""Generated Context Surface models for the Leet Bank domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_customer:{customer_id}"

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

    phone_masked: str | None = ContextField(
        description="Celular mascarado (ex: +55 11 9****-1337)",
    )

    account_status: str = ContextField(
        description="Status: active, blocked, in_review",
        index="tag",
    )

    segmento: str = ContextField(
        description="Segmento: elite_1337, dev_pro, starter",
        index="tag",
    )

    cliente_desde: str = ContextField(
        description="Início do relacionamento (YYYY-MM)",
    )

    city: str = ContextField(
        description="Cidade do cliente",
        index="tag",
    )

    profissao: str | None = ContextField(
        description="Profissão declarada",
    )

    default_address: str | None = ContextField(
        description="Endereço residencial",
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
    """Account entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_account:{account_id}"

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

    conta_masked: str = ContextField(
        description="Número da conta mascarado (ex: ***1337)",
    )

    tipo: str = ContextField(
        description="Tipo: corrente",
        index="tag",
    )

    saldo_disponivel: float = ContextField(
        description="Saldo disponível em BRL",
        index="numeric",
        sortable=True,
    )

    saldo_cdb: float = ContextField(
        description="Total aplicado em CDB com liquidez diária (BRL)",
        index="numeric",
    )

    cdb_rendimento_cdi_pct: float = ContextField(
        description="Rendimento do CDB em % do CDI (ex: 103.37)",
    )

    cdb_liquidez: str | None = ContextField(
        description="Liquidez do CDB: diaria",
    )

    cheque_especial_limite: float = ContextField(
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
    """Card entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_card:{card_id}"

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
        description="Bandeira: mastercard, visa",
        index="tag",
    )

    produto: str = ContextField(
        description="Produto: leet_black, leet_virtual",
        index="tag",
    )

    numero_mascarado: str = ContextField(
        description="Final mascarado (ex: ****1337)",
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

    fatura_aberta: float = ContextField(
        description="Valor da fatura aberta do ciclo atual (BRL)",
        index="numeric",
    )

    fatura_vencimento: str | None = ContextField(
        description="Vencimento da fatura aberta (YYYY-MM-DD)",
    )

    utilizacao_pct: float = ContextField(
        description="Percentual de utilização do limite",
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


class BillingCycle(ContextModel):
    """BillingCycle entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_billing_cycle:{cycle_id}"

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


class Transaction(ContextModel):
    """Transaction entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_transaction:{transaction_id}"

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
        description="Conta envolvida (Pix, boleto, débito, salário)",
        index="tag",
    )

    billing_cycle_id: str | None = ContextField(
        description="Fatura à qual pertence",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: compra_credito, pix_envio, pix_recebido, debito, boleto, salario, estorno",
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
        description="Rótulo legível se recorrente (ex: Assinatura CLOUD DEV PRO)",
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


class PixContact(ContextModel):
    """PixContact entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_pix_contact:{contact_id}"

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
        description="Chave Pix (cpf, cnpj, email, celular ou aleatória)",
        index="text",
    )

    chave_tipo: str = ContextField(
        description="Tipo da chave: cpf, cnpj, email, celular, aleatoria",
        index="tag",
    )

    banco_destino: str = ContextField(
        description="Banco do destinatário",
    )

    contato_desde: str | None = ContextField(
        description="Desde quando é contato salvo (YYYY-MM)",
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


class PixAutomatico(ContextModel):
    """PixAutomatico entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_pix_automatico:{autorizacao_id}"

    autorizacao_id: str = ContextField(
        description="Identificador único da autorização",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente pagador",
        index="tag",
    )

    payee_name: str = ContextField(
        description="Nome do recebedor",
        index="text",
        weight=2.0,
    )

    chave_pix: str = ContextField(
        description="Chave Pix do recebedor",
    )

    chave_tipo: str = ContextField(
        description="Tipo da chave: cpf, cnpj, email, celular, aleatoria",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor de cada cobrança (BRL)",
        index="numeric",
    )

    dia_cobranca: int = ContextField(
        description="Dia do mês da cobrança",
        index="numeric",
    )

    periodicidade: str = ContextField(
        description="Periodicidade: mensal, semanal, anual",
        index="tag",
    )

    status: str = ContextField(
        description="Status: ativo, pausado, cancelado",
        index="tag",
    )

    data_criacao: str = ContextField(
        description="Timestamp ISO da autorização",
    )

    ultima_cobranca: str | None = ContextField(
        description="Timestamp ISO da última cobrança executada",
    )

    descricao: str = ContextField(
        description="Descrição legível da recorrência",
    )

    customer: Any = ContextRelationship(
        description="Cliente pagador",
        target="Customer",
        source_field="customer_id",
    )


class Dispute(ContextModel):
    """Dispute entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_dispute:{dispute_id}"

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


class RewardsAccount(ContextModel):
    """RewardsAccount entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_rewards:{rewards_id}"

    rewards_id: str = ContextField(
        description="Identificador único da conta de pontos",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente dono",
        index="tag",
    )

    programa: str = ContextField(
        description="Programa: leet_xp",
        index="tag",
    )

    saldo_xp: int = ContextField(
        description="Saldo atual de XP",
        index="numeric",
    )

    nivel: str = ContextField(
        description="Nível do programa: Iniciante, Hacker, Elite 1337",
        index="tag",
    )

    xp_expirando: int = ContextField(
        description="XP que expira na próxima janela",
        index="numeric",
    )

    expira_em: str | None = ContextField(
        description="Data de expiração do próximo lote de XP (YYYY-MM-DD)",
    )

    multiplicador_tech: int = ContextField(
        description="Multiplicador de XP em tech/eletrônicos (ex: 2 = 2x)",
    )

    categoria_top: str | None = ContextField(
        description="Categoria de maior acúmulo (tech_eletronicos, alimentacao, etc)",
    )

    customer: Any = ContextRelationship(
        description="Cliente",
        target="Customer",
        source_field="customer_id",
    )


class SupportTicket(ContextModel):
    """SupportTicket entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_support_ticket:{ticket_id}"

    ticket_id: str = ContextField(
        description="Identificador único do chamado",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente",
        index="tag",
    )

    categoria: str = ContextField(
        description="Categoria: cartao, pix, contestacao, fatura, investimentos, outros",
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


class FeatureStoreRecord(ContextModel):
    """FeatureStoreRecord entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_features:{customer_id}"

    customer_id: str = ContextField(
        description="Cliente (chave da feature row)",
        is_key_component=True,
    )

    saldo: float = ContextField(
        description="Feature: saldo disponível em conta (BRL)",
    )

    cdb_total: float = ContextField(
        description="Feature: total aplicado em CDB (BRL)",
    )

    cdb_livre: float = ContextField(
        description="Feature: CDB livre de garantias, disponível como colateral (BRL)",
    )

    credito_flash_pre_aprovado: float = ContextField(
        description="Feature: Crédito Flash pré-aprovado (BRL)",
    )

    taxa_flash_am: float = ContextField(
        description="Feature: taxa do Crédito Flash em % ao mês",
    )

    pix_ticket_medio: float = ContextField(
        description="Feature: ticket médio dos Pix enviados (BRL)",
    )

    maior_pix_90d: float = ContextField(
        description="Feature: maior Pix enviado nos últimos 90 dias (BRL)",
    )

    contatos_confiaveis: int = ContextField(
        description="Feature: nº de contatos Pix confiáveis salvos",
    )

    golpe_score: float = ContextField(
        description="Feature: score de risco de golpe do cliente (0-1)",
    )

    utilizacao_cartao_pct: int = ContextField(
        description="Feature: utilização do limite do cartão (%)",
    )

    xp_saldo: int = ContextField(
        description="Feature: saldo de XP no programa de pontos",
    )

    xp_expirando: int = ContextField(
        description="Feature: XP expirando na próxima janela",
    )

    nivel: str = ContextField(
        description="Feature: nível no programa XP (ex: elite_1337)",
    )

    propensao_credito: float = ContextField(
        description="Feature: propensão a contratar crédito (0-1)",
    )

    torce_para: str = ContextField(
        description="Feature: time do coração (base pra ofertas de experiências)",
    )

    evento_proximo: str = ContextField(
        description="Feature: próximo evento de interesse do cliente",
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
    """Policy entity for the Leet Bank domain."""

    __redis_key_template__ = "leet_bank_policy:{policy_id}"

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
        description="Categoria: seguranca, pix, credito, pontos, contestacao, fatura, cartao, open_finance, experiencias",
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
