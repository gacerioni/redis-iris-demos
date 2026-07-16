"""Generated Context Surface models for the aiqfome domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Identificador único do fominha",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Nome completo do fominha",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Email do fominha",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    cidade: str = ContextField(
        description="Cidade do fominha",
        index="tag",
    )

    bairro: str = ContextField(
        description="Bairro do endereço principal",
        index="tag",
    )

    fominha_desde: str = ContextField(
        description="Cliente aiqfome desde (YYYY-MM)",
    )

    clube_aiqfome: str = ContextField(
        description="Assinante do clube aiqfome (frete grátis em parceiros): sim, nao",
        index="tag",
    )

    endereco_entrega: str = ContextField(
        description="Endereço de entrega padrão",
    )

    telefone: str = ContextField(
        description="Celular mascarado (ex: +55 44 9****-4321)",
    )

    orders: Any = ContextRelationship(
        description="Pedidos do fominha",
        target="Order",
        source_field="customer_id",
    )

    vouchers: Any = ContextRelationship(
        description="Vouchers do fominha",
        target="Voucher",
        source_field="customer_id",
    )

    features: Any = ContextRelationship(
        description="Features online do fominha",
        target="FeatureStoreRecord",
        source_field="customer_id",
    )


class Merchant(ContextModel):
    """Merchant entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_merchant:{merchant_id}"

    merchant_id: str = ContextField(
        description="Identificador único do restaurante",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Nome do restaurante",
        index="text",
        weight=2.0,
    )

    cozinha: str = ContextField(
        description="Tipo de cozinha: japonesa, pizza, lanches, acai_sobremesas, caseira, pastelaria, massas, churrasco, vegetariana, mexicana, padaria_cafe",
        index="tag",
    )

    rating: float = ContextField(
        description="Nota média do restaurante (1-5)",
        index="numeric",
        sortable=True,
    )

    delivery_fee: float = ContextField(
        description="Taxa de entrega (BRL, 0 nos parceiros do clube)",
        index="numeric",
    )

    eta_min: int = ContextField(
        description="Tempo estimado de entrega em minutos",
        index="numeric",
        sortable=True,
    )

    cidade: str = ContextField(
        description="Cidade do restaurante",
        index="tag",
    )

    bairro: str = ContextField(
        description="Bairro do restaurante",
        index="tag",
    )

    aberto: str = ContextField(
        description="Aberto agora: sim, nao",
        index="tag",
    )

    clube_parceiro: str = ContextField(
        description="Parceiro do clube aiqfome (frete grátis pra assinantes): sim, nao",
        index="tag",
    )

    lat: float = ContextField(
        description="Latitude do restaurante",
        index="numeric",
    )

    lon: float = ContextField(
        description="Longitude do restaurante",
        index="numeric",
    )

    geo: str = ContextField(
        description="Coordenada no formato 'lon,lat', pronta pra um índice GEO futuro",
    )

    descricao: str = ContextField(
        description="Descrição curta do restaurante",
        index="text",
    )

    dishes: Any = ContextRelationship(
        description="Pratos do cardápio do restaurante",
        target="Dish",
        source_field="merchant_id",
    )

    orders: Any = ContextRelationship(
        description="Pedidos do restaurante",
        target="Order",
        source_field="merchant_id",
    )


class Dish(ContextModel):
    """Dish entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_dish:{dish_id}"

    dish_id: str = ContextField(
        description="Identificador único do prato",
        is_key_component=True,
    )

    merchant_id: str = ContextField(
        description="Restaurante dono do prato",
        index="tag",
    )

    nome: str = ContextField(
        description="Nome do prato",
        index="text",
        weight=2.0,
    )

    descricao: str = ContextField(
        description="Descrição rica do prato em PT-BR",
        index="text",
    )

    categoria: str = ContextField(
        description="Categoria: temaki, sushi, combo, entrada, pizza, burger, porcao, acai, marmita, pastel, massa, risoto, espeto, churrasco, vegano, salada, taco, burrito, lanche, doce, bebida",
        index="tag",
    )

    preco: float = ContextField(
        description="Preço do prato (BRL)",
        index="numeric",
        sortable=True,
    )

    rating: float = ContextField(
        description="Nota média do prato (1-5)",
        index="numeric",
    )

    popularity: int = ContextField(
        description="Popularidade 1-100 (usada pra reranking)",
        index="numeric",
        sortable=True,
    )

    tags: list[str] = ContextField(
        description="Tags do prato: mais_pedido, promo, picante, vegetariano, vegano, sem_gluten",
        index="tag",
    )

    alergenos: list[str] = ContextField(
        description="Alérgenos presentes: camarao, gluten, lactose, amendoim, ovo (lista vazia se nenhum)",
        index="tag",
    )

    serve_pessoas: int = ContextField(
        description="Quantas pessoas o prato serve",
        index="numeric",
    )

    content_embedding: list[float] = ContextField(
        description="Embedding vetorial de nome + descrição",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )

    merchant: Any = ContextRelationship(
        description="Restaurante dono do prato",
        target="Merchant",
        source_field="merchant_id",
    )


class Order(ContextModel):
    """Order entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_order:{order_id}"

    order_id: str = ContextField(
        description="Identificador do pedido (ex: AIQ-8842)",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Fominha que fez o pedido",
        index="tag",
    )

    merchant_id: str = ContextField(
        description="Restaurante do pedido",
        index="tag",
    )

    itens: list[dict] = ContextField(
        description="Itens do pedido (dish_id, nome, qty, preco)",
    )

    total: float = ContextField(
        description="Total do pedido (BRL), soma dos itens",
        index="numeric",
        sortable=True,
    )

    status: str = ContextField(
        description="Status: entregue, saiu_para_entrega, em_preparo, recebido, cancelado",
        index="tag",
    )

    courier_id: str | None = ContextField(
        description="Entregador designado",
        index="tag",
    )

    criado_em: str = ContextField(
        description="Timestamp ISO de criação do pedido",
        sortable=True,
    )

    entregue_em: str | None = ContextField(
        description="Timestamp ISO da entrega (null se não entregue)",
    )

    pagamento: str = ContextField(
        description="Forma de pagamento: pix, credito, dinheiro",
        index="tag",
    )

    observacao: str | None = ContextField(
        description="Observações do pedido (nota do cliente ou ocorrência registrada)",
        index="text",
    )

    customer: Any = ContextRelationship(
        description="Fominha que fez o pedido",
        target="Customer",
        source_field="customer_id",
    )

    merchant: Any = ContextRelationship(
        description="Restaurante do pedido",
        target="Merchant",
        source_field="merchant_id",
    )

    courier: Any = ContextRelationship(
        description="Entregador do pedido",
        target="Courier",
        source_field="courier_id",
    )


