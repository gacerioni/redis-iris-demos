"""Generated Context Surface models for the BS2 Pay domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Merchant(ContextModel):
    """Merchant entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_merchant:{merchant_id}"

    merchant_id: str = ContextField(
        description="Identificador único do estabelecimento",
        is_key_component=True,
    )

    razao_social: str = ContextField(
        description="Razão social do estabelecimento",
        index="text",
        weight=2.0,
    )

    nome_fantasia: str = ContextField(
        description="Nome fantasia do estabelecimento",
        index="text",
        weight=2.0,
    )

    cnpj_masked: str = ContextField(
        description="CNPJ mascarado (ex: 12.***.***/0001-07)",
    )

    segmento: str = ContextField(
        description="Segmento: artigos_esportivos, alimentacao, autopecas",
        index="tag",
    )

    plano_adiq: str = ContextField(
        description="Plano de credenciamento: adiq_pro, adiq_flex",
        index="tag",
    )

    cliente_desde: str = ContextField(
        description="Início do credenciamento (YYYY-MM)",
    )

    relacionamento_bs2: str = ContextField(
        description="Relacionamento bancário: bs2_empresas, nenhum",
        index="tag",
    )

    cidade: str = ContextField(
        description="Cidade da sede",
        index="tag",
    )

    status: str = ContextField(
        description="Status: ativo, suspenso, descredenciado",
        index="tag",
    )

    socio_responsavel: str = ContextField(
        description="Sócio responsável pela conta",
        index="text",
        weight=1.5,
    )

    contato_email: str = ContextField(
        description="Email de contato do sócio",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    pj_accounts: Any = ContextRelationship(
        description="Contas PJ do estabelecimento",
        target="PjAccount",
        source_field="merchant_id",
    )

    terminals: Any = ContextRelationship(
        description="Terminais POS do estabelecimento",
        target="Terminal",
        source_field="merchant_id",
    )

    features: Any = ContextRelationship(
        description="Features online do estabelecimento",
        target="FeatureStore",
        source_field="merchant_id",
    )


class PjAccount(ContextModel):
    """PjAccount entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_pj_account:{account_id}"

    account_id: str = ContextField(
        description="Identificador único da conta PJ",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento titular",
        index="tag",
    )

    banco: str = ContextField(
        description="Banco da conta de liquidação",
        index="tag",
    )

    agencia: str = ContextField(
        description="Número da agência",
    )

    conta_masked: str = ContextField(
        description="Número da conta mascarado",
    )

    saldo_disponivel: float = ContextField(
        description="Saldo disponível em BRL",
        index="numeric",
        sortable=True,
    )

    limite_capital_giro: float = ContextField(
        description="Limite de capital de giro pré-aprovado (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: ativa, bloqueada",
        index="tag",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento titular",
        target="Merchant",
        source_field="merchant_id",
    )


class SalesTransaction(ContextModel):
    """SalesTransaction entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_sales_transaction:{transaction_id}"

    transaction_id: str = ContextField(
        description="Identificador único da venda",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento da venda",
        index="tag",
    )

    data: str = ContextField(
        description="Data da venda (ISO)",
        sortable=True,
    )

    valor_bruto: float = ContextField(
        description="Valor bruto da venda (BRL)",
        index="numeric",
        sortable=True,
    )

    modalidade: str = ContextField(
        description="Modalidade: credito_avista, credito_parcelado, debito, pix",
        index="tag",
    )

    parcelas: int = ContextField(
        description="Número de parcelas (1 se à vista)",
    )

    bandeira: str = ContextField(
        description="Bandeira: visa, mastercard, elo, pix",
        index="tag",
    )

    canal: str = ContextField(
        description="Canal de captura: ecommerce, pos",
        index="tag",
    )

    terminal_id: str | None = ContextField(
        description="Terminal POS da captura (null no e-commerce)",
        index="tag",
    )

    status: str = ContextField(
        description="Status: aprovada, em_disputa, estornada",
        index="tag",
    )

    nsu: str = ContextField(
        description="NSU (número sequencial único) da transação",
    )

    cliente_final: str = ContextField(
        description="Nome do comprador final",
        index="text",
        weight=1.5,
    )

    descricao: str = ContextField(
        description="Descrição resumida do pedido",
        index="text",
    )

    mdr_pct: float = ContextField(
        description="MDR aplicado na venda (%)",
    )

    valor_liquido: float = ContextField(
        description="Valor líquido após MDR (BRL)",
        index="numeric",
    )

    entrega: str = ContextField(
        description="Entrega: confirmada:<rastreio>, extraviada:<rastreio> ou n/a (POS)",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento da venda",
        target="Merchant",
        source_field="merchant_id",
    )

    terminal: Any = ContextRelationship(
        description="Terminal POS da captura",
        target="Terminal",
        source_field="terminal_id",
    )


class Receivable(ContextModel):
    """Receivable entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_receivable:{receivable_id}"

    receivable_id: str = ContextField(
        description="Identificador único do recebível",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento dono da agenda",
        index="tag",
    )

    data_prevista: str = ContextField(
        description="Data prevista de liquidação (ISO)",
        sortable=True,
    )

    valor_bruto: float = ContextField(
        description="Valor bruto do lote (BRL)",
        index="numeric",
    )

    mdr_valor: float = ContextField(
        description="MDR descontado do lote (BRL)",
    )

    valor_liquido: float = ContextField(
        description="Valor líquido a receber (BRL)",
        index="numeric",
        sortable=True,
    )

    bandeira: str = ContextField(
        description="Bandeira predominante: visa, mastercard, elo, pix",
        index="tag",
    )

    modalidade: str = ContextField(
        description="Modalidade: credito_avista, credito_parcelado, debito, pix",
        index="tag",
    )

    status: str = ContextField(
        description="Status: pendente, liquidado, antecipado",
        index="tag",
    )

    origem_transaction_id: str = ContextField(
        description="Venda âncora (representativa) do lote de liquidação",
        index="tag",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento",
        target="Merchant",
        source_field="merchant_id",
    )

    origem_transaction: Any = ContextRelationship(
        description="Venda âncora do lote",
        target="SalesTransaction",
        source_field="origem_transaction_id",
    )


class Terminal(ContextModel):
    """Terminal entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_terminal:{terminal_id}"

    terminal_id: str = ContextField(
        description="Identificador único do terminal",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento dono do terminal",
        index="tag",
    )

    serial: str = ContextField(
        description="Número de série do equipamento",
    )

    modelo: str = ContextField(
        description="Modelo: pos_smart, pos_mini",
        index="tag",
    )

    loja: str = ContextField(
        description="Loja onde o terminal está instalado",
        index="tag",
    )

    status: str = ContextField(
        description="Status: ativo, instavel, inativo",
        index="tag",
    )

    ultima_transacao_em: str = ContextField(
        description="Timestamp ISO da última transação capturada",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento",
        target="Merchant",
        source_field="merchant_id",
    )


class Dispute(ContextModel):
    """Dispute entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_dispute:{dispute_id}"

    dispute_id: str = ContextField(
        description="Identificador único da disputa",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento notificado",
        index="tag",
    )

    transaction_id: str = ContextField(
        description="Venda contestada",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor contestado (BRL)",
        index="numeric",
    )

    motivo: str = ContextField(
        description="Motivo: nao_reconhecida, produto_nao_recebido, duplicada, fraude",
        index="tag",
    )

    cliente_final: str = ContextField(
        description="Comprador que abriu a contestação",
        index="text",
        weight=1.5,
    )

    status: str = ContextField(
        description="Status: aguardando_lojista, em_analise, ganha, perdida",
        index="tag",
    )

    prazo_resposta: str = ContextField(
        description="Data limite para envio de evidências (ISO)",
    )

    bandeira: str = ContextField(
        description="Bandeira da transação: visa, mastercard, elo",
        index="tag",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento",
        target="Merchant",
        source_field="merchant_id",
    )

    transaction: Any = ContextRelationship(
        description="Venda contestada",
        target="SalesTransaction",
        source_field="transaction_id",
    )


class SupportTicket(ContextModel):
    """SupportTicket entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_support_ticket:{ticket_id}"

    ticket_id: str = ContextField(
        description="Identificador único do chamado",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento",
        index="tag",
    )

    categoria: str = ContextField(
        description="Categoria: terminal, suprimentos, repasse, chargeback, outros",
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

    merchant: Any = ContextRelationship(
        description="Estabelecimento",
        target="Merchant",
        source_field="merchant_id",
    )


class PixContact(ContextModel):
    """PixContact entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_pix_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Identificador único do contato",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Estabelecimento dono do contato",
        index="tag",
    )

    recipient_name: str = ContextField(
        description="Nome do destinatário",
        index="text",
        weight=2.0,
    )

    chave_pix: str = ContextField(
        description="Chave Pix (cnpj, email, celular ou aleatória)",
        index="text",
    )

    chave_tipo: str = ContextField(
        description="Tipo da chave: cnpj, email, celular, aleatoria",
        index="tag",
    )

    banco_destino: str = ContextField(
        description="Banco do destinatário",
    )

    tipo_relacao: str = ContextField(
        description="Relação: fornecedor, pro_labore, frete, outros",
        index="tag",
    )

    valor_recorrente: float | None = ContextField(
        description="Valor típico do pagamento recorrente (BRL)",
    )

    recorrencia: str | None = ContextField(
        description="Padrão de recorrência (ex: mensal, todo dia 15)",
    )

    frequencia_uso: int = ContextField(
        description="Quantas vezes o lojista já pagou este contato",
        index="numeric",
    )

    ultimo_uso: str | None = ContextField(
        description="Timestamp do último Pix enviado",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento",
        target="Merchant",
        source_field="merchant_id",
    )


class FeatureStore(ContextModel):
    """FeatureStore entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_features:{merchant_id}"

    merchant_id: str = ContextField(
        description="Estabelecimento (chave da feature row)",
        is_key_component=True,
    )

    agenda_liquida_30d: float = ContextField(
        description="Feature: agenda líquida a receber nos próximos 30 dias (BRL)",
    )

    agenda_liquida_31_60d: float = ContextField(
        description="Feature: agenda líquida a receber entre 31 e 60 dias (BRL)",
    )

    vendas_mes: float = ContextField(
        description="Feature: vendas brutas do ciclo atual (BRL)",
    )

    qtd_transacoes_mes: int = ContextField(
        description="Feature: nº de transações do ciclo atual",
    )

    ticket_medio: float = ContextField(
        description="Feature: ticket médio do ciclo atual (BRL)",
    )

    mdr_medio_pct: float = ContextField(
        description="Feature: MDR médio ponderado do ciclo (%)",
    )

    chargeback_rate_pct: float = ContextField(
        description="Feature: taxa de chargeback (%)",
    )

    crescimento_mm_pct: float = ContextField(
        description="Feature: crescimento mês a mês das vendas (%)",
    )

    plano: str = ContextField(
        description="Feature: plano de credenciamento vigente",
    )

    taxa_antecipacao_am: float = ContextField(
        description="Feature: taxa de antecipação vigente (% a.m., pro-rata)",
    )

    sazonalidade_pico: str = ContextField(
        description="Feature: pico sazonal de vendas do estabelecimento",
    )

    saldo_pj: float = ContextField(
        description="Feature: saldo disponível na conta PJ BS2 (BRL)",
    )

    capital_giro_pre_aprovado: float = ContextField(
        description="Feature: limite de capital de giro pré-aprovado (BRL)",
    )

    filial_planejada: str = ContextField(
        description="Feature: cidade da próxima filial planejada pelo lojista",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização (ISO)",
    )

    merchant: Any = ContextRelationship(
        description="Estabelecimento dono das features",
        target="Merchant",
        source_field="merchant_id",
    )


class Policy(ContextModel):
    """Policy entity for the BS2 Pay domain."""

    __redis_key_template__ = "bs2_adiq_policy:{policy_id}"

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
        description="Categoria: taxas, repasse, chargeback, antecipacao, terminal, credenciamento, pix, credito, conta",
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
