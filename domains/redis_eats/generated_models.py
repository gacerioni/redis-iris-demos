"""Generated Context Surface models for the Redis Eats domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Identificador único do cliente",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome completo do cliente",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Email do cliente",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    phone: str | None = ContextField(
        description="Telefone (celular)",
    )

    account_status: str = ContextField(
        description="Status da conta: active, suspended, deactivated",
        index="tag",
    )

    membership_tier: str = ContextField(
        description="Plano de assinatura: none, plus, premium",
        index="tag",
    )

    city: str = ContextField(
        description="Cidade",
        index="tag",
    )

    default_address: str | None = ContextField(
        description="Endereço de entrega padrão",
    )

    lifetime_orders: int = ContextField(
        description="Total de pedidos feitos",
        index="numeric",
        sortable=True,
    )

    account_created_at: str = ContextField(
        description="Data de criação da conta (ISO)",
    )

    orders: Any = ContextRelationship(
        description="Pedidos feitos por este cliente",
        target="Order",
        source_field="customer_id",
    )


class Restaurant(ContextModel):
    """Restaurant entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_restaurant:{restaurant_id}"

    restaurant_id: str = ContextField(
        description="Identificador único do restaurante",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome do restaurante",
        index="text",
        weight=2.0,
    )

    cuisine_type: str = ContextField(
        description="Tipo de cozinha",
        index="tag",
    )

    city: str = ContextField(
        description="Cidade do restaurante",
        index="tag",
    )

    address: str | None = ContextField(
        description="Endereço completo",
    )

    rating: float = ContextField(
        description="Nota média (1-5)",
        index="numeric",
        sortable=True,
    )

    avg_prep_time_mins: int = ContextField(
        description="Tempo médio de preparo em minutos",
        index="numeric",
    )

    status: str = ContextField(
        description="Status operacional: open, closed, temporarily_closed",
        index="tag",
    )

    orders: Any = ContextRelationship(
        description="Pedidos desse restaurante",
        target="Order",
        source_field="restaurant_id",
    )


class Driver(ContextModel):
    """Driver entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_driver:{driver_id}"

    driver_id: str = ContextField(
        description="Identificador único do motoboy",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Nome completo do motoboy",
        index="text",
        weight=2.0,
    )

    phone: str | None = ContextField(
        description="Telefone do motoboy",
    )

    vehicle_type: str = ContextField(
        description="Tipo de veículo: car, bike, scooter",
        index="tag",
    )

    current_status: str = ContextField(
        description="Status: available, en_route, at_restaurant, delivering, offline",
        index="tag",
    )

    rating: float = ContextField(
        description="Nota média do motoboy (1-5)",
        index="numeric",
        sortable=True,
    )

    city: str = ContextField(
        description="Cidade onde opera",
        index="tag",
    )

    active_order_id: str | None = ContextField(
        description="Pedido atualmente em rota",
        index="tag",
    )

    status_update: str | None = ContextField(
        description="Última mensagem de status do motoboy",
        index="text",
    )

    status_updated_at: str | None = ContextField(
        description="Timestamp ISO da última atualização",
    )


class Order(ContextModel):
    """Order entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_order:{order_id}"

    order_id: str = ContextField(
        description="Identificador único do pedido",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente que fez o pedido",
        index="tag",
    )

    restaurant_id: str = ContextField(
        description="Restaurante que prepara o pedido",
        index="tag",
    )

    driver_id: str | None = ContextField(
        description="Motoboy designado",
        index="tag",
    )

    status: str = ContextField(
        description="Status do pedido: placed, confirmed, preparing, ready, picked_up, in_transit, delivered, cancelled",
        index="tag",
    )

    order_total: float = ContextField(
        description="Valor total cobrado (BRL)",
        index="numeric",
        sortable=True,
    )

    items_summary: str = ContextField(
        description="Resumo legível dos itens do pedido",
        index="text",
    )

    placed_at: str = ContextField(
        description="Timestamp ISO de quando o pedido foi feito",
    )

    estimated_delivery: str | None = ContextField(
        description="Timestamp ISO da entrega estimada",
    )

    delivered_at: str | None = ContextField(
        description="Timestamp ISO da entrega real",
    )

    delivery_address: str | None = ContextField(
        description="Endereço de entrega deste pedido",
    )

    city: str = ContextField(
        description="Cidade da entrega",
        index="tag",
    )

    restaurant_name: str | None = ContextField(
        description="Nome do restaurante (denormalizado)",
        index="text",
        weight=1.2,
    )

    driver_name: str | None = ContextField(
        description="Nome do motoboy (denormalizado)",
    )

    cancelled_at: str | None = ContextField(
        description="Timestamp ISO do cancelamento",
    )

    cancellation_reason: str | None = ContextField(
        description="Motivo do cancelamento",
    )

    customer: Any = ContextRelationship(
        description="Cliente que fez o pedido",
        target="Customer",
        source_field="customer_id",
    )

    restaurant: Any = ContextRelationship(
        description="Restaurante que prepara o pedido",
        target="Restaurant",
        source_field="restaurant_id",
    )

    driver: Any = ContextRelationship(
        description="Motoboy que entrega o pedido",
        target="Driver",
        source_field="driver_id",
    )


