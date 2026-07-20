"""Leet Bank data model definitions (single source of truth).

Each EntitySpec governs:
  - ContextModel generation
  - Redis Search index creation via Context Retriever
  - Synthetic data generation

Leet Bank is a fictional Brazilian digital bank with a hacker/dev aesthetic,
built for the Febraban Tech 2026 demo ("Agentes Inteligentes, lideranca
humana"). Assistant name: MarIAm. Redis prefix: leet_bank.
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
        redis_key_template="leet_bank_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Identificador único do cliente", is_key_component=True),
            FieldSpec("name", "str", "Nome completo do cliente", index="text", weight=2.0),
            FieldSpec("cpf_masked", "str", "CPF mascarado (ex: ***.456.789-**)"),
            FieldSpec("email", "str", "Email do cliente", index="text", weight=1.5, no_stem=True),
            FieldSpec("phone_masked", "str | None", "Celular mascarado (ex: +55 11 9****-1337)"),
            FieldSpec("account_status", "str", "Status: active, blocked, in_review", index="tag"),
            FieldSpec("segmento", "str", "Segmento: elite_1337, dev_pro, starter", index="tag"),
            FieldSpec("cliente_desde", "str", "Início do relacionamento (YYYY-MM)"),
            FieldSpec("city", "str", "Cidade do cliente", index="tag"),
            FieldSpec("profissao", "str | None", "Profissão declarada"),
            FieldSpec("default_address", "str | None", "Endereço residencial"),
        ),
        relationships=(
            RelationshipSpec("accounts", "Contas do cliente", "customer_id", "list[Account]"),
            RelationshipSpec("cards", "Cartões do cliente", "customer_id", "list[Card]"),
        ),
    ),
    # ── Account (Conta Corrente + CDB) ──────────────────────────
    EntitySpec(
        class_name="Account",
        redis_key_template="leet_bank_account:{account_id}",
        file_name="accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Identificador único da conta", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente titular", index="tag"),
            FieldSpec("agencia", "str", "Número da agência"),
            FieldSpec("conta_masked", "str", "Número da conta mascarado (ex: ***1337)"),
            FieldSpec("tipo", "str", "Tipo: corrente", index="tag"),
            FieldSpec("saldo_disponivel", "float", "Saldo disponível em BRL", index="numeric", sortable=True),
            FieldSpec("saldo_cdb", "float", "Total aplicado em CDB com liquidez diária (BRL)", index="numeric"),
            FieldSpec("cdb_rendimento_cdi_pct", "float", "Rendimento do CDB em % do CDI (ex: 103.37)"),
            FieldSpec("cdb_liquidez", "str | None", "Liquidez do CDB: diaria"),
            FieldSpec("cheque_especial_limite", "float", "Limite do cheque especial (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: active, blocked", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente titular", "customer_id", "Customer"),
        ),
    ),
    # ── Card (Cartão de Crédito) ────────────────────────────────
    EntitySpec(
        class_name="Card",
        redis_key_template="leet_bank_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Identificador único do cartão", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente titular", index="tag"),
            FieldSpec("account_id", "str", "Conta vinculada", index="tag"),
            FieldSpec("bandeira", "str", "Bandeira: mastercard, visa", index="tag"),
            FieldSpec("produto", "str", "Produto: leet_black, leet_virtual", index="tag"),
            FieldSpec("numero_mascarado", "str", "Final mascarado (ex: ****1337)"),
            FieldSpec("limite_total", "float", "Limite total aprovado (BRL)", index="numeric"),
            FieldSpec("limite_usado", "float", "Limite atualmente utilizado (BRL)", index="numeric"),
            FieldSpec("limite_disponivel", "float", "Limite disponível para uso (BRL)", index="numeric"),
            FieldSpec("fatura_aberta", "float", "Valor da fatura aberta do ciclo atual (BRL)", index="numeric"),
            FieldSpec("fatura_vencimento", "str | None", "Vencimento da fatura aberta (YYYY-MM-DD)"),
            FieldSpec("utilizacao_pct", "float", "Percentual de utilização do limite", index="numeric"),
            FieldSpec("validade", "str", "Validade no formato MM/AA"),
            FieldSpec("status", "str", "Status: active, blocked, replaced", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente titular", "customer_id", "Customer"),
            RelationshipSpec("account", "Conta vinculada", "account_id", "Account"),
        ),
    ),
    # ── BillingCycle (Fatura) ───────────────────────────────────
    EntitySpec(
        class_name="BillingCycle",
        redis_key_template="leet_bank_billing_cycle:{cycle_id}",
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
    # ── Transaction (Lançamento na fatura, Pix, boleto, salário) ─
    EntitySpec(
        class_name="Transaction",
        redis_key_template="leet_bank_transaction:{transaction_id}",
        file_name="transactions.jsonl",
        id_field="transaction_id",
        fields=(
            FieldSpec("transaction_id", "str", "Identificador único da transação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente associado", index="tag"),
            FieldSpec("card_id", "str | None", "Cartão usado (se for compra com cartão)", index="tag"),
            FieldSpec("account_id", "str | None", "Conta envolvida (Pix, boleto, débito, salário)", index="tag"),
            FieldSpec("billing_cycle_id", "str | None", "Fatura à qual pertence", index="tag"),
            FieldSpec("tipo", "str", "Tipo: compra_credito, pix_envio, pix_recebido, debito, boleto, salario, estorno", index="tag"),
            FieldSpec("merchant", "str", "Estabelecimento ou contraparte", index="text", weight=1.5),
            FieldSpec("mcc", "str | None", "Merchant Category Code", index="tag"),
            FieldSpec("valor", "float", "Valor (positivo = saída, negativo = entrada)", index="numeric"),
            FieldSpec("parcelas_total", "int", "Total de parcelas (1 se à vista)"),
            FieldSpec("parcela_atual", "int", "Parcela atual"),
            FieldSpec("status", "str", "Status: aprovada, contestada, estornada, pendente", index="tag"),
            FieldSpec("data_compra", "str", "Timestamp ISO da compra", sortable=True),
            FieldSpec("data_lancamento", "str", "Timestamp ISO do lançamento na fatura", sortable=True),
            FieldSpec("is_recurring", "str", "Flag de recorrência: sim, nao", index="tag"),
            FieldSpec("recurring_label", "str | None", "Rótulo legível se recorrente (ex: Assinatura CLOUD DEV PRO)"),
            FieldSpec("location_city", "str | None", "Cidade da compra"),
            FieldSpec("dispute_id", "str | None", "Se contestada, ID da contestação", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
            RelationshipSpec("card", "Cartão", "card_id", "Card"),
            RelationshipSpec("account", "Conta", "account_id", "Account"),
        ),
    ),
    # ── PixContact (Contato Pix) ────────────────────────────────
    EntitySpec(
        class_name="PixContact",
        redis_key_template="leet_bank_pix_contact:{contact_id}",
        file_name="pix_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Identificador único do contato", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono do contato", index="tag"),
            FieldSpec("recipient_name", "str", "Nome do destinatário", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Chave Pix (cpf, cnpj, email, celular ou aleatória)", index="text"),
            FieldSpec("chave_tipo", "str", "Tipo da chave: cpf, cnpj, email, celular, aleatoria", index="tag"),
            FieldSpec("banco_destino", "str", "Banco do destinatário"),
            FieldSpec("contato_desde", "str | None", "Desde quando é contato salvo (YYYY-MM)"),
            FieldSpec("frequencia_uso", "int", "Quantas vezes o cliente já enviou pra este contato", index="numeric"),
            FieldSpec("ultimo_uso", "str | None", "Timestamp do último Pix enviado"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── PixAutomatico (Recorrência Pix autorizada) ──────────────
    EntitySpec(
        class_name="PixAutomatico",
        redis_key_template="leet_bank_pix_automatico:{autorizacao_id}",
        file_name="pix_automatico.jsonl",
        id_field="autorizacao_id",
        fields=(
            FieldSpec("autorizacao_id", "str", "Identificador único da autorização", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente pagador", index="tag"),
            FieldSpec("payee_name", "str", "Nome do recebedor", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Chave Pix do recebedor"),
            FieldSpec("chave_tipo", "str", "Tipo da chave: cpf, cnpj, email, celular, aleatoria", index="tag"),
            FieldSpec("valor", "float", "Valor de cada cobrança (BRL)", index="numeric"),
            FieldSpec("dia_cobranca", "int", "Dia do mês da cobrança", index="numeric"),
            FieldSpec("periodicidade", "str", "Periodicidade: mensal, semanal, anual", index="tag"),
            FieldSpec("status", "str", "Status: ativo, pausado, cancelado", index="tag"),
            FieldSpec("data_criacao", "str", "Timestamp ISO da autorização"),
            FieldSpec("ultima_cobranca", "str | None", "Timestamp ISO da última cobrança executada"),
            FieldSpec("descricao", "str", "Descrição legível da recorrência"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente pagador", "customer_id", "Customer"),
        ),
    ),
    # ── Dispute (Contestação) ───────────────────────────────────
    EntitySpec(
        class_name="Dispute",
        redis_key_template="leet_bank_dispute:{dispute_id}",
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
    # ── RewardsAccount (Programa de pontos XP) ──────────────────
    EntitySpec(
        class_name="RewardsAccount",
        redis_key_template="leet_bank_rewards:{rewards_id}",
        file_name="rewards_accounts.jsonl",
        id_field="rewards_id",
        fields=(
            FieldSpec("rewards_id", "str", "Identificador único da conta de pontos", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono", index="tag"),
            FieldSpec("programa", "str", "Programa: leet_xp", index="tag"),
            FieldSpec("saldo_xp", "int", "Saldo atual de XP", index="numeric"),
            FieldSpec("nivel", "str", "Nível do programa: Iniciante, Hacker, Elite 1337", index="tag"),
            FieldSpec("xp_expirando", "int", "XP que expira na próxima janela", index="numeric"),
            FieldSpec("expira_em", "str | None", "Data de expiração do próximo lote de XP (YYYY-MM-DD)"),
            FieldSpec("multiplicador_tech", "int", "Multiplicador de XP em tech/eletrônicos (ex: 2 = 2x)"),
            FieldSpec("categoria_top", "str | None", "Categoria de maior acúmulo (tech_eletronicos, alimentacao, etc)"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── SupportTicket (Atendimento anterior) ────────────────────
    EntitySpec(
        class_name="SupportTicket",
        redis_key_template="leet_bank_support_ticket:{ticket_id}",
        file_name="support_tickets.jsonl",
        id_field="ticket_id",
        fields=(
            FieldSpec("ticket_id", "str", "Identificador único do chamado", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("categoria", "str", "Categoria: cartao, pix, contestacao, fatura, investimentos, outros", index="tag"),
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
    # ── FeatureStoreRecord (online features for MarIAm) ─────────
    # Heart of the flagship: online features in Redis read in real time (sub-ms)
    # by the next-best-action and anti-scam flows. NOT indexed (read via JSON.GET
    # by the tool, not FT.SEARCH) to avoid useless filter tools and to stay under
    # the 128-tool API ceiling.
    EntitySpec(
        class_name="FeatureStoreRecord",
        redis_key_template="leet_bank_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Cliente (chave da feature row)", is_key_component=True),
            FieldSpec("saldo", "float", "Feature: saldo disponível em conta (BRL)"),
            FieldSpec("cdb_total", "float", "Feature: total aplicado em CDB (BRL)"),
            FieldSpec("cdb_livre", "float", "Feature: CDB livre de garantias, disponível como colateral (BRL)"),
            FieldSpec("credito_flash_pre_aprovado", "float", "Feature: Crédito Flash pré-aprovado (BRL)"),
            FieldSpec("taxa_flash_am", "float", "Feature: taxa do Crédito Flash em % ao mês"),
            FieldSpec("pix_ticket_medio", "float", "Feature: ticket médio dos Pix enviados (BRL)"),
            FieldSpec("maior_pix_90d", "float", "Feature: maior Pix enviado nos últimos 90 dias (BRL)"),
            FieldSpec("contatos_confiaveis", "int", "Feature: nº de contatos Pix confiáveis salvos"),
            FieldSpec("golpe_score", "float", "Feature: score de risco de golpe do cliente (0-1)"),
            FieldSpec("utilizacao_cartao_pct", "int", "Feature: utilização do limite do cartão (%)"),
            FieldSpec("xp_saldo", "int", "Feature: saldo de XP no programa de pontos"),
            FieldSpec("xp_expirando", "int", "Feature: XP expirando na próxima janela"),
            FieldSpec("nivel", "str", "Feature: nível no programa XP (ex: elite_1337)"),
            FieldSpec("propensao_credito", "float", "Feature: propensão a contratar crédito (0-1)"),
            FieldSpec("torce_para", "str", "Feature: time do coração (base pra ofertas de experiências)"),
            FieldSpec("evento_proximo", "str", "Feature: próximo evento de interesse do cliente"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização (ISO)"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente dono das features", "customer_id", "Customer"),
        ),
    ),
    # ── Policy (Políticas do banco) ─────────────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="leet_bank_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: seguranca, pix, credito, pontos, contestacao, fatura, cartao, open_finance, experiencias", index="tag"),
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
