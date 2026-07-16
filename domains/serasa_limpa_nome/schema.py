"""Limpa Nome IA — definições de modelo de dados (single source of truth).

Domínio de consumer credit / score / Limpa Nome real-time. Cada EntitySpec
governa:
  • Geração do ContextModel
  • Criação do índice Redis Search via Context Retriever
  • Geração de dados sintéticos
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
    # ── Consumer (Cliente Serasa) ───────────────────────────────
    EntitySpec(
        class_name="Consumer",
        redis_key_template="serasa_limpa_nome_consumer:{consumer_id}",
        file_name="consumers.jsonl",
        id_field="consumer_id",
        fields=(
            FieldSpec("consumer_id", "str", "Identificador único do consumidor", is_key_component=True),
            FieldSpec("name", "str", "Nome completo", index="text", weight=2.0),
            FieldSpec("cpf_masked", "str", "CPF mascarado (ex: ***.456.789-**)"),
            FieldSpec("email", "str", "Email cadastrado", index="text", weight=1.5, no_stem=True),
            FieldSpec("phone", "str | None", "Celular cadastrado"),
            FieldSpec("city", "str", "Cidade", index="tag"),
            FieldSpec("state", "str", "Estado (UF)", index="tag"),
            FieldSpec("score", "int", "Score Serasa atual (0-1000)", index="numeric", sortable=True),
            FieldSpec("score_faixa", "str", "Faixa: muito_baixo, baixo, regular, bom, excelente", index="tag"),
            FieldSpec("monitoramento_ativo", "str", "Monitoramento ativo: sim, nao", index="tag"),
            FieldSpec("premium_tier", "str", "Tier: free, premium, premium_plus", index="tag"),
            FieldSpec("premium_since_years", "int", "Anos como Premium (0 se free)", index="numeric"),
            FieldSpec("cadastro_positivo_ativo", "str", "Cadastro Positivo ativo: sim, nao", index="tag"),
            FieldSpec("antifraude_ativo", "str", "Proteção antifraude ativa: sim, nao", index="tag"),
        ),
        relationships=(
            RelationshipSpec("debts", "Dívidas negativadas do consumidor", "consumer_id", "list[Debt]"),
            RelationshipSpec("pending_debts", "Pendências descobertas em real-time", "consumer_id", "list[PendingDebt]"),
        ),
    ),
    # ── Creditor (Credor parceiro) ──────────────────────────────
    EntitySpec(
        class_name="Creditor",
        redis_key_template="serasa_limpa_nome_creditor:{creditor_id}",
        file_name="creditors.jsonl",
        id_field="creditor_id",
        fields=(
            FieldSpec("creditor_id", "str", "Identificador único do credor", is_key_component=True),
            FieldSpec("name", "str", "Nome do credor", index="text", weight=2.0),
            FieldSpec("setor", "str", "Setor: telecom, varejo, financeiro, energia, streaming, saude", index="tag"),
            FieldSpec("partner_level", "str", "Nível parceria: full, legacy, realtime_only", index="tag"),
            FieldSpec("max_discount_pct", "int", "Desconto máximo praticado por esse credor (%)", index="numeric"),
            FieldSpec("supports_realtime_query", "str", "Suporta consulta real-time: sim, nao", index="tag"),
        ),
    ),
    # ── Debt (Dívida já negativada) ─────────────────────────────
    EntitySpec(
        class_name="Debt",
        redis_key_template="serasa_limpa_nome_debt:{debt_id}",
        file_name="debts.jsonl",
        id_field="debt_id",
        fields=(
            FieldSpec("debt_id", "str", "Identificador único da dívida", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor devedor", index="tag"),
            FieldSpec("creditor_id", "str", "Credor", index="tag"),
            FieldSpec("descricao", "str", "Descrição da dívida", index="text"),
            FieldSpec("valor_original", "float", "Valor original (BRL)", index="numeric"),
            FieldSpec("valor_atualizado", "float", "Valor atualizado com juros (BRL)", index="numeric", sortable=True),
            FieldSpec("data_origem", "str", "Data da dívida (ISO)", sortable=True),
            FieldSpec("dias_em_atraso", "int", "Dias em atraso", index="numeric", sortable=True),
            FieldSpec("is_negativada", "str", "Aparece como negativação ativa: sim, nao", index="tag"),
            FieldSpec("status", "str", "Status: ativa, em_negociacao, quitada, contestada", index="tag"),
            FieldSpec("score_impact_estimate", "int", "Impacto estimado no score se quitada (pontos)", index="numeric"),
        ),
        relationships=(
            RelationshipSpec("consumer", "Consumidor", "consumer_id", "Consumer"),
            RelationshipSpec("creditor", "Credor", "creditor_id", "Creditor"),
        ),
    ),
    # ── PendingDebt (Pendência descoberta via real-time) ────────
    EntitySpec(
        class_name="PendingDebt",
        redis_key_template="serasa_limpa_nome_pending_debt:{pending_id}",
        file_name="pending_debts.jsonl",
        id_field="pending_id",
        fields=(
            FieldSpec("pending_id", "str", "Identificador único da pendência", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor", index="tag"),
            FieldSpec("creditor_id", "str", "Credor parceiro que reportou", index="tag"),
            FieldSpec("descricao", "str", "Descrição (ex: fatura final pós-cancelamento)", index="text"),
            FieldSpec("valor", "float", "Valor da pendência (BRL)", index="numeric", sortable=True),
            FieldSpec("data_origem", "str", "Data da pendência original (ISO)", sortable=True),
            FieldSpec("descoberto_em", "str", "Timestamp da descoberta via real-time (ISO)", sortable=True),
            FieldSpec("dias_silencioso", "int", "Há quantos dias está pendurada sem virar negativação", index="numeric"),
            FieldSpec("status", "str", "Status: aberta, em_negociacao, quitada, ignorada", index="tag"),
            FieldSpec("source", "str", "Origem: realtime_discovery, legacy_import, user_added", index="tag"),
            FieldSpec("would_negativate_in_days", "int", "Em quantos dias viraria negativação se ignorada", index="numeric"),
        ),
        relationships=(
            RelationshipSpec("consumer", "Consumidor", "consumer_id", "Consumer"),
            RelationshipSpec("creditor", "Credor", "creditor_id", "Creditor"),
        ),
    ),
    # ── Proposal (Oferta de negociação) ─────────────────────────
    EntitySpec(
        class_name="Proposal",
        redis_key_template="serasa_limpa_nome_proposal:{proposal_id}",
        file_name="proposals.jsonl",
        id_field="proposal_id",
        fields=(
            FieldSpec("proposal_id", "str", "Identificador único da proposta", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor alvo", index="tag"),
            FieldSpec("creditor_id", "str", "Credor ofertante", index="tag"),
            FieldSpec("debt_id", "str | None", "Dívida associada (se for negativada)", index="tag"),
            FieldSpec("pending_id", "str | None", "Pendência associada (se for real-time)", index="tag"),
            FieldSpec("valor_original", "float", "Valor original da dívida/pendência (BRL)", index="numeric"),
            FieldSpec("valor_com_desconto", "float", "Valor após desconto (BRL)", index="numeric"),
            FieldSpec("desconto_percentual", "int", "Desconto aplicado (%)", index="numeric", sortable=True),
            FieldSpec("modalidade", "str", "à_vista, parcelado_2x, parcelado_3x, parcelado_6x, parcelado_12x", index="tag"),
            FieldSpec("valor_parcela", "float", "Valor da parcela (BRL)", index="numeric"),
            FieldSpec("validade", "str", "Data de validade da oferta (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: ativa, aceita, expirada, recusada", index="tag"),
        ),
        relationships=(
            RelationshipSpec("consumer", "Consumidor alvo", "consumer_id", "Consumer"),
            RelationshipSpec("creditor", "Credor ofertante", "creditor_id", "Creditor"),
        ),
    ),
    # ── ScoreHistory (Snapshots do score) ───────────────────────
    EntitySpec(
        class_name="ScoreHistory",
        redis_key_template="serasa_limpa_nome_score_history:{history_id}",
        file_name="score_history.jsonl",
        id_field="history_id",
        fields=(
            FieldSpec("history_id", "str", "Identificador único do snapshot", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor", index="tag"),
            FieldSpec("mes_referencia", "str", "Mês de referência (YYYY-MM)", index="tag", sortable=True),
            FieldSpec("score", "int", "Score no mês", index="numeric"),
            FieldSpec("faixa", "str", "Faixa: muito_baixo, baixo, regular, bom, excelente", index="tag"),
            FieldSpec("variacao", "int", "Variação em relação ao mês anterior (+/-)"),
            FieldSpec("fator_principal", "str", "Principal fator do mês", index="text"),
        ),
    ),
    # ── ScoreFactor (O que afeta o score AGORA) ─────────────────
    EntitySpec(
        class_name="ScoreFactor",
        redis_key_template="serasa_limpa_nome_score_factor:{factor_id}",
        file_name="score_factors.jsonl",
        id_field="factor_id",
        fields=(
            FieldSpec("factor_id", "str", "Identificador único do fator", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor", index="tag"),
            FieldSpec("tipo", "str", "Tipo: positivo, negativo", index="tag"),
            FieldSpec("descricao", "str", "Descrição (ex: 'Histórico de pagamento em dia')", index="text"),
            FieldSpec("peso_estimado", "int", "Peso estimado no score (pontos)", index="numeric"),
            FieldSpec("categoria", "str", "Categoria: pagamento, diversidade, tempo, renda, cadastro_positivo, consultas", index="tag"),
        ),
    ),
    # ── Inquiry (Consulta ao CPF) ───────────────────────────────
    EntitySpec(
        class_name="Inquiry",
        redis_key_template="serasa_limpa_nome_inquiry:{inquiry_id}",
        file_name="inquiries.jsonl",
        id_field="inquiry_id",
        fields=(
            FieldSpec("inquiry_id", "str", "Identificador único da consulta", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor consultado", index="tag"),
            FieldSpec("consultor", "str", "Quem consultou (banco, varejo, etc)", index="text", weight=2.0),
            FieldSpec("consultor_setor", "str", "Setor do consultor", index="tag"),
            FieldSpec("motivo", "str", "Motivo declarado: aprovacao_credito, cadastro, contratacao, monitoramento", index="tag"),
            FieldSpec("data_consulta", "str", "Timestamp ISO da consulta", sortable=True),
            FieldSpec("autorizada", "str", "Cliente autorizou explicitamente: sim, nao, parcial", index="tag"),
            FieldSpec("status", "str", "Status: registrada, contestada, em_disputa, resolvida", index="tag"),
            FieldSpec("severidade_anomalia", "int", "0-10 (0=normal, 10=fortemente suspeita)", index="numeric"),
        ),
    ),
    # ── FraudAlert (Alerta de fraude) ───────────────────────────
    EntitySpec(
        class_name="FraudAlert",
        redis_key_template="serasa_limpa_nome_fraud_alert:{alert_id}",
        file_name="fraud_alerts.jsonl",
        id_field="alert_id",
        fields=(
            FieldSpec("alert_id", "str", "Identificador único do alerta", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor", index="tag"),
            FieldSpec("inquiry_id", "str | None", "Consulta associada (se aplicável)", index="tag"),
            FieldSpec("tipo", "str", "Tipo: consulta_suspeita, padrao_anomalo, cpf_em_lista_vazada, tentativa_credito_negada", index="tag"),
            FieldSpec("severidade", "str", "Severidade: baixa, media, alta, critica", index="tag"),
            FieldSpec("data_alerta", "str", "Timestamp ISO", sortable=True),
            FieldSpec("status", "str", "Status: aberto, em_analise, resolvido_falso_positivo, resolvido_confirmado", index="tag"),
            FieldSpec("descricao", "str", "Descrição do alerta", index="text"),
            FieldSpec("acao_sugerida", "str | None", "Ação sugerida (ex: contestar consulta, bloquear acesso)"),
        ),
    ),
    # ── NegotiationHistory (Histórico de acordos) ───────────────
    EntitySpec(
        class_name="NegotiationHistory",
        redis_key_template="serasa_limpa_nome_negotiation:{negotiation_id}",
        file_name="negotiation_history.jsonl",
        id_field="negotiation_id",
        fields=(
            FieldSpec("negotiation_id", "str", "Identificador único do acordo", is_key_component=True),
            FieldSpec("consumer_id", "str", "Consumidor", index="tag"),
            FieldSpec("creditor_id", "str", "Credor", index="tag"),
            FieldSpec("proposal_id", "str | None", "Proposta aceita (se aplicável)", index="tag"),
            FieldSpec("debt_id", "str | None", "Dívida quitada (se negativada)", index="tag"),
            FieldSpec("pending_id", "str | None", "Pendência quitada (se real-time)", index="tag"),
            FieldSpec("data_acordo", "str", "Timestamp ISO do acordo", sortable=True),
            FieldSpec("valor_acordado", "float", "Valor final acordado (BRL)", index="numeric"),
            FieldSpec("modalidade", "str", "Modalidade de pagamento", index="tag"),
            FieldSpec("protocolo", "str", "Protocolo do acordo (LN-AAAAMMDD-XXXXXX)", index="text"),
            FieldSpec("status_pagamento", "str", "Status: aguardando, em_dia, atrasado, quitado", index="tag"),
            FieldSpec("score_impact_real", "int | None", "Impacto real medido após N dias (pontos)"),
        ),
    ),
    # ── Policy (Políticas do Serasa) ────────────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="serasa_limpa_nome_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: limpa_nome, score, monitoramento, antifraude, lgpd, premium", index="tag"),
            FieldSpec("content", "str", "Texto completo da política", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Embedding vetorial",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
