"""Itaú Assist — definições de modelo de dados (single source of truth).

Cada EntitySpec governa:
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
    # ── Customer (Cliente) ──────────────────────────────────────
    EntitySpec(
        class_name="Customer",
        redis_key_template="itau_assist_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Identificador único do cliente", is_key_component=True),
            FieldSpec("name", "str", "Nome completo do cliente", index="text", weight=2.0),
            FieldSpec("cpf_masked", "str", "CPF mascarado (ex: ***.456.789-**)"),
            FieldSpec("email", "str", "Email do cliente", index="text", weight=1.5, no_stem=True),
            FieldSpec("phone", "str | None", "Celular cadastrado"),
            FieldSpec("account_status", "str", "Status: active, blocked, in_review", index="tag"),
            FieldSpec("tier", "str", "Segmento: pf_mass, uniclass, personnalite, private", index="tag"),
            FieldSpec("relationship_years", "int", "Anos de relacionamento com o banco", index="numeric", sortable=True),
            FieldSpec("city", "str", "Cidade do cliente", index="tag"),
            FieldSpec("default_address", "str | None", "Endereço residencial"),
            FieldSpec("perfil_investidor", "str", "Perfil de investidor: conservador, moderado, arrojado, sofisticado", index="tag"),
            FieldSpec("credit_score", "int", "Score interno Itaú (0-1000)", index="numeric", sortable=True),
            FieldSpec("account_created_at", "str", "Data de abertura de conta (ISO)"),
        ),
        relationships=(
            RelationshipSpec("accounts", "Contas do cliente", "customer_id", "list[Account]"),
            RelationshipSpec("cards", "Cartões do cliente", "customer_id", "list[Card]"),
        ),
    ),
    # ── Account (Conta Corrente / Poupança) ─────────────────────
    EntitySpec(
        class_name="Account",
        redis_key_template="itau_assist_account:{account_id}",
        file_name="accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Identificador único da conta", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente titular", index="tag"),
            FieldSpec("agencia", "str", "Número da agência"),
            FieldSpec("conta_numero", "str", "Número da conta com dígito"),
            FieldSpec("tipo", "str", "Tipo: corrente, poupanca, cdb", index="tag"),
            FieldSpec("saldo_disponivel", "float", "Saldo disponível em BRL", index="numeric", sortable=True),
            FieldSpec("saldo_aplicado", "float", "Saldo aplicado em investimentos (BRL)", index="numeric"),
            FieldSpec("limite_cheque_especial", "float", "Limite do cheque especial (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: active, blocked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente titular", "customer_id", "Customer"),
        ),
    ),
    # ── Card (Cartão de Crédito) ────────────────────────────────
    EntitySpec(
        class_name="Card",
        redis_key_template="itau_assist_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Identificador único do cartão", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente titular", index="tag"),
            FieldSpec("account_id", "str", "Conta vinculada", index="tag"),
            FieldSpec("bandeira", "str", "Bandeira: visa, mastercard, elo", index="tag"),
            FieldSpec("produto", "str", "Produto: click, itaucard, uniclass, personnalite, mastercard_black, visa_infinite", index="tag"),
            FieldSpec("numero_mascarado", "str", "Final mascarado (ex: ****1234)"),
            FieldSpec("limite_total", "float", "Limite total aprovado (BRL)", index="numeric"),
            FieldSpec("limite_usado", "float", "Limite atualmente utilizado (BRL)", index="numeric"),
            FieldSpec("limite_disponivel", "float", "Limite disponível para uso (BRL)", index="numeric"),
            FieldSpec("validade", "str", "Validade no formato MM/AA"),
            FieldSpec("status", "str", "Status: active, blocked, replaced", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente titular", "customer_id", "Customer"),
            RelationshipSpec("account", "Conta vinculada", "account_id", "Account"),
        ),
    ),
    # ── Transaction (Lançamento na fatura ou Pix) ───────────────
    EntitySpec(
        class_name="Transaction",
        redis_key_template="itau_assist_transaction:{transaction_id}",
        file_name="transactions.jsonl",
        id_field="transaction_id",
        fields=(
            FieldSpec("transaction_id", "str", "Identificador único da transação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente associado", index="tag"),
            FieldSpec("card_id", "str | None", "Cartão usado (se for compra com cartão)", index="tag"),
            FieldSpec("account_id", "str | None", "Conta envolvida (Pix, débito, transferência)", index="tag"),
            FieldSpec("billing_cycle_id", "str | None", "Fatura à qual pertence", index="tag"),
            FieldSpec("tipo", "str", "Tipo: compra_credito, pix_envio, pix_recebido, debito, anuidade, juros, estorno", index="tag"),
            FieldSpec("merchant", "str", "Estabelecimento ou contraparte", index="text", weight=1.5),
            FieldSpec("mcc", "str | None", "Merchant Category Code", index="tag"),
            FieldSpec("valor", "float", "Valor (positivo = saída, negativo = entrada)", index="numeric"),
            FieldSpec("parcelas_total", "int", "Total de parcelas (1 se à vista)"),
            FieldSpec("parcela_atual", "int", "Parcela atual"),
            FieldSpec("status", "str", "Status: aprovada, contestada, estornada, pendente", index="tag"),
            FieldSpec("data_compra", "str", "Timestamp ISO da compra", sortable=True),
            FieldSpec("data_lancamento", "str", "Timestamp ISO do lançamento na fatura", sortable=True),
            FieldSpec("is_recurring", "str", "Flag de recorrência: sim, nao", index="tag"),
            FieldSpec("recurring_label", "str | None", "Rótulo legível se recorrente (ex: Amazon Prime + Music)"),
            FieldSpec("location_city", "str | None", "Cidade da compra"),
            FieldSpec("dispute_id", "str | None", "Se contestada, ID da contestação", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
            RelationshipSpec("card", "Cartão", "card_id", "Card"),
            RelationshipSpec("account", "Conta", "account_id", "Account"),
        ),
    ),
    # ── BillingCycle (Fatura) ───────────────────────────────────
    EntitySpec(
        class_name="BillingCycle",
        redis_key_template="itau_assist_billing_cycle:{cycle_id}",
        file_name="billing_cycles.jsonl",
        id_field="cycle_id",
        fields=(
            FieldSpec("cycle_id", "str", "Identificador único da fatura", is_key_component=True),
            FieldSpec("card_id", "str", "Cartão da fatura", index="tag"),
            FieldSpec("customer_id", "str", "Cliente titular", index="tag"),
            FieldSpec("mes_referencia", "str", "Mês de referência (YYYY-MM)", index="tag"),
            FieldSpec("data_fechamento", "str", "Data de fechamento da fatura (ISO)"),
            FieldSpec("data_vencimento", "str", "Data de vencimento da fatura (ISO)"),
            FieldSpec("valor_total", "float", "Valor total da fatura (BRL)", index="numeric"),
            FieldSpec("pagamento_minimo", "float", "Valor do pagamento mínimo (BRL)", index="numeric"),
            FieldSpec("valor_pago", "float", "Valor já pago (BRL, 0 se aberta)", index="numeric"),
            FieldSpec("status", "str", "Status: aberta, fechada_aguardando_pagamento, paga, atrasada", index="tag"),
        ),
        relationships=(
            RelationshipSpec("card", "Cartão da fatura", "card_id", "Card"),
            RelationshipSpec("customer", "Cliente titular", "customer_id", "Customer"),
        ),
    ),
    # ── Dispute (Contestação) ───────────────────────────────────
    EntitySpec(
        class_name="Dispute",
        redis_key_template="itau_assist_dispute:{dispute_id}",
        file_name="disputes.jsonl",
        id_field="dispute_id",
        fields=(
            FieldSpec("dispute_id", "str", "Identificador único da contestação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente que abriu", index="tag"),
            FieldSpec("transaction_id", "str", "Transação contestada", index="tag"),
            FieldSpec("protocolo", "str", "Protocolo de atendimento", index="text"),
            FieldSpec("motivo", "str", "Motivo: nao_reconheco, duplicada, valor_divergente, produto_nao_recebido, fraude", index="tag"),
            FieldSpec("status", "str", "Status: aberta, em_analise, resolvida_favoravel, resolvida_contraria", index="tag"),
            FieldSpec("valor_contestado", "float", "Valor da contestação (BRL)", index="numeric"),
            FieldSpec("data_abertura", "str", "Timestamp ISO de abertura"),
            FieldSpec("data_resolucao", "str | None", "Timestamp ISO da resolução"),
            FieldSpec("descricao", "str", "Descrição do cliente"),
            FieldSpec("resolucao", "str | None", "Conclusão do banco"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
            RelationshipSpec("transaction", "Transação contestada", "transaction_id", "Transaction"),
        ),
    ),
    # ── PixContact (Contato Pix) ────────────────────────────────
    EntitySpec(
        class_name="PixContact",
        redis_key_template="itau_assist_pix_contact:{contact_id}",
        file_name="pix_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Identificador único do contato", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono do contato", index="tag"),
            FieldSpec("recipient_name", "str", "Nome do destinatário", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Chave Pix (cpf, email, celular ou aleatória)", index="text"),
            FieldSpec("chave_tipo", "str", "Tipo da chave: cpf, email, celular, aleatoria", index="tag"),
            FieldSpec("banco_destino", "str", "Banco do destinatário"),
            FieldSpec("frequencia_uso", "int", "Quantas vezes o cliente já enviou pra este contato", index="numeric"),
            FieldSpec("ultimo_uso", "str | None", "Timestamp do último Pix enviado"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── RewardsAccount (Programa de Pontos) ─────────────────────
    EntitySpec(
        class_name="RewardsAccount",
        redis_key_template="itau_assist_rewards:{rewards_id}",
        file_name="rewards_accounts.jsonl",
        id_field="rewards_id",
        fields=(
            FieldSpec("rewards_id", "str", "Identificador único da conta de pontos", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono", index="tag"),
            FieldSpec("programa", "str", "Programa: sempre_presente, atomos, latam_pass", index="tag"),
            FieldSpec("saldo_pontos", "int", "Saldo atual de pontos", index="numeric"),
            FieldSpec("pontos_a_vencer", "int", "Pontos que vencem nos próximos 90 dias", index="numeric"),
            FieldSpec("data_vencimento_proxima", "str | None", "Próxima data de vencimento de pontos (ISO)"),
            FieldSpec("categoria_top", "str | None", "Categoria de maior acúmulo (alimentacao, viagem, supermercado, etc)"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── SupportTicket (Atendimento anterior) ────────────────────
    EntitySpec(
        class_name="SupportTicket",
        redis_key_template="itau_assist_support_ticket:{ticket_id}",
        file_name="support_tickets.jsonl",
        id_field="ticket_id",
        fields=(
            FieldSpec("ticket_id", "str", "Identificador único do chamado", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("categoria", "str", "Categoria: contestacao, limite, cartao_bloqueado, pix, fatura, outros", index="tag"),
            FieldSpec("status", "str", "Status: aberto, em_andamento, resolvido", index="tag"),
            FieldSpec("data_abertura", "str", "Timestamp ISO de abertura"),
            FieldSpec("data_resolucao", "str | None", "Timestamp ISO de resolução"),
            FieldSpec("resumo", "str", "Resumo do chamado", index="text"),
            FieldSpec("resolucao", "str | None", "Como foi resolvido"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── FeatureStore (features online pro modelo de next-best-action da IARA) ─
    # Coração do flagship: features online no Redis lidas em tempo real (sub-ms) pelo
    # modelo de NBA. SEM index (lido via JSON.GET pela tool, não FT.SEARCH) pra não gerar
    # filter tools inúteis nem estourar o teto de 128 tools da API.
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="itau_assist_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Cliente (chave da feature row)", is_key_component=True),
            FieldSpec("renda_mensal", "float", "Feature: renda mensal estimada (BRL)"),
            FieldSpec("score_interno", "int", "Feature: score interno Itaú (0-1000)"),
            FieldSpec("aplicado_cdb", "float", "Feature: total aplicado em CDB tributado (BRL)"),
            FieldSpec("saldo_medio_3m", "float", "Feature: saldo médio dos últimos 3 meses (BRL)"),
            FieldSpec("tenure_meses", "int", "Feature: meses de relacionamento Personnalité"),
            FieldSpec("num_produtos", "int", "Feature: nº de produtos contratados"),
            FieldSpec("propensao_investimento", "float", "Feature: propensão a investir (0-1)"),
            FieldSpec("propensao_upgrade_cartao", "float", "Feature: propensão a upgrade de cartão premium (0-1)"),
            FieldSpec("propensao_cobranded_clube", "float", "Feature: afinidade com cartão co-branded do time do coração (0-1)"),
            FieldSpec("propensao_seguro", "float", "Feature: propensão a seguro/previdência (0-1)"),
            FieldSpec("time_do_coracao", "str", "Feature: clube de futebol (base do cartão co-branded via cartão branco)"),
            FieldSpec("perfil_digital", "str", "Feature: engajamento digital: alto, medio, baixo"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização (ISO)"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente dono das features", "customer_id", "Customer"),
        ),
    ),
    # ── Policy (Políticas do banco) ─────────────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="itau_assist_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: contestacao, limite, fatura, pix, pontos, seguranca, conta", index="tag"),
            FieldSpec("content", "str", "Texto completo da política", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Embedding vetorial do conteúdo",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
