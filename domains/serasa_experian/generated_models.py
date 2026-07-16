"""Generated Context Surface models for the Serasa Experian domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Consumer(ContextModel):
    """Consumer entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_consumer:{consumer_id}"

    consumer_id: str = ContextField(
        description="Identificador único do consumidor",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome completo",
        index="text",
        weight=2.0,
    )

    cpf_masked: str = ContextField(
        description="CPF mascarado (ex: ***.456.789-**)",
    )

    email: str = ContextField(
        description="Email cadastrado",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    phone: str | None = ContextField(
        description="Celular cadastrado",
    )

    city: str = ContextField(
        description="Cidade",
        index="tag",
    )

    state: str = ContextField(
        description="Estado (UF)",
        index="tag",
    )

    score: int = ContextField(
        description="Serasa Score atual (0-1000)",
        index="numeric",
        sortable=True,
    )

    score_faixa: str = ContextField(
        description="Faixa oficial: baixo, regular, bom, excelente",
        index="tag",
    )

    monitoramento_ativo: str = ContextField(
        description="Monitoramento ativo: sim, nao",
        index="tag",
    )

    premium_tier: str = ContextField(
        description="Tier: free, premium, premium_plus",
        index="tag",
    )

    premium_since_years: int = ContextField(
        description="Anos como Premium (0 se free)",
        index="numeric",
    )

    cadastro_positivo_ativo: str = ContextField(
        description="Cadastro Positivo ativo: sim, nao",
        index="tag",
    )

    antifraude_ativo: str = ContextField(
        description="Proteção antifraude ativa: sim, nao",
        index="tag",
    )

    renda_mensal_estimada: float = ContextField(
        description="Renda mensal estimada (BRL)",
        index="numeric",
        sortable=True,
    )

    meta_faixa: str = ContextField(
        description="Meta de faixa/score que o consumidor persegue",
        index="tag",
    )

    debts: Any = ContextRelationship(
        description="Dívidas negativadas do consumidor",
        target="Debt",
        source_field="consumer_id",
    )

    pending_debts: Any = ContextRelationship(
        description="Pendências descobertas em real-time",
        target="PendingDebt",
        source_field="consumer_id",
    )

    features: Any = ContextRelationship(
        description="Feature row online do consumidor (Serasa Score)",
        target="CreditFeatures",
        source_field="consumer_id",
    )


class Creditor(ContextModel):
    """Creditor entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_creditor:{creditor_id}"

    creditor_id: str = ContextField(
        description="Identificador único do credor",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome do credor",
        index="text",
        weight=2.0,
    )

    setor: str = ContextField(
        description="Setor: telecom, varejo, financeiro, energia, streaming, saude",
        index="tag",
    )

    partner_level: str = ContextField(
        description="Nível parceria: full, legacy, realtime_only",
        index="tag",
    )

    max_discount_pct: int = ContextField(
        description="Desconto máximo praticado por esse credor (%)",
        index="numeric",
    )

    supports_realtime_query: str = ContextField(
        description="Suporta consulta real-time: sim, nao",
        index="tag",
    )


class Debt(ContextModel):
    """Debt entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_debt:{debt_id}"

    debt_id: str = ContextField(
        description="Identificador único da dívida",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor devedor",
        index="tag",
    )

    creditor_id: str = ContextField(
        description="Credor",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição da dívida",
        index="text",
    )

    valor_original: float = ContextField(
        description="Valor original (BRL)",
        index="numeric",
    )

    valor_atualizado: float = ContextField(
        description="Valor atualizado com juros (BRL)",
        index="numeric",
        sortable=True,
    )

    data_origem: str = ContextField(
        description="Data da dívida (ISO)",
        sortable=True,
    )

    dias_em_atraso: int = ContextField(
        description="Dias em atraso",
        index="numeric",
        sortable=True,
    )

    is_negativada: str = ContextField(
        description="Aparece como negativação ativa: sim, nao",
        index="tag",
    )

    status: str = ContextField(
        description="Status: ativa, em_negociacao, quitada, contestada",
        index="tag",
    )

    score_impact_estimate: int = ContextField(
        description="Impacto estimado no score se quitada (pontos)",
        index="numeric",
    )

    consumer: Any = ContextRelationship(
        description="Consumidor",
        target="Consumer",
        source_field="consumer_id",
    )

    creditor: Any = ContextRelationship(
        description="Credor",
        target="Creditor",
        source_field="creditor_id",
    )


class PendingDebt(ContextModel):
    """PendingDebt entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_pending_debt:{pending_id}"

    pending_id: str = ContextField(
        description="Identificador único da pendência",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
        index="tag",
    )

    creditor_id: str = ContextField(
        description="Credor parceiro que reportou",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição (ex: fatura final pós-cancelamento)",
        index="text",
    )

    valor: float = ContextField(
        description="Valor da pendência (BRL)",
        index="numeric",
        sortable=True,
    )

    data_origem: str = ContextField(
        description="Data da pendência original (ISO)",
        sortable=True,
    )

    descoberto_em: str = ContextField(
        description="Timestamp da descoberta via real-time (ISO)",
        sortable=True,
    )

    dias_silencioso: int = ContextField(
        description="Há quantos dias está pendurada sem virar negativação",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: aberta, em_negociacao, quitada, ignorada",
        index="tag",
    )

    source: str = ContextField(
        description="Origem: realtime_discovery, legacy_import, user_added",
        index="tag",
    )

    would_negativate_in_days: int = ContextField(
        description="Em quantos dias viraria negativação se ignorada",
        index="numeric",
    )

    consumer: Any = ContextRelationship(
        description="Consumidor",
        target="Consumer",
        source_field="consumer_id",
    )

    creditor: Any = ContextRelationship(
        description="Credor",
        target="Creditor",
        source_field="creditor_id",
    )


class Proposal(ContextModel):
    """Proposal entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_proposal:{proposal_id}"

    proposal_id: str = ContextField(
        description="Identificador único da proposta",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor alvo",
        index="tag",
    )

    creditor_id: str = ContextField(
        description="Credor ofertante",
        index="tag",
    )

    debt_id: str | None = ContextField(
        description="Dívida associada (se for negativada)",
        index="tag",
    )

    pending_id: str | None = ContextField(
        description="Pendência associada (se for real-time)",
        index="tag",
    )

    valor_original: float = ContextField(
        description="Valor original da dívida/pendência (BRL)",
        index="numeric",
    )

    valor_com_desconto: float = ContextField(
        description="Valor após desconto (BRL)",
        index="numeric",
    )

    desconto_percentual: int = ContextField(
        description="Desconto aplicado (%)",
        index="numeric",
        sortable=True,
    )

    modalidade: str = ContextField(
        description="à_vista, parcelado_2x, parcelado_3x, parcelado_6x, parcelado_12x",
        index="tag",
    )

    valor_parcela: float = ContextField(
        description="Valor da parcela (BRL)",
        index="numeric",
    )

    validade: str = ContextField(
        description="Data de validade da oferta (ISO)",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: ativa, aceita, expirada, recusada",
        index="tag",
    )

    consumer: Any = ContextRelationship(
        description="Consumidor alvo",
        target="Consumer",
        source_field="consumer_id",
    )

    creditor: Any = ContextRelationship(
        description="Credor ofertante",
        target="Creditor",
        source_field="creditor_id",
    )


class ScoreHistory(ContextModel):
    """ScoreHistory entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_score_history:{history_id}"

    history_id: str = ContextField(
        description="Identificador único do snapshot",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
        index="tag",
    )

    mes_referencia: str = ContextField(
        description="Mês de referência (YYYY-MM)",
        index="tag",
        sortable=True,
    )

    score: int = ContextField(
        description="Score no mês",
        index="numeric",
    )

    faixa: str = ContextField(
        description="Faixa oficial: baixo, regular, bom, excelente",
        index="tag",
    )

    variacao: int = ContextField(
        description="Variação em relação ao mês anterior (+/-)",
    )

    fator_principal: str = ContextField(
        description="Principal fator do mês",
        index="text",
    )


class ScoreFactor(ContextModel):
    """ScoreFactor entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_score_factor:{factor_id}"

    factor_id: str = ContextField(
        description="Identificador único do fator",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: positivo, negativo",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição (ex: 'Cadastro Positivo ativo')",
        index="text",
    )

    peso_estimado: int = ContextField(
        description="Peso estimado no score (pontos)",
        index="numeric",
    )

    categoria: str = ContextField(
        description="Categoria (peso oficial Serasa Score): cadastro_positivo, experiencia_mercado, dividas, busca_credito, dados_cadastrais, contratos",
        index="tag",
    )


class Inquiry(ContextModel):
    """Inquiry entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_inquiry:{inquiry_id}"

    inquiry_id: str = ContextField(
        description="Identificador único da consulta",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor consultado",
        index="tag",
    )

    consultor: str = ContextField(
        description="Quem consultou (banco, varejo, etc)",
        index="text",
        weight=2.0,
    )

    consultor_setor: str = ContextField(
        description="Setor do consultor",
        index="tag",
    )

    motivo: str = ContextField(
        description="Motivo declarado: aprovacao_credito, cadastro, contratacao, monitoramento",
        index="tag",
    )

    data_consulta: str = ContextField(
        description="Timestamp ISO da consulta",
        sortable=True,
    )

    autorizada: str = ContextField(
        description="Cliente autorizou explicitamente: sim, nao, parcial",
        index="tag",
    )

    status: str = ContextField(
        description="Status: registrada, contestada, em_disputa, resolvida",
        index="tag",
    )

    severidade_anomalia: int = ContextField(
        description="0-10 (0=normal, 10=fortemente suspeita)",
        index="numeric",
    )


class FraudAlert(ContextModel):
    """FraudAlert entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_fraud_alert:{alert_id}"

    alert_id: str = ContextField(
        description="Identificador único do alerta",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
        index="tag",
    )

    inquiry_id: str | None = ContextField(
        description="Consulta associada (se aplicável)",
        index="tag",
    )

    tipo: str = ContextField(
        description="Tipo: consulta_suspeita, padrao_anomalo, cpf_em_lista_vazada, tentativa_credito_negada",
        index="tag",
    )

    severidade: str = ContextField(
        description="Severidade: baixa, media, alta, critica",
        index="tag",
    )

    data_alerta: str = ContextField(
        description="Timestamp ISO",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: aberto, em_analise, resolvido_falso_positivo, resolvido_confirmado",
        index="tag",
    )

    descricao: str = ContextField(
        description="Descrição do alerta",
        index="text",
    )

    acao_sugerida: str | None = ContextField(
        description="Ação sugerida (ex: contestar consulta, bloquear acesso)",
    )


class NegotiationHistory(ContextModel):
    """NegotiationHistory entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_negotiation:{negotiation_id}"

    negotiation_id: str = ContextField(
        description="Identificador único do acordo",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
        index="tag",
    )

    creditor_id: str = ContextField(
        description="Credor",
        index="tag",
    )

    proposal_id: str | None = ContextField(
        description="Proposta aceita (se aplicável)",
        index="tag",
    )

    debt_id: str | None = ContextField(
        description="Dívida quitada (se negativada)",
        index="tag",
    )

    pending_id: str | None = ContextField(
        description="Pendência quitada (se real-time)",
        index="tag",
    )

    data_acordo: str = ContextField(
        description="Timestamp ISO do acordo",
        sortable=True,
    )

    valor_acordado: float = ContextField(
        description="Valor final acordado (BRL)",
        index="numeric",
    )

    modalidade: str = ContextField(
        description="Modalidade de pagamento",
        index="tag",
    )

    protocolo: str = ContextField(
        description="Protocolo do acordo (SX-AAAAMMDD-XXXXXX)",
        index="text",
    )

    status_pagamento: str = ContextField(
        description="Status: aguardando, em_dia, atrasado, quitado",
        index="tag",
    )

    score_impact_real: int | None = ContextField(
        description="Impacto real medido após N dias (pontos)",
    )


class CreditFeatures(ContextModel):
    """CreditFeatures entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_features:{consumer_id}"

    consumer_id: str = ContextField(
        description="Consumidor (chave da feature row)",
        is_key_component=True,
    )

    f_cadastro_positivo: float = ContextField(
        description="Feature: força do Cadastro Positivo (0-1)",
    )

    f_experiencia_mercado: float = ContextField(
        description="Feature: experiência de mercado (0-1)",
    )

    f_dividas: float = ContextField(
        description="Feature: saúde de dívidas, 1=sem dívidas (0-1)",
    )

    f_busca_credito: float = ContextField(
        description="Feature: comportamento de busca de crédito, 1=baixa busca (0-1)",
    )

    f_dados_cadastrais: float = ContextField(
        description="Feature: completude dos dados cadastrais (0-1)",
    )

    f_contratos: float = ContextField(
        description="Feature: histórico de contratos firmados (0-1)",
    )

    score_calculado: int = ContextField(
        description="Score recalculado a partir das 6 features ponderadas",
    )

    faixa: str = ContextField(
        description="Faixa oficial derivada: baixo, regular, bom, excelente",
    )

    propensao_cartao: float = ContextField(
        description="Feature: propensão a cartão de crédito (0-1)",
    )

    propensao_emprestimo: float = ContextField(
        description="Feature: propensão a empréstimo pessoal (0-1)",
    )

    propensao_consignado: float = ContextField(
        description="Feature: propensão a consignado (0-1)",
    )

    renda_estimada: float = ContextField(
        description="Feature: renda mensal estimada (BRL)",
    )

    inadimplencia_setor_atual: float = ContextField(
        description="Feature: inadimplência no setor (0-1, atualizável no recompute)",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização das features (ISO)",
    )

    consumer: Any = ContextRelationship(
        description="Consumidor dono das features",
        target="Consumer",
        source_field="consumer_id",
    )


class CadastroPositivo(ContextModel):
    """CadastroPositivo entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_cadastro_positivo:{record_id}"

    record_id: str = ContextField(
        description="Identificador único do registro de pagamento",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor dono do histórico",
        index="tag",
    )

    categoria: str = ContextField(
        description="Categoria: utilities, telecom, streaming, educacao, cartao, financiamento, seguro",
        index="tag",
    )

    credor: str = ContextField(
        description="Nome do credor/empresa (ex: Enel, Vivo, Netflix)",
    )

    valor: float = ContextField(
        description="Valor médio mensal pago (BRL)",
    )

    status: str = ContextField(
        description="Status do histórico: em_dia, quitado",
    )

    meses_em_dia: int = ContextField(
        description="Quantos meses consecutivos pago em dia",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização do registro (ISO)",
    )

    consumer: Any = ContextRelationship(
        description="Consumidor dono do histórico",
        target="Consumer",
        source_field="consumer_id",
    )


class CreditOffer(ContextModel):
    """CreditOffer entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_offer:{offer_id}"

    offer_id: str = ContextField(
        description="Identificador único da oferta",
        is_key_component=True,
    )

    partner_name: str = ContextField(
        description="Nome do parceiro ofertante",
    )

    produto: str = ContextField(
        description="Produto: cartao, emprestimo_pessoal, consignado, fgts, conta_digital, cartao_negativado",
    )

    taxa_min_aa: float = ContextField(
        description="Taxa mínima ao ano (% a.a.)",
    )

    faixa_minima: str = ContextField(
        description="Faixa mínima de score exigida: baixo, regular, bom, excelente",
    )

    renda_minima: float = ContextField(
        description="Renda mínima exigida (BRL)",
    )

    publico_alvo: str = ContextField(
        description="Público-alvo: bom, excelente, negativado",
    )

    valor_max: float = ContextField(
        description="Valor/limite máximo do produto (BRL)",
    )

    status: str = ContextField(
        description="Status: ativa, pausada, expirada",
    )


class OfferMatch(ContextModel):
    """OfferMatch entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_offer_match:{match_id}"

    match_id: str = ContextField(
        description="Identificador único do match",
        is_key_component=True,
    )

    consumer_id: str = ContextField(
        description="Consumidor",
    )

    offer_id: str = ContextField(
        description="Oferta rankeada",
    )

    partner_name: str = ContextField(
        description="Nome do parceiro",
    )

    produto: str = ContextField(
        description="Produto da oferta",
    )

    approval_odds: float = ContextField(
        description="Probabilidade estimada de aprovação (0-1)",
    )

    fit_score: float = ContextField(
        description="Aderência ao perfil (0-1)",
    )

    ranked_at: str = ContextField(
        description="Timestamp ISO do ranqueamento",
    )

    explicabilidade: str = ContextField(
        description="Racional do ranqueamento",
    )


class Policy(ContextModel):
    """Policy entity for the Serasa Experian domain."""

    __redis_key_template__ = "serasa_experian_policy:{policy_id}"

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
        description="Categoria: score, ecred, limpa_nome, monitoramento, antifraude, lgpd, premium",
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
