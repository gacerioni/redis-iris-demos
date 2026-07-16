"""Bradesco BIA — definições de modelo de dados (single source of truth).

Banco premium (segmento Prime) com o diferencial de feature store: a entidade
FeatureStore guarda features online no Redis que o modelo de next-best-offer lê
em tempo real. Cada EntitySpec governa:
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
    # ── Customer (cliente Bradesco Prime) ───────────────────────
    EntitySpec(
        class_name="Customer",
        redis_key_template="bradesco_bia_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Identificador único do cliente", is_key_component=True),
            FieldSpec("nome", "str", "Nome completo", index="text", weight=2.0),
            FieldSpec("cpf_masked", "str", "CPF mascarado"),
            FieldSpec("email", "str", "Email cadastrado", index="text", weight=1.5, no_stem=True),
            FieldSpec("cidade", "str", "Cidade", index="tag"),
            FieldSpec("segmento", "str", "Segmento: varejo, exclusive, prime, private", index="tag"),
            FieldSpec("agencia", "str", "Número da agência"),
            FieldSpec("conta", "str", "Número da conta mascarado"),
            FieldSpec("cliente_desde_anos", "int", "Anos de relacionamento", index="numeric", sortable=True),
            FieldSpec("renda_mensal", "float", "Renda mensal declarada (BRL)", index="numeric", sortable=True),
            FieldSpec("score_interno", "int", "Score interno Bradesco (0-1000)", index="numeric", sortable=True),
            FieldSpec("perfil_investidor", "str", "Perfil: conservador, moderado, arrojado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("accounts", "Contas do cliente", "customer_id", "list[Account]"),
            RelationshipSpec("cards", "Cartões do cliente", "customer_id", "list[Card]"),
            RelationshipSpec("features", "Features online do cliente", "customer_id", "FeatureStore"),
        ),
    ),
    # ── Account (conta) ─────────────────────────────────────────
    EntitySpec(
        class_name="Account",
        redis_key_template="bradesco_bia_account:{account_id}",
        file_name="accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Identificador único da conta", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono da conta", index="tag"),
            FieldSpec("tipo", "str", "Tipo: corrente, poupanca, investimento", index="tag"),
            FieldSpec("saldo", "float", "Saldo atual (BRL)", index="numeric", sortable=True),
            FieldSpec("limite_cheque_especial", "float", "Limite do cheque especial (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: ativa, bloqueada", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── Card (cartão) ───────────────────────────────────────────
    EntitySpec(
        class_name="Card",
        redis_key_template="bradesco_bia_card:{card_id}",
        file_name="cards.jsonl",
        id_field="card_id",
        fields=(
            FieldSpec("card_id", "str", "Identificador único do cartão", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono do cartão", index="tag"),
            FieldSpec("produto", "str", "Produto: Elo Nanquim, Visa Infinite, Mastercard Black, etc.", index="text"),
            FieldSpec("tipo", "str", "Tipo: credito, debito", index="tag"),
            FieldSpec("bandeira", "str", "Bandeira: visa, mastercard, elo", index="tag"),
            FieldSpec("final", "str", "4 últimos dígitos"),
            FieldSpec("limite", "float", "Limite de crédito (BRL)", index="numeric", sortable=True),
            FieldSpec("fatura_atual", "float", "Fatura atual em aberto (BRL)", index="numeric", sortable=True),
            FieldSpec("vencimento", "str", "Data de vencimento da fatura (ISO)", sortable=True),
            FieldSpec("anuidade", "float", "Anuidade anual (BRL, 0 se isenta)", index="numeric"),
            FieldSpec("status", "str", "Status: ativo, bloqueado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── Transaction ─────────────────────────────────────────────
    EntitySpec(
        class_name="Transaction",
        redis_key_template="bradesco_bia_transaction:{txn_id}",
        file_name="transactions.jsonl",
        id_field="txn_id",
        fields=(
            FieldSpec("txn_id", "str", "Identificador único da transação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("card_id", "str | None", "Cartão usado (se compra)", index="tag"),
            FieldSpec("account_id", "str | None", "Conta (se débito/Pix)", index="tag"),
            FieldSpec("tipo", "str", "Tipo: compra_credito, compra_debito, pix_enviado, pix_recebido, cashback", index="tag"),
            FieldSpec("merchant", "str", "Estabelecimento/contraparte", index="text", weight=1.5),
            FieldSpec("mcc", "str", "Categoria (MCC)", index="tag"),
            FieldSpec("valor", "float", "Valor total da transação (BRL)", index="numeric", sortable=True),
            FieldSpec("data", "str", "Timestamp ISO", sortable=True),
            FieldSpec("is_recurring", "str", "Recorrente: sim, nao", index="tag"),
            FieldSpec("parcela_atual", "int", "Parcela atual (1 se à vista)", index="numeric"),
            FieldSpec("parcela_total", "int", "Total de parcelas (1 se à vista)", index="numeric", sortable=True),
            FieldSpec("valor_parcela", "float", "Valor de cada parcela (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: aprovada, pendente, contestada", index="tag"),
        ),
        relationships=(
            RelationshipSpec("owner", "Cliente", "customer_id", "Customer"),
        ),
    ),
    # ── BillingCycle (fatura) ───────────────────────────────────
    EntitySpec(
        class_name="BillingCycle",
        redis_key_template="bradesco_bia_billing_cycle:{cycle_id}",
        file_name="billing_cycles.jsonl",
        id_field="cycle_id",
        fields=(
            FieldSpec("cycle_id", "str", "Identificador único da fatura", is_key_component=True),
            FieldSpec("card_id", "str", "Cartão", index="tag"),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("mes_referencia", "str", "Mês de referência (YYYY-MM)", index="tag", sortable=True),
            FieldSpec("valor_total", "float", "Valor total da fatura (BRL)", index="numeric", sortable=True),
            FieldSpec("valor_minimo", "float", "Pagamento mínimo (BRL)", index="numeric"),
            FieldSpec("vencimento", "str", "Vencimento da fatura (ISO)", sortable=True),
            FieldSpec("status", "str", "Status: aberta, fechada, paga, atrasada", index="tag"),
        ),
    ),
    # ── Investment (aplicações) ─────────────────────────────────
    EntitySpec(
        class_name="Investment",
        redis_key_template="bradesco_bia_investment:{investment_id}",
        file_name="investments.jsonl",
        id_field="investment_id",
        fields=(
            FieldSpec("investment_id", "str", "Identificador único da aplicação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("produto", "str", "Produto: CDB, LCI, LCA, Tesouro, Fundo, Previdência", index="tag"),
            FieldSpec("descricao", "str", "Descrição da aplicação", index="text"),
            FieldSpec("valor_aplicado", "float", "Valor aplicado (BRL)", index="numeric", sortable=True),
            FieldSpec("rentabilidade_cdi_pct", "int", "Rentabilidade (% do CDI)", index="numeric"),
            FieldSpec("vencimento", "str", "Vencimento (ISO)", sortable=True),
            FieldSpec("liquidez", "str", "Liquidez: diaria, no_vencimento, D_mais_30", index="tag"),
        ),
    ),
    # ── PixContact ──────────────────────────────────────────────
    EntitySpec(
        class_name="PixContact",
        redis_key_template="bradesco_bia_pix_contact:{contact_id}",
        file_name="pix_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Identificador único do contato", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente dono da agenda", index="tag"),
            FieldSpec("nome", "str", "Nome do contato", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Chave Pix mascarada"),
            FieldSpec("tipo_chave", "str", "Tipo: cpf, email, celular, aleatoria", index="tag"),
            FieldSpec("banco", "str", "Banco do contato", index="text"),
            FieldSpec("is_frequente", "str", "Contato frequente: sim, nao", index="tag"),
        ),
    ),
    # ── Dispute (contestação) ───────────────────────────────────
    EntitySpec(
        class_name="Dispute",
        redis_key_template="bradesco_bia_dispute:{dispute_id}",
        file_name="disputes.jsonl",
        id_field="dispute_id",
        fields=(
            FieldSpec("dispute_id", "str", "Identificador único da contestação", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente", index="tag"),
            FieldSpec("transaction_id", "str | None", "Transação contestada", index="tag"),
            FieldSpec("motivo", "str", "Motivo", index="text"),
            FieldSpec("valor", "float", "Valor contestado (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: aberta, em_analise, procedente, improcedente", index="tag"),
            FieldSpec("data", "str", "Timestamp ISO", sortable=True),
        ),
    ),
    # ── FeatureStore (features online pro modelo de recomendação) ─
    # Esta entidade é o coração do diferencial: features online no Redis que o
    # modelo de next-best-offer lê em tempo real (sub-ms).
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="bradesco_bia_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Cliente (chave da feature row)", is_key_component=True),
            FieldSpec("renda_mensal", "float", "Feature: renda mensal (BRL)", index="numeric", sortable=True),
            FieldSpec("score_interno", "int", "Feature: score interno (0-1000)", index="numeric", sortable=True),
            FieldSpec("utilizacao_cartao_pct", "int", "Feature: % de utilização do limite do cartão", index="numeric"),
            FieldSpec("tenure_meses", "int", "Feature: meses de relacionamento", index="numeric"),
            FieldSpec("velocity_gasto_30d", "float", "Feature: gasto nos últimos 30 dias (BRL)", index="numeric", sortable=True),
            FieldSpec("saldo_medio_3m", "float", "Feature: saldo médio dos últimos 3 meses (BRL)", index="numeric"),
            FieldSpec("num_produtos", "int", "Feature: nº de produtos contratados", index="numeric"),
            FieldSpec("propensao_investimento", "float", "Feature: propensão a investir (0-1)", index="numeric", sortable=True),
            FieldSpec("propensao_credito", "float", "Feature: propensão a crédito (0-1)", index="numeric"),
            FieldSpec("propensao_seguro", "float", "Feature: propensão a seguro/previdência (0-1)", index="numeric"),
            FieldSpec("perfil_digital", "str", "Feature: engajamento digital: alto, medio, baixo", index="tag"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização das features (ISO)", sortable=True),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente dono das features", "customer_id", "Customer"),
        ),
    ),
    # ── Policy (políticas / ajuda Bradesco) ─────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="bradesco_bia_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: pix, contestacao, cartao, investimento, seguranca, prime, limites, lgpd", index="tag"),
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