class Courier(ContextModel):
    """Courier entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_courier:{courier_id}"

    courier_id: str = ContextField(
        description="Identificador único do entregador",
        is_key_component=True,
    )

    nome: str = ContextField(
        description="Nome do entregador",
        index="text",
        weight=2.0,
    )

    veiculo: str = ContextField(
        description="Veículo: moto, bike",
        index="tag",
    )

    status: str = ContextField(
        description="Status: em_rota, disponivel",
        index="tag",
    )

    posicao_atual: str = ContextField(
        description="Posição atual em texto (ex: a 1,2 km, subindo a Av. Colombo)",
    )

    avaliacao: float = ContextField(
        description="Nota média do entregador (1-5)",
        index="numeric",
    )


class RefundRequest(ContextModel):
    """RefundRequest entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_refund_request:{refund_id}"

    refund_id: str = ContextField(
        description="Identificador único do reembolso",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Fominha que pediu o reembolso",
        index="tag",
    )

    order_id: str = ContextField(
        description="Pedido associado",
        index="tag",
    )

    motivo: str = ContextField(
        description="Motivo: item_faltante, item_errado, pedido_atrasado, pedido_nao_chegou",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor reembolsado (BRL)",
        index="numeric",
    )

    status: str = ContextField(
        description="Status: aprovado, em_analise, negado",
        index="tag",
    )

    data_abertura: str = ContextField(
        description="Timestamp ISO de abertura",
    )

    data_resolucao: str | None = ContextField(
        description="Timestamp ISO da resolução",
    )

    descricao: str = ContextField(
        description="Descrição do fominha",
        index="text",
    )

    resolucao: str | None = ContextField(
        description="Conclusão do atendimento",
    )

    customer: Any = ContextRelationship(
        description="Fominha",
        target="Customer",
        source_field="customer_id",
    )

    order: Any = ContextRelationship(
        description="Pedido associado",
        target="Order",
        source_field="order_id",
    )


class Voucher(ContextModel):
    """Voucher entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_voucher:{voucher_id}"

    voucher_id: str = ContextField(
        description="Identificador único do voucher",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Fominha dono do voucher",
        index="tag",
    )

    valor: float = ContextField(
        description="Valor do voucher (BRL)",
        index="numeric",
    )

    motivo: str = ContextField(
        description="Motivo da concessão do voucher",
    )

    validade: str = ContextField(
        description="Data de validade (YYYY-MM-DD)",
    )

    status: str = ContextField(
        description="Status: ativo, usado, expirado",
        index="tag",
    )

    customer: Any = ContextRelationship(
        description="Fominha dono do voucher",
        target="Customer",
        source_field="customer_id",
    )


class FeatureStoreRecord(ContextModel):
    """FeatureStoreRecord entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_features:{customer_id}"

    customer_id: str = ContextField(
        description="Fominha (chave da feature row)",
        is_key_component=True,
    )

    pedidos_total: int = ContextField(
        description="Feature: total de pedidos desde o cadastro",
    )

    pedidos_90d: int = ContextField(
        description="Feature: pedidos nos últimos 90 dias",
    )

    ticket_medio: float = ContextField(
        description="Feature: ticket médio (BRL)",
    )

    ltv_12m: float = ContextField(
        description="Feature: LTV dos últimos 12 meses (BRL)",
    )

    refund_rate_pct: float = ContextField(
        description="Feature: taxa de reembolso (%)",
    )

    fraude_score: float = ContextField(
        description="Feature: score de fraude (0-1, menor é melhor)",
    )

    cozinha_favorita: str = ContextField(
        description="Feature: cozinha favorita do fominha",
    )

    dia_pico: str = ContextField(
        description="Feature: dia da semana com mais pedidos",
    )

    clube_aiqfome: bool = ContextField(
        description="Feature: assinante do clube aiqfome",
    )

    voucher_ativo: float = ContextField(
        description="Feature: valor do voucher ativo (BRL, 0 se nenhum)",
    )

    cidade: str = ContextField(
        description="Feature: cidade do fominha (slug)",
    )

    fominha_desde: str = ContextField(
        description="Feature: cliente desde (YYYY-MM)",
    )

    ultima_atualizacao: str = ContextField(
        description="Timestamp da última atualização (ISO)",
    )

    customer: Any = ContextRelationship(
        description="Fominha dono das features",
        target="Customer",
        source_field="customer_id",
    )


class Policy(ContextModel):
    """Policy entity for the aiqfome domain."""

    __redis_key_template__ = "aiqfome_policy:{policy_id}"

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
        description="Categoria: reembolso, clube, entrega, taxa, pagamento, cancelamento, cupom, alergia, gorjeta, suporte",
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
