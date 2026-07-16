"""aiqfome (AIQ): data model definitions (single source of truth).

Delivery concierge for aiqfome (Magalu's white-label food delivery, HQ in
Maringa-PR; customers are called "fominhas"). Each EntitySpec governs:
  * ContextModel generation
  * Redis Search index creation via Context Retriever
  * Synthetic data generation

The Dish catalog doubles as the strategic asset for a future retail search
demo (autocomplete, full-text search, synonyms, vector search, reranking),
so dishes carry rich PT-BR descriptions, popularity for reranking and a
content embedding for the vector index.
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
    # -- Customer (Fominha) ---------------------------------------
    EntitySpec(
        class_name="Customer",
        redis_key_template="aiqfome_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Identificador único do fominha", is_key_component=True),
            FieldSpec("nome", "str", "Nome completo do fominha", index="text", weight=2.0),
            FieldSpec("email", "str", "Email do fominha", index="text", weight=1.5, no_stem=True),
            FieldSpec("cidade", "str", "Cidade do fominha", index="tag"),
            FieldSpec("bairro", "str", "Bairro do endereço principal", index="tag"),
            FieldSpec("fominha_desde", "str", "Cliente aiqfome desde (YYYY-MM)"),
            FieldSpec("clube_aiqfome", "str", "Assinante do clube aiqfome (frete grátis em parceiros): sim, nao", index="tag"),
            FieldSpec("endereco_entrega", "str", "Endereço de entrega padrão"),
            FieldSpec("telefone", "str", "Celular mascarado (ex: +55 44 9****-4321)"),
        ),
        relationships=(
            RelationshipSpec("orders", "Pedidos do fominha", "customer_id", "list[Order]"),
            RelationshipSpec("vouchers", "Vouchers do fominha", "customer_id", "list[Voucher]"),
            RelationshipSpec("features", "Features online do fominha", "customer_id", "FeatureStoreRecord"),
        ),
    ),
    # -- Merchant (Restaurante parceiro) --------------------------
    EntitySpec(
        class_name="Merchant",
        redis_key_template="aiqfome_merchant:{merchant_id}",
        file_name="merchants.jsonl",
        id_field="merchant_id",
        fields=(
            FieldSpec("merchant_id", "str", "Identificador único do restaurante", is_key_component=True),
            FieldSpec("nome", "str", "Nome do restaurante", index="text", weight=2.0),
            FieldSpec("cozinha", "str", "Tipo de cozinha: japonesa, pizza, lanches, acai_sobremesas, caseira, pastelaria, massas, churrasco, vegetariana, mexicana, padaria_cafe", index="tag"),
            FieldSpec("rating", "float", "Nota média do restaurante (1-5)", index="numeric", sortable=True),
            FieldSpec("delivery_fee", "float", "Taxa de entrega (BRL, 0 nos parceiros do clube)", index="numeric"),
            FieldSpec("eta_min", "int", "Tempo estimado de entrega em minutos", index="numeric", sortable=True),
            FieldSpec("cidade", "str", "Cidade do restaurante", index="tag"),
            FieldSpec("bairro", "str", "Bairro do restaurante", index="tag"),
            FieldSpec("aberto", "str", "Aberto agora: sim, nao", index="tag"),
            FieldSpec("clube_parceiro", "str", "Parceiro do clube aiqfome (frete grátis pra assinantes): sim, nao", index="tag"),
            FieldSpec("lat", "float", "Latitude do restaurante", index="numeric"),
            FieldSpec("lon", "float", "Longitude do restaurante", index="numeric"),
            FieldSpec("geo", "str", "Coordenada no formato 'lon,lat', pronta pra um índice GEO futuro"),
            FieldSpec("descricao", "str", "Descrição curta do restaurante", index="text"),
        ),
        relationships=(
            RelationshipSpec("dishes", "Pratos do cardápio do restaurante", "merchant_id", "list[Dish]"),
            RelationshipSpec("orders", "Pedidos do restaurante", "merchant_id", "list[Order]"),
        ),
    ),
    # -- Dish (Item do cardápio) -----------------------------------
    # Strategic asset: this catalog also powers the future retail search demo
    # (autocomplete, FTS, synonyms, vector search, RRF reranking), hence the
    # rich descriptions, popularity score and content embedding.
    EntitySpec(
        class_name="Dish",
        redis_key_template="aiqfome_dish:{dish_id}",
        file_name="dishes.jsonl",
        id_field="dish_id",
        fields=(
            FieldSpec("dish_id", "str", "Identificador único do prato", is_key_component=True),
            FieldSpec("merchant_id", "str", "Restaurante dono do prato", index="tag"),
            FieldSpec("nome", "str", "Nome do prato", index="text", weight=2.0),
            FieldSpec("descricao", "str", "Descrição rica do prato em PT-BR", index="text"),
            FieldSpec("categoria", "str", "Categoria: temaki, sushi, combo, entrada, pizza, burger, porcao, acai, marmita, pastel, massa, risoto, espeto, churrasco, vegano, salada, taco, burrito, lanche, doce, bebida", index="tag"),
            FieldSpec("preco", "float", "Preço do prato (BRL)", index="numeric", sortable=True),
            FieldSpec("rating", "float", "Nota média do prato (1-5)", index="numeric"),
            FieldSpec("popularity", "int", "Popularidade 1-100 (usada pra reranking)", index="numeric", sortable=True),
            FieldSpec("tags", "list[str]", "Tags do prato: mais_pedido, promo, picante, vegetariano, vegano, sem_gluten", index="tag"),
            FieldSpec("alergenos", "list[str]", "Alérgenos presentes: camarao, gluten, lactose, amendoim, ovo (lista vazia se nenhum)", index="tag"),
            FieldSpec("serve_pessoas", "int", "Quantas pessoas o prato serve", index="numeric"),
            FieldSpec(
                "content_embedding", "list[float]", "Embedding vetorial de nome + descrição",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
        relationships=(
            RelationshipSpec("merchant", "Restaurante dono do prato", "merchant_id", "Merchant"),
        ),
    ),
    # -- Order (Pedido) --------------------------------------------
    EntitySpec(
        class_name="Order",
        redis_key_template="aiqfome_order:{order_id}",
        file_name="orders.jsonl",
        id_field="order_id",
        fields=(
            FieldSpec("order_id", "str", "Identificador do pedido (ex: AIQ-8842)", is_key_component=True),
            FieldSpec("customer_id", "str", "Fominha que fez o pedido", index="tag"),
            FieldSpec("merchant_id", "str", "Restaurante do pedido", index="tag"),
            FieldSpec("itens", "list[dict]", "Itens do pedido (dish_id, nome, qty, preco)"),
            FieldSpec("total", "float", "Total do pedido (BRL), soma dos itens", index="numeric", sortable=True),
            FieldSpec("status", "str", "Status: entregue, saiu_para_entrega, em_preparo, recebido, cancelado", index="tag"),
            FieldSpec("courier_id", "str | None", "Entregador designado", index="tag"),
            FieldSpec("criado_em", "str", "Timestamp ISO de criação do pedido", sortable=True),
            FieldSpec("entregue_em", "str | None", "Timestamp ISO da entrega (null se não entregue)"),
            FieldSpec("pagamento", "str", "Forma de pagamento: pix, credito, dinheiro", index="tag"),
            FieldSpec("observacao", "str | None", "Observações do pedido (nota do cliente ou ocorrência registrada)", index="text"),
        ),
        relationships=(
            RelationshipSpec("customer", "Fominha que fez o pedido", "customer_id", "Customer"),
            RelationshipSpec("merchant", "Restaurante do pedido", "merchant_id", "Merchant"),
            RelationshipSpec("courier", "Entregador do pedido", "courier_id", "Courier"),
        ),
    ),
    # -- Courier (Entregador) --------------------------------------
    EntitySpec(
        class_name="Courier",
        redis_key_template="aiqfome_courier:{courier_id}",
        file_name="couriers.jsonl",
        id_field="courier_id",
        fields=(
            FieldSpec("courier_id", "str", "Identificador único do entregador", is_key_component=True),
            FieldSpec("nome", "str", "Nome do entregador", index="text", weight=2.0),
            FieldSpec("veiculo", "str", "Veículo: moto, bike", index="tag"),
            FieldSpec("status", "str", "Status: em_rota, disponivel", index="tag"),
            FieldSpec("posicao_atual", "str", "Posição atual em texto (ex: a 1,2 km, subindo a Av. Colombo)"),
            FieldSpec("avaliacao", "float", "Nota média do entregador (1-5)", index="numeric"),
        ),
    ),
    # -- RefundRequest (Reembolso) ---------------------------------
    EntitySpec(
        class_name="RefundRequest",
        redis_key_template="aiqfome_refund_request:{refund_id}",
        file_name="refund_requests.jsonl",
        id_field="refund_id",
        fields=(
            FieldSpec("refund_id", "str", "Identificador único do reembolso", is_key_component=True),
            FieldSpec("customer_id", "str", "Fominha que pediu o reembolso", index="tag"),
            FieldSpec("order_id", "str", "Pedido associado", index="tag"),
            FieldSpec("motivo", "str", "Motivo: item_faltante, item_errado, pedido_atrasado, pedido_nao_chegou", index="tag"),
            FieldSpec("valor", "float", "Valor reembolsado (BRL)", index="numeric"),
            FieldSpec("status", "str", "Status: aprovado, em_analise, negado", index="tag"),
            FieldSpec("data_abertura", "str", "Timestamp ISO de abertura"),
            FieldSpec("data_resolucao", "str | None", "Timestamp ISO da resolução"),
            FieldSpec("descricao", "str", "Descrição do fominha", index="text"),
            FieldSpec("resolucao", "str | None", "Conclusão do atendimento"),
        ),
        relationships=(
            RelationshipSpec("customer", "Fominha", "customer_id", "Customer"),
            RelationshipSpec("order", "Pedido associado", "order_id", "Order"),
        ),
    ),
    # -- Voucher (Cupom de fidelidade) -----------------------------
    EntitySpec(
        class_name="Voucher",
        redis_key_template="aiqfome_voucher:{voucher_id}",
        file_name="vouchers.jsonl",
        id_field="voucher_id",
        fields=(
            FieldSpec("voucher_id", "str", "Identificador único do voucher", is_key_component=True),
            FieldSpec("customer_id", "str", "Fominha dono do voucher", index="tag"),
            FieldSpec("valor", "float", "Valor do voucher (BRL)", index="numeric"),
            FieldSpec("motivo", "str", "Motivo da concessão do voucher"),
            FieldSpec("validade", "str", "Data de validade (YYYY-MM-DD)"),
            FieldSpec("status", "str", "Status: ativo, usado, expirado", index="tag"),
        ),
        relationships=(
            RelationshipSpec("customer", "Fominha dono do voucher", "customer_id", "Customer"),
        ),
    ),
    # -- FeatureStoreRecord (online features for AIQ's recommendations) ------
    # Core of the flagship: online features in Redis read in real time (sub-ms)
    # by AIQ (instant refund decision, next-best-offer). NO index (read via
    # JSON.GET by the tool, not FT.SEARCH) to avoid useless filter tools and
    # to stay under the 128-tool API ceiling.
    EntitySpec(
        class_name="FeatureStoreRecord",
        redis_key_template="aiqfome_features:{customer_id}",
        file_name="feature_store.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Fominha (chave da feature row)", is_key_component=True),
            FieldSpec("pedidos_total", "int", "Feature: total de pedidos desde o cadastro"),
            FieldSpec("pedidos_90d", "int", "Feature: pedidos nos últimos 90 dias"),
            FieldSpec("ticket_medio", "float", "Feature: ticket médio (BRL)"),
            FieldSpec("ltv_12m", "float", "Feature: LTV dos últimos 12 meses (BRL)"),
            FieldSpec("refund_rate_pct", "float", "Feature: taxa de reembolso (%)"),
            FieldSpec("fraude_score", "float", "Feature: score de fraude (0-1, menor é melhor)"),
            FieldSpec("cozinha_favorita", "str", "Feature: cozinha favorita do fominha"),
            FieldSpec("dia_pico", "str", "Feature: dia da semana com mais pedidos"),
            FieldSpec("clube_aiqfome", "bool", "Feature: assinante do clube aiqfome"),
            FieldSpec("voucher_ativo", "float", "Feature: valor do voucher ativo (BRL, 0 se nenhum)"),
            FieldSpec("cidade", "str", "Feature: cidade do fominha (slug)"),
            FieldSpec("fominha_desde", "str", "Feature: cliente desde (YYYY-MM)"),
            FieldSpec("ultima_atualizacao", "str", "Timestamp da última atualização (ISO)"),
        ),
        relationships=(
            RelationshipSpec("customer", "Fominha dono das features", "customer_id", "Customer"),
        ),
    ),
    # -- Policy (Políticas aiqfome) --------------------------------
    EntitySpec(
        class_name="Policy",
        redis_key_template="aiqfome_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria: reembolso, clube, entrega, taxa, pagamento, cancelamento, cupom, alergia, gorjeta, suporte", index="tag"),
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
