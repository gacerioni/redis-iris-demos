"""Generated Context Surface models for the PicPay Assist domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class User(ContextModel):
    """User entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_user:{user_id}"

    user_id: str = ContextField(
        description="Identificador único do usuário",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Nome completo",
        index="text",
        weight=2.0,
    )

    handle: str = ContextField(
        description="@usuário do PicPay",
        index="text",
        weight=1.5,
        no_stem=True,
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

    saldo_carteira: float = ContextField(
        description="Saldo na carteira PicPay (BRL)",
        index="numeric",
        sortable=True,
    )

    cashback_disponivel: float = ContextField(
        description="Cashback acumulado disponível (BRL)",
        index="numeric",
        sortable=True,
    )

    membro_desde: str = ContextField(
        description="Ano de cadastro (YYYY)",
    )

    nivel: str = ContextField(
        description="Nível: membro, prata, ouro, diamante",
        index="tag",
    )

    pix_key_principal: str = ContextField(
        description="Chave Pix principal mascarada",
    )

    contacts: Any = ContextRelationship(
        description="Contatos sociais do usuário",
        target="Contact",
        source_field="user_id",
    )

    transactions: Any = ContextRelationship(
        description="Transações do usuário",
        target="Transaction",
        source_field="user_id",
    )

    cofrinhos: Any = ContextRelationship(
        description="Cofrinhos (metas) do usuário",
        target="Cofrinho",
        source_field="user_id",
    )

    features: Any = ContextRelationship(
        description="Features online (feature store) do usuário",
        target="FeatureStore",
        source_field="user_id",
    )


class Contact(ContextModel):
    """Contact entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_contact:{contact_id}"

    contact_id: str = ContextField(
        description="Identificador único do contato",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Dono da agenda",
        index="tag",
    )

    nome: str = ContextField(
        description="Nome do contato",
        index="text",
        weight=2.0,
    )

    handle: str = ContextField(
        description="@ do contato no PicPay",
        index="text",
        no_stem=True,
    )

    relacao: str = ContextField(
        description="Relação: amigo, familia, republica, trabalho, desconhecido",
        index="tag",
    )

    is_frequente: str = ContextField(
        description="Contato frequente: sim, nao",
        index="tag",
    )

    trust_level: str = ContextField(
        description="Confiança: confiavel, novo, suspeito",
        index="tag",
    )

    vezes_transacionado: int = ContextField(
        description="Quantas vezes já transacionou",
        index="numeric",
        sortable=True,
    )

    ultima_interacao: str = ContextField(
        description="Timestamp ISO da última transação",
        sortable=True,
    )

    owner: Any = ContextRelationship(
        description="Dono da agenda",
        target="User",
        source_field="user_id",
    )


class Transaction(ContextModel):
    """Transaction entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_transaction:{txn_id}"

    txn_id: str = ContextField(
        description="Identificador único da transação",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Dono da transação",
        index="tag",
    )

    counterparty_id: str | None = ContextField(
        description="Contato da outra ponta",
        index="tag",
    )

    counterparty_nome: str = ContextField(
        description="Nome da outra ponta",
        index="text",
    )

    tipo: str = ContextField(
        description="Tipo: p2p_enviado, p2p_recebido, pix, compra, cashback, cofrinho, boleto",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor da transação (BRL)",
        index="numeric",
        sortable=True,
    )

    tag: str | None = ContextField(
        description="Tag social (ex: churrasco, aluguel, rolê)",
        index="text",
    )

    emoji: str | None = ContextField(
        description="Emoji social da transação",
    )

    status: str = ContextField(
        description="Status: concluida, pendente, solicitada, bloqueada",
        index="tag",
    )

    data: str = ContextField(
        description="Timestamp ISO da transação",
        sortable=True,
    )

    is_split: str = ContextField(
        description="Faz parte de um racha: sim, nao",
        index="tag",
    )

    split_group_id: str | None = ContextField(
        description="ID do grupo de racha",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Dono da transação",
        target="User",
        source_field="user_id",
    )


class CashbackEvent(ContextModel):
    """CashbackEvent entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_cashback:{cashback_id}"

    cashback_id: str = ContextField(
        description="Identificador único do cashback",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Usuário",
        index="tag",
    )

    origem: str = ContextField(
        description="Origem: compra, promo, indicacao, pix, parceiro",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição (ex: 'Cashback iFood 5%')",
        index="text",
    )

    valor: float = ContextField(
        description="Valor do cashback (BRL)",
        index="numeric",
        sortable=True,
    )

    data: str = ContextField(
        description="Timestamp ISO",
        sortable=True,
    )

    destino: str = ContextField(
        description="Destino: disponivel, carteira, cofrinho",
        index="tag",
    )

    status: str = ContextField(
        description="Status: creditado, resgatado, expirado",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Usuário",
        target="User",
        source_field="user_id",
    )


class Cofrinho(ContextModel):
    """Cofrinho entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_cofrinho:{cofrinho_id}"

    cofrinho_id: str = ContextField(
        description="Identificador único do cofrinho",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Usuário",
        index="tag",
    )

    nome: str = ContextField(
        description="Nome da meta (ex: 'Viagem Chile')",
        index="text",
        weight=2.0,
    )

    emoji: str | None = ContextField(
        description="Emoji da meta",
    )

    meta_valor: float = ContextField(
        description="Valor-alvo da meta (BRL)",
        index="numeric",
        sortable=True,
    )

    saldo_atual: float = ContextField(
        description="Quanto já guardou (BRL)",
        index="numeric",
        sortable=True,
    )

    rende_cdi_pct: int = ContextField(
        description="Rendimento (% do CDI)",
        index="numeric",
    )

    data_meta: str = ContextField(
        description="Data-alvo da meta (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: ativo, concluido, pausado",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Usuário",
        target="User",
        source_field="user_id",
    )


class Card(ContextModel):
    """Card entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_card:{card_id}"

    card_id: str = ContextField(
        description="Identificador único do cartão",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Dono do cartão",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: debito, credito",
        index="tag",
    )

    final: str = ContextField(
        description="4 últimos dígitos",
    )

    limite: float = ContextField(
        description="Limite de crédito (BRL)",
        index="numeric",
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

    status: str = ContextField(
        description="Status: ativo, bloqueado",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Dono do cartão",
        target="User",
        source_field="user_id",
    )


class Boleto(ContextModel):
    """Boleto entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_boleto:{boleto_id}"

    boleto_id: str = ContextField(
        description="Identificador único do boleto",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Usuário",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição (ex: 'Conta de luz Enel')",
        index="text",
        weight=1.5,
    )

    beneficiario: str = ContextField(
        description="Beneficiário",
        index="text",
    )

    valor: float = ContextField(
        description="Valor do boleto (BRL)",
        index="numeric",
        sortable=True,
    )

    vencimento: str = ContextField(
        description="Data de vencimento (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: a_pagar, pago, vencido",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Usuário",
        target="User",
        source_field="user_id",
    )


class SuspiciousFlag(ContextModel):
    """SuspiciousFlag entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_suspicious:{flag_id}"

    flag_id: str = ContextField(
        description="Identificador único da sinalização",
        is_key_component=True,
    )

    user_id: str = ContextField(
        description="Usuário protegido",
        index="tag",
    )

    target_type: str = ContextField(
        description="Alvo: contato, chave_pix, transacao",
        index="tag",
    )

    target_id: str | None = ContextField(
        description="ID do alvo (contato/transação)",
        index="tag",
    )

    target_label: str = ContextField(
        description="Rótulo legível do alvo (ex: '@premios-caixa-2026')",
        index="text",
    )

    motivo: str = ContextField(
        description="Motivo da suspeita",
        index="text",
    )

    padrao_detectado: str = ContextField(
        description="Padrão: chave_recem_criada, valor_atipico, fora_do_grafo, urgencia_falsa, premio_falso",
        index="tag",
    )

    severidade: str = ContextField(
        description="Severidade: baixa, media, alta, critica",
        index="tag",
    )

    data: str = ContextField(
        description="Timestamp ISO",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: alerta, bloqueado, liberado, em_analise",
        index="tag",
    )

    owner: Any = ContextRelationship(
        description="Usuário protegido",
        target="User",
        source_field="user_id",
    )


class Policy(ContextModel):
    """Policy entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_policy:{policy_id}"

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
        description="Categoria: pagamentos, cashback, cofrinho, seguranca, cartao, limites, lgpd",
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


class FeatureStore(ContextModel):
    """FeatureStore entity for the PicPay Assist domain."""

    __redis_key_template__ = "picpay_assist_features:{user_id}"

    user_id: str = ContextField(
        description="Usuário (chave da feature row)",
        is_key_component=True,
    )

    velocity_pix_24h: int = ContextField(
        description="Feature: nº de Pix nas últimas 24h",
        index="numeric",
    )

    valor_medio_p2p: float = ContextField(
        description="Feature: ticket médio P2P do usuário (BRL)",
        index="numeric",
        sortable=True,
    )

    valor_max_historico: float = ContextField(
        description="Feature: maior P2P já feito (BRL)",
        index="numeric",
    )

    num_contatos_confiaveis: int = ContextField(
        description="Feature: contatos confiáveis no grafo",
        index="numeric",
    )

    prior_golpe_count: int = ContextField(
        description="Feature: golpes em que já caiu (histórico)",
        index="numeric",
    )

    device_trust_score: float = ContextField(
        description="Feature: confiança do device (0-1)",
        index="numeric",
    )

    horario_tipico_inicio: int = ContextField(
        description="Feature: hora típica de início de atividade (0-23)",
        index="numeric",
    )

    horario_tipico_fim: int = ContextField(
        description="Feature: hora típica de fim de atividade (0-23)",
        index="numeric",
    )

    perfil_risco: str = ContextField(
        description="Feature: perfil de risco do usuário: baixo, medio, alto",
        index="tag",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização das features (ISO)",
        sortable=True,
    )

    owner: Any = ContextRelationship(
        description="Usuário dono das features",
        target="User",
        source_field="user_id",
    )
