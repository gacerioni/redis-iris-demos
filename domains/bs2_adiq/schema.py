"""BS2 Pay (ADA): data model definitions (single source of truth).

Merchant/acquiring concierge for BS2 Payments (formerly Adiq). Each EntitySpec
governs:
  * ContextModel generation
  * Redis Search index creation via Context Retriever
  * Synthetic data generation
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
    # -- Merchant (Estabelecimento credenciado) ------------------
    EntitySpec(
        class_name="Merchant",
        redis_key_template="bs2_adiq_merchant:{merchant_id}",
        file_name="merchants.jsonl",
        id_field="merchant_id",
        fields=(
            FieldSpec("merchant_id", "str", "Identificador único do estabelecimento", is_key_component=True),
            FieldSpec("razao_social", "str", "Razão social do estabelecimento", index="text", weight=2.0),
            FieldSpec("nome_fantasia", "str", "Nome fantasia do estabelecimento", index="text", weight=2.0),
            FieldSpec("cnpj_masked", "str", "CNPJ mascarado (ex: 12.***.***/0001-07)"),
            FieldSpec("segmento", "str", "Segmento: artigos_esportivos, alimentacao, autopecas", index="tag"),
            FieldSpec("plano_adiq", "str", "Plano de credenciamento: adiq_pro, adiq_flex", index="tag"),
            FieldSpec("cliente_desde", "str", "Início do credenciamento (YYYY-MM)"),
            FieldSpec("relacionamento_bs2", "str", "Relacionamento bancário: bs2_empresas, nenhum", index="tag"),
            FieldSpec("cidade", "str", "Cidade da sede", index="tag"),
            FieldSpec("status", "str", "Status: ativo, suspenso, descredenciado", index="tag"),
            FieldSpec("socio_responsavel", "str", "Sócio responsável pela conta", index="text", weight=1.5),
            FieldSpec("contato_email", "str", "Email de contato do sócio", index="text", weight=1.5, no_stem=True),
        ),
        relationships=(
            RelationshipSpec("pj_accounts", "Contas PJ do estabelecimento", "merchant_id", "list[PjAccount]"),
            RelationshipSpec("terminals", "Terminais POS do estabelecimento", "merchant_id", "list[Terminal]"),
            RelationshipSpec("features", "Features online do estabelecimento", "merchant_id", "FeatureStore"),
        ),
    ),
    # -- PjAccount (Conta PJ BS2) --------------------------------
    EntitySpec(
        class_name="PjAccount",
        redis_key_template="bs2_adiq_pj_account:{account_id}",
        file_name="pj_accounts.jsonl",
        id_field="account_id",
        fields=(
            FieldSpec("account_id", "str", "Identificador único da conta PJ", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento titular", index="tag"),
            FieldSpec("banco", "str", "Banco da conta de liquidação", index="tag"),
            FieldSpec("agencia", "str", "Número da agência"),
            FieldSpec("conta_masked", "str", "Número da conta mascarado"),
            FieldSpec("saldo_disponivel", "float", "Saldo disponível em BRL", index="numeric", sortable=True),
            FieldSpec("limite_capital_giro", "float", "Limite de capital de giro pré-aprovado (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: ativa, bloqueada", index="tag"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento titular", "merchant_id", "Merchant"),
        ),
    ),
    # -- SalesTransaction (Venda capturada) ----------------------
    EntitySpec(
        class_name="SalesTransaction",
        redis_key_template="bs2_adiq_sales_transaction:{transaction_id}",
        file_name="sales_transactions.jsonl",
        id_field="transaction_id",
        fields=(
            FieldSpec("transaction_id", "str", "Identificador único da venda", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento da venda", index="tag"),
            FieldSpec("data", "str", "Data da venda (ISO)", sortable=True),
            FieldSpec("valor_bruto", "float", "Valor bruto da venda (BRL)", index="numeric", sortable=True),
            FieldSpec("modalidade", "str", "Modalidade: credito_avista, credito_parcelado, debito, pix", index="tag"),
            FieldSpec("parcelas", "int", "Número de parcelas (1 se à vista)"),
            FieldSpec("bandeira", "str", "Bandeira: visa, mastercard, elo, pix", index="tag"),
            FieldSpec("canal", "str", "Canal de captura: ecommerce, pos", index="tag"),
            FieldSpec("terminal_id", "str | None", "Terminal POS da captura (null no e-commerce)", index="tag"),
            FieldSpec("status", "str", "Status: aprovada, em_disputa, estornada", index="tag"),
            FieldSpec("nsu", "str", "NSU (número sequencial único) da transação"),
            FieldSpec("cliente_final", "str", "Nome do comprador final", index="text", weight=1.5),
            FieldSpec("descricao", "str", "Descrição resumida do pedido", index="text"),
            FieldSpec("mdr_pct", "float", "MDR aplicado na venda (%)"),
            FieldSpec("valor_liquido", "float", "Valor líquido após MDR (BRL)", index="numeric"),
            FieldSpec("entrega", "str", "Entrega: confirmada:<rastreio>, extraviada:<rastreio> ou n/a (POS)"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento da venda", "merchant_id", "Merchant"),
            RelationshipSpec("terminal", "Terminal POS da captura", "terminal_id", "Terminal"),
        ),
    ),
    # -- Receivable (Agenda de recebíveis) -----------------------
    EntitySpec(
        class_name="Receivable",
        redis_key_template="bs2_adiq_receivable:{receivable_id}",
        file_name="receivables.jsonl",
        id_field="receivable_id",
        fields=(
            FieldSpec("receivable_id", "str", "Identificador único do recebível", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento dono da agenda", index="tag"),
            FieldSpec("data_prevista", "str", "Data prevista de liquidação (ISO)", sortable=True),
            FieldSpec("valor_bruto", "float", "Valor bruto do lote (BRL)", index="numeric"),
            FieldSpec("mdr_valor", "float", "MDR descontado do lote (BRL)"),
            FieldSpec("valor_liquido", "float", "Valor líquido a receber (BRL)", index="numeric", sortable=True),
            FieldSpec("bandeira", "str", "Bandeira predominante: visa, mastercard, elo, pix", index="tag"),
            FieldSpec("modalidade", "str", "Modalidade: credito_avista, credito_parcelado, debito, pix", index="tag"),
            FieldSpec("status", "str", "Status: pendente, liquidado, antecipado", index="tag"),
            FieldSpec("origem_transaction_id", "str", "Venda âncora (representativa) do lote de liquidação", index="tag"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento", "merchant_id", "Merchant"),
            RelationshipSpec("origem_transaction", "Venda âncora do lote", "origem_transaction_id", "SalesTransaction"),
        ),
    ),
    # -- Terminal (Maquininha POS) -------------------------------
    EntitySpec(
        class_name="Terminal",
        redis_key_template="bs2_adiq_terminal:{terminal_id}",
        file_name="terminals.jsonl",
        id_field="terminal_id",
        fields=(
            FieldSpec("terminal_id", "str", "Identificador único do terminal", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento dono do terminal", index="tag"),
            FieldSpec("serial", "str", "Número de série do equipamento"),
            FieldSpec("modelo", "str", "Modelo: pos_smart, pos_mini", index="tag"),
            FieldSpec("loja", "str", "Loja onde o terminal está instalado", index="tag"),
            FieldSpec("status", "str", "Status: ativo, instavel, inativo", index="tag"),
            FieldSpec("ultima_transacao_em", "str", "Timestamp ISO da última transação capturada"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento", "merchant_id", "Merchant"),
        ),
    ),
    # -- Dispute (Chargeback) ------------------------------------
    EntitySpec(
        class_name="Dispute",
        redis_key_template="bs2_adiq_dispute:{dispute_id}",
        file_name="disputes.jsonl",
        id_field="dispute_id",
        fields=(
            FieldSpec("dispute_id", "str", "Identificador único da disputa", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento notificado", index="tag"),
            FieldSpec("transaction_id", "str", "Venda contestada", index="tag"),
            FieldSpec("valor", "float", "Valor contestado (BRL)", index="numeric"),
            FieldSpec("motivo", "str", "Motivo: nao_reconhecida, produto_nao_recebido, duplicada, fraude", index="tag"),
            FieldSpec("cliente_final", "str", "Comprador que abriu a contestação", index="text", weight=1.5),
            FieldSpec("status", "str", "Status: aguardando_lojista, em_analise, ganha, perdida", index="tag"),
            FieldSpec("prazo_resposta", "str", "Data limite para envio de evidências (ISO)"),
            FieldSpec("bandeira", "str", "Bandeira da transação: visa, mastercard, elo", index="tag"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento", "merchant_id", "Merchant"),
            RelationshipSpec("transaction", "Venda contestada", "transaction_id", "SalesTransaction"),
        ),
    ),
    # -- SupportTicket (Atendimento anterior) --------------------
    EntitySpec(
        class_name="SupportTicket",
        redis_key_template="bs2_adiq_support_ticket:{ticket_id}",
        file_name="support_tickets.jsonl",
        id_field="ticket_id",
        fields=(
            FieldSpec("ticket_id", "str", "Identificador único do chamado", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento", index="tag"),
            FieldSpec("categoria", "str", "Categoria: terminal, suprimentos, repasse, chargeback, outros", index="tag"),
            FieldSpec("status", "str", "Status: aberto, em_andamento, resolvido", index="tag"),
            FieldSpec("data_abertura", "str", "Timestamp ISO de abertura"),
            FieldSpec("data_resolucao", "str | None", "Timestamp ISO de resolução"),
            FieldSpec("resumo", "str", "Resumo do chamado", index="text"),
            FieldSpec("resolucao", "str | None", "Como foi resolvido"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento", "merchant_id", "Merchant"),
        ),
    ),
    # -- PixContact (Contato Pix da conta PJ) --------------------
    EntitySpec(
        class_name="PixContact",
        redis_key_template="bs2_adiq_pix_contact:{contact_id}",
        file_name="pix_contacts.jsonl",
        id_field="contact_id",
        fields=(
            FieldSpec("contact_id", "str", "Identificador único do contato", is_key_component=True),
            FieldSpec("merchant_id", "str", "Estabelecimento dono do contato", index="tag"),
            FieldSpec("recipient_name", "str", "Nome do destinatário", index="text", weight=2.0),
            FieldSpec("chave_pix", "str", "Chave Pix (cnpj, email, celular ou aleatória)", index="text"),
            FieldSpec("chave_tipo", "str", "Tipo da chave: cnpj, email, celular, aleatoria", index="tag"),
            FieldSpec("banco_destino", "str", "Banco do destinatário"),
            FieldSpec("tipo_relacao", "str", "Relação: fornecedor, pro_labore, frete, outros", index="tag"),
            FieldSpec("valor_recorrente", "float | None", "Valor típico do pagamento recorrente (BRL)"),
            FieldSpec("recorrencia", "str | None", "Padrão de recorrência (ex: mensal, todo dia 15)"),
            FieldSpec("frequencia_uso", "int", "Quantas vezes o lojista já pagou este contato", index="numeric"),
            FieldSpec("ultimo_uso", "str | None", "Timestamp do último Pix enviado"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento", "merchant_id", "Merchant"),
        ),
    ),
    # -- FeatureStore (online features for ADA's merchant recommendations) ---
    # Core of the flagship: online features in Redis read in real time (sub-ms) by
    # the recommendation model (anticipation offers, working capital, expansion).
    # NO index (read via JSON.GET by the tool, not FT.SEARCH) to avoid useless
    # filter tools and to stay under the 128-tool API ceiling.
    EntitySpec(
        class_name="FeatureStore",
        redis_key_template="bs2_adiq_features:{merchant_id}",
        file_name="feature_store.jsonl",
        id_field="merchant_id",
        fields=(
            FieldSpec("merchant_id", "str", "Estabelecimento (chave da feature row)", is_key_component=True),
            FieldSpec("agenda_liquida_30d", "float", "Feature: agenda líquida a receber nos próximos 30 dias (BRL)"),
            FieldSpec("agenda_liquida_31_60d", "float", "Feature: agenda líquida a receber entre 31 e 60 dias (BRL)"),
            FieldSpec("vendas_mes", "float", "Feature: vendas brutas do ciclo atual (BRL)"),
            FieldSpec("qtd_transacoes_mes", "int", "Feature: nº de transações do ciclo atual"),
            FieldSpec("ticket_medio", "float", "Feature: ticket médio do ciclo atual (BRL)"),
            FieldSpec("mdr_medio_pct", "float", "Feature: MDR médio ponderado do ciclo (%)"),
            FieldSpec("chargeback_rate_pct", "float", "Feature: taxa de chargeback (%)"),
            FieldSpec("crescimento_mm_pct", "float", "Feature: crescimento mês a mês das vendas (%)"),
            FieldSpec("plano", "str", "Feature: plano de credenciamento vigente"),
            FieldSpec("taxa_antecipacao_am", "float", "Feature: taxa de antecipação vigente (% a.m., pro-rata)"),
            FieldSpec("sazonalidade_pico", "str", "Feature: pico sazonal de vendas do estabelecimento"),
            FieldSpec("saldo_pj", "float", "Feature: saldo disponível na conta PJ BS2 (BRL)"),
            FieldSpec("capital_giro_pre_aprovado", "float", "Feature: limite de capital de giro pré-aprovado (BRL)"),
            FieldSpec("filial_planejada", "str", "Feature: cidade da próxima filial planejada pelo lojista"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização (ISO)"),
        ),
        relationships=(
            RelationshipSpec("merchant", "Estabelecimento dono das features", "merchant_id", "Merchant"),
        ),
    ),
    # -- Policy (Políticas BS2 Pay) ------------------------------
    EntitySpec(
        class_name="Policy",
        redis_key_template="bs2_adiq_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: taxas, repasse, chargeback, antecipacao, terminal, credenciamento, pix, credito, conta", index="tag"),
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
