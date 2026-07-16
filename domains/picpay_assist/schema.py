"""PicPay Assist — definições de modelo de dados (single source of truth).

Carteira digital social: P2P com feed social, cashback, Cofrinhos, cartão,
boletos e sinalização anti-golpe. Cada EntitySpec governa:
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
    # ── User (dono da carteira) ─────────────────────────────────
    EntitySpec(
        class_name="User",
        redis_key_template="picpay_assist_user:{user_id}",
        file_name="users.jsonl",
        id_field="user_id",
        fields=(
            FieldSpec("user_id", "str", "Identificador único do usuário", is_key_component=True),
            FieldSpec("nome", "str", "Nome completo", index="text", weight=2.0),
            FieldSpec("handle", "str", "@usuário do PicPay", index="text", weight=1.5, no_stem=True),
            FieldSpec("cpf_masked", "str", "CPF mascarado"),
            FieldSpec("email", "str", "Email cadastrado", index="text", weight=1.5, no_stem=True),
            FieldSpec("cidade", "str", "Cidade", index="tag"),
            FieldSpec("saldo_carteira", "float", "Saldo na carteira PicPay (BRL)", index="numeric", sortable=True),
            FieldSpec("cashback_disponivel", "float", "Cashback acumulado disponível (BRL)", index="numeric", sortable=True),
            FieldSpec("membro_desde", "str", "Ano de cadastro (YYYY)"),
            FieldSpec("nivel", "str", "Nível: membro, prata, ouro, diamante", index="tag"),
            FieldSpec("pix_key_principal", "str", "Chave Pix principal mascarada"),
        ),
        relationships=(
            RelationshipSpec("contacts", "Contatos sociais do usuário", "user_id", "list[Contact]"),
            RelationshipSpec("transactions", "Transações do usuário", "user_id", "list[Transaction]"),
            RelationshipSpec("cofrinhos", "Cofrinhos (metas) do usuário", "user_id", "list[Cofrinho]"),
            RelationshipSpec("features", "Features online (feature store) do usuário", "user_id", "FeatureStore"),
        ),
    ),
    # ── Contact (grafo social de pagamentos) ────────────────────
    EntitySpec(
        class_name="Contact",
        redis_key_template="picpay_assist_contact:{contact_id}",
        file_name="contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Identificador único do contato", is_key_component=True),
            FieldSpec("user_id", "str", "Dono da agenda", index="tag"),
            FieldSpec("nome", "str", "Nome do contato", index="text", weight=2.0),
            FieldSpec("handle", "str", "@ do contato no PicPay", index="text", no_stem=True),
            FieldSpec("relacao", "str", "Relação: amigo, familia, republica, trabalho, desconhecido", index="tag"),
            FieldSpec("is_frequente", "str", "Contato frequente: sim, nao", index="tag"),
            FieldSpec("trust_level", "str", "Confiança: confiavel, novo, suspeito", index="tag"),
            FieldSpec("vezes_transacionado", "int", "Quantas vezes já transacionou", index="numeric", sortable=True),
            FieldSpec("ultima_interacao", "str", "Timestamp ISO da última transação", sortable=True),
        ),
        relationships=(
            RelationshipSpec("owner", "Dono da agenda", "user_id", "User"),
        ),
    ),
    # ── Transaction (feed social de pagamentos) ─────────────────
    EntitySpec(
        class_name="Transaction",
        redis_key_template="picpay_assist_transaction:{txn_id}",
        file_name="transactions.jsonl",
        id_field="txn_id",
        fields=(
            FieldSpec("txn_id", "str", "Identificador único da transação", is_key_component=True),
            FieldSpec("user_id", "str", "Dono da transação", index="tag"),
            FieldSpec("counterparty_id", "str | None", "Contato da outra ponta", index="tag"),
            FieldSpec("counterparty_nome", "str", "Nome da outra ponta", index="text"),
            FieldSpec("tipo", "str", "Tipo: p2p_enviado, p2p_recebido, pix, compra, cashback, cofrinho, boleto", index="tag"),
            FieldSpec("valor", "float", "Valor da transação (BRL)", index="numeric", sortable=True),
            FieldSpec("tag", "str | None", "Tag social (ex: churrasco, aluguel, rolê)", index="text"),
            FieldSpec("emoji", "str | None", "Emoji social da transação"),
            FieldSpec("status", "str", "Status: concluida, pendente, solicitada, bloqueada", index="tag"),
            FieldSpec("data", "str", "Timestamp ISO da transação", sortable=True),
            FieldSpec("is_split", "str", "Faz parte de um racha: sim, nao", index="tag"),
            FieldSpec("split_group_id", "str | None", "ID do grupo de racha", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Dono da transação", "user_id", "User"),
        ),
    ),
    # ── CashbackEvent (motor de cashback) ───────────────────────
    EntitySpec(
        class_name="CashbackEvent",
        redis_key_template="picpay_assist_cashback:{cashback_id}",
        file_name="cashback_events.jsonl",
        id_field="cashback_id",
        fields=(
            FieldSpec("cashback_id", "str", "Identificador único do cashback", is_key_component=True),
            FieldSpec("user_id", "str", "Usuário", index="tag"),
            FieldSpec("origem", "str", "Origem: compra, promo, indicacao, pix, parceiro", index="tag"),
            FieldSpec("descricao", "str", "Descrição (ex: 'Cashback iFood 5%')", index="text"),
            FieldSpec("valor", "float", "Valor do cashback (BRL)", index="numeric", sortable=True),
            FieldSpec("data", "str", "Timestamp ISO", sortable=True),
            FieldSpec("destino", "str", "Destino: disponivel, carteira, cofrinho", index="tag"),
            FieldSpec("status", "str", "Status: creditado, resgatado, expirado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Usuário", "user_id", "User"),
        ),
    ),
    # ── Cofrinho (metas de poupança) ────────────────────────────
    EntitySpec(
        class_name="Cofrinho",
        redis_key_template="picpay_assist_cofrinho:{cofrinho_id}",
        file_name="cofrinhos.jsonl",
        id_field="cofrinho_id",
        fields=(
            FieldSpec("cofrinho_id", "str", "Identificador único do cofrinho", is_key_component=True),
            FieldSpec("user_id", "str", "Usuário", index="tag"),
            FieldSpec("nome", "str", "Nome da meta (ex: 'Viagem Chile')", index="text", weight=2.0),
            FieldSpec("emoji", "str | None", "Emoji da meta"),
            FieldSpec("meta_valor", "float", "Valor-alvo da meta (BRL)", index="numeric", sortable=True),
            FieldSpec("saldo_atual", "float", "Quanto já guardou (BRL)", index="numeric", sortable=True),
            FieldSpec("rende_cdi_pct", "int", "Rendimento (% do CDI)", index="numeric"),
            FieldSpec("data_meta", "str", "Data-alvo da meta (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: ativo, concluido, pausado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Usuário", "user_id", "User"),
        ),
    ),
    # ── Card (cartão PicPay) ────────────────────────────────────
    EntitySpec(
        class_name="Card",
        redis_key_template="picpay_assist_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Identificador único do cartão", is_key_component=True),
            FieldSpec("user_id", "str", "Dono do cartão", index="tag"),
            FieldSpec("tipo", "str", "Tipo: debito, credito", index="tag"),
            FieldSpec("final", "str", "4 últimos dígitos"),
            FieldSpec("limite", "float", "Limite de crédito (BRL)", index="numeric"),
            FieldSpec("fatura_atual", "float", "Fatura atual em aberto (BRL)", index="numeric", sortable=True),
            FieldSpec("vencimento", "str", "Data de vencimento da fatura (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: ativo, bloqueado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Dono do cartão", "user_id", "User"),
        ),
    ),
    # ── Boleto (contas a pagar) ─────────────────────────────────
    EntitySpec(
        class_name="Boleto",
        redis_key_template="picpay_assist_boleto:{boleto_id}",
        file_name="boletos.jsonl",
        id_field="boleto_id",
        fields=(
            FieldSpec("boleto_id", "str", "Identificador único do boleto", is_key_component=True),
            FieldSpec("user_id", "str", "Usuário", index="tag"),
            FieldSpec("descricao", "str", "Descrição (ex: 'Conta de luz Enel')", index="text", weight=1.5),
            FieldSpec("beneficiario", "str", "Beneficiário", index="text"),
            FieldSpec("valor", "float", "Valor do boleto (BRL)", index="numeric", sortable=True),
            FieldSpec("vencimento", "str", "Data de vencimento (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: a_pagar, pago, vencido", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Usuário", "user_id", "User"),
        ),
    ),
    # ── SuspiciousFlag (anti-golpe do Pix) ──────────────────────
    EntitySpec(
        class_name="SuspiciousFlag",
        redis_key_template="picpay_assist_suspicious:{flag_id}",
        file_name="suspicious_flags.jsonl",
        id_field="flag_id",
        fields=(
            FieldSpec("flag_id", "str", "Identificador único da sinalização", is_key_component=True),
            FieldSpec("user_id", "str", "Usuário protegido", index="tag"),
            FieldSpec("target_type", "str", "Alvo: contato, chave_pix, transacao", index="tag"),
            FieldSpec("target_id", "str | None", "ID do alvo (contato/transação)", index="tag"),
            FieldSpec("target_label", "str", "Rótulo legível do alvo (ex: '@premios-caixa-2026')", index="text"),
            FieldSpec("motivo", "str", "Motivo da suspeita", index="text"),
            FieldSpec("padrao_detectado", "str", "Padrão: chave_recem_criada, valor_atipico, fora_do_grafo, urgencia_falsa, premio_falso", index="tag"),
            FieldSpec("severidade", "str", "Severidade: baixa, media, alta, critica", index="tag"),
            FieldSpec("data", "str", "Timestamp ISO", sortable=True),
            FieldSpec("status", "str", "Status: alerta, bloqueado, liberado, em_analise", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Usuário protegido", "user_id", "User"),
        ),
    ),
    # ── Policy (políticas / ajuda PicPay) ───────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="picpay_assist_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: pagamentos, cashback, cofrinho, seguranca, cartao, limites, lgpd", index="tag"),
            FieldSpec("content", "str", "Texto completo da política", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Embedding vetorial",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
    ),
    # ── FeatureStore (features online pro modelo de fraude) ─────
    # O coração do diferencial: features comportamentais online no Redis que o
    # modelo de scoring de fraude lê em tempo real (sub-ms) na hora de avaliar um Pix.
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="picpay_assist_features:{user_id}",
        file_name="feature_store.jsonl",
        id_field="user_id",
        fields=(
            FieldSpec("user_id", "str", "Usuário (chave da feature row)", is_key_component=True),
            FieldSpec("velocity_pix_24h", "int", "Feature: nº de Pix nas últimas 24h", index="numeric"),
            FieldSpec("valor_medio_p2p", "float", "Feature: ticket médio P2P do usuário (BRL)", index="numeric", sortable=True),
            FieldSpec("valor_max_historico", "float", "Feature: maior P2P já feito (BRL)", index="numeric"),
            FieldSpec("num_contatos_confiaveis", "int", "Feature: contatos confiáveis no grafo", index="numeric"),
            FieldSpec("prior_golpe_count", "int", "Feature: golpes em que já caiu (histórico)", index="numeric"),
            FieldSpec("device_trust_score", "float", "Feature: confiança do device (0-1)", index="numeric"),
            FieldSpec("horario_tipico_inicio", "int", "Feature: hora típica de início de atividade (0-23)", index="numeric"),
            FieldSpec("horario_tipico_fim", "int", "Feature: hora típica de fim de atividade (0-23)", index="numeric"),
            FieldSpec("perfil_risco", "str", "Feature: perfil de risco do usuário: baixo, medio, alto", index="tag"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização das features (ISO)", sortable=True),
        ),
        relationships=(
            RelationshipSpec("owner", "Usuário dono das features", "user_id", "User"),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