class OrderItem(ContextModel):
    """OrderItem entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_order_item:{item_id}"

    item_id: str = ContextField(
        description="Identificador único do item",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Pedido pai",
        index="tag",
    )

    item_name: str = ContextField(
        description="Nome do item do cardápio",
        index="text",
    )

    quantity: int = ContextField(
        description="Quantidade pedida",
        index="numeric",
    )

    unit_price: float = ContextField(
        description="Preço unitário (BRL)",
        index="numeric",
    )

    modifications: str | None = ContextField(
        description="Modificações: sem cebola, bem passado, etc.",
    )

    special_instructions: str | None = ContextField(
        description="Instruções especiais de entrega",
    )

    order: Any = ContextRelationship(
        description="Pedido pai",
        target="Order",
        source_field="order_id",
    )


class DeliveryEvent(ContextModel):
    """DeliveryEvent entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_delivery_event:{event_id}"

    event_id: str = ContextField(
        description="Identificador único do evento",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Pedido associado",
        index="tag",
    )

    event_type: str = ContextField(
        description="Tipo: placed, confirmed, preparing, ready, driver_assigned, picked_up, en_route, delivered, cancelled",
        index="tag",
    )

    timestamp: str = ContextField(
        description="Timestamp ISO do evento",
    )

    description: str = ContextField(
        description="Descrição legível do evento",
        index="text",
    )

    actor: str = ContextField(
        description="Quem gerou: customer, restaurant, driver, system",
        index="tag",
    )

    order: Any = ContextRelationship(
        description="Pedido associado",
        target="Order",
        source_field="order_id",
    )


class Payment(ContextModel):
    """Payment entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_payment:{payment_id}"

    payment_id: str = ContextField(
        description="Identificador único do pagamento",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Pedido associado",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Cliente que pagou",
        index="tag",
    )

    subtotal: float = ContextField(
        description="Subtotal dos itens (BRL)",
        index="numeric",
    )

    delivery_fee: float = ContextField(
        description="Taxa de entrega (BRL)",
        index="numeric",
    )

    service_fee: float = ContextField(
        description="Taxa de serviço (BRL)",
        index="numeric",
    )

    tax: float = ContextField(
        description="Impostos (BRL, geralmente 0 no BR)",
        index="numeric",
    )

    tip: float = ContextField(
        description="Gorjeta do motoboy (BRL)",
        index="numeric",
    )

    discount: float = ContextField(
        description="Desconto aplicado (BRL)",
        index="numeric",
    )

    total_charged: float = ContextField(
        description="Valor final cobrado (BRL)",
        index="numeric",
        sortable=True,
    )

    payment_method: str = ContextField(
        description="Forma de pagamento: pix, visa_4242, mastercard_8888, picpay, apple_pay",
        index="tag",
    )

    promo_code: str | None = ContextField(
        description="Código promocional aplicado",
        index="tag",
    )

    refund_amount: float = ContextField(
        description="Valor de estorno (0 se nenhum)",
        index="numeric",
    )

    refund_status: str = ContextField(
        description="Status do estorno: none, pending, completed",
        index="tag",
    )

    refund_reason: str | None = ContextField(
        description="Motivo do estorno",
    )

    order: Any = ContextRelationship(
        description="Pedido associado",
        target="Order",
        source_field="order_id",
    )

    customer: Any = ContextRelationship(
        description="Cliente que pagou",
        target="Customer",
        source_field="customer_id",
    )


class SupportTicket(ContextModel):
    """SupportTicket entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_support_ticket:{ticket_id}"

    ticket_id: str = ContextField(
        description="Identificador único do chamado",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Cliente que abriu o chamado",
        index="tag",
    )

    order_id: str | None = ContextField(
        description="Pedido relacionado",
        index="tag",
    )

    category: str = ContextField(
        description="Categoria: late_delivery, wrong_item, missing_item, billing, account, other",
        index="tag",
    )

    status: str = ContextField(
        description="Status: open, in_progress, resolved, closed",
        index="tag",
    )

    created_at: str = ContextField(
        description="Timestamp ISO de abertura",
    )

    resolved_at: str | None = ContextField(
        description="Timestamp ISO de resolução",
    )

    summary: str = ContextField(
        description="Resumo do chamado",
        index="text",
    )

    resolution: str | None = ContextField(
        description="Como foi resolvido",
    )

    customer: Any = ContextRelationship(
        description="Cliente que abriu o chamado",
        target="Customer",
        source_field="customer_id",
    )

    order: Any = ContextRelationship(
        description="Pedido relacionado",
        target="Order",
        source_field="order_id",
    )


class Policy(ContextModel):
    """Policy entity for the Redis Eats domain."""

    __redis_key_template__ = "redis_eats_policy:{policy_id}"

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
        description="Categoria da política",
        index="tag",
    )

    content: str = ContextField(
        description="Texto completo da política",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Embedding vetorial do conteúdo da política",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
