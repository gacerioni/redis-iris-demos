"""Redis Eats — definições de modelo de dados (single source of truth).

Cada EntitySpec governa:
  • Geração do ContextModel
  • Criação do índice Redis Search
  • Geração de dados de exemplo
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
        redis_key_template="redis_eats_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Identificador único do cliente", is_key_component=True),
            FieldSpec("name", "str", "Nome completo do cliente", index="text", weight=2.0),
            FieldSpec("email", "str", "Email do cliente", index="text", weight=1.5, no_stem=True),
            FieldSpec("phone", "str | None", "Telefone (celular)"),
            FieldSpec("account_status", "str", "Status da conta: active, suspended, deactivated", index="tag"),
            FieldSpec("membership_tier", "str", "Plano de assinatura: none, plus, premium", index="tag"),
            FieldSpec("city", "str", "Cidade", index="tag"),
            FieldSpec("default_address", "str | None", "Endereço de entrega padrão"),
            FieldSpec("lifetime_orders", "int", "Total de pedidos feitos", index="numeric", sortable=True),
            FieldSpec("account_created_at", "str", "Data de criação da conta (ISO)"),
        ),
        relationships=(
            RelationshipSpec("orders", "Pedidos feitos por este cliente", "customer_id", "list[Order]"),
        ),
    ),
    # ── Restaurant (Restaurante) ────────────────────────────────
    EntitySpec(
        class_name="Restaurant",
        redis_key_template="redis_eats_restaurant:{restaurant_id}",
        file_name="restaurants.jsonl",
        id_field="restaurant_id",
        fields=(
            FieldSpec("restaurant_id", "str", "Identificador único do restaurante", is_key_component=True),
            FieldSpec("name", "str", "Nome do restaurante", index="text", weight=2.0),
            FieldSpec("cuisine_type", "str", "Tipo de cozinha", index="tag"),
            FieldSpec("city", "str", "Cidade do restaurante", index="tag"),
            FieldSpec("address", "str | None", "Endereço completo"),
            FieldSpec("rating", "float", "Nota média (1-5)", index="numeric", sortable=True),
            FieldSpec("avg_prep_time_mins", "int", "Tempo médio de preparo em minutos", index="numeric"),
            FieldSpec("status", "str", "Status operacional: open, closed, temporarily_closed", index="tag"),
        ),
        relationships=(
            RelationshipSpec("orders", "Pedidos desse restaurante", "restaurant_id", "list[Order]"),
        ),
    ),
    # ── Driver (Motoboy) ────────────────────────────────────────
    EntitySpec(
        class_name="Driver",
        redis_key_template="redis_eats_driver:{driver_id}",
        file_name="drivers.jsonl",
        id_field="driver_id",
        fields=(
            FieldSpec("driver_id", "str", "Identificador único do motoboy", is_key_component=True),
            FieldSpec("name", "str", "Nome completo do motoboy", index="text", weight=2.0),
            FieldSpec("phone", "str | None", "Telefone do motoboy"),
            FieldSpec("vehicle_type", "str", "Tipo de veículo: car, bike, scooter", index="tag"),
            FieldSpec("current_status", "str", "Status: available, en_route, at_restaurant, delivering, offline", index="tag"),
            FieldSpec("rating", "float", "Nota média do motoboy (1-5)", index="numeric", sortable=True),
            FieldSpec("city", "str", "Cidade onde opera", index="tag"),
            FieldSpec("active_order_id", "str | None", "Pedido atualmente em rota", index="tag"),
            FieldSpec("status_update", "str | None", "Última mensagem de status do motoboy", index="text"),
            FieldSpec("status_updated_at", "str | None", "Timestamp ISO da última atualização"),
        ),
    ),
    # ── Order (Pedido) ──────────────────────────────────────────
    EntitySpec(
        class_name="Order",
        redis_key_template="redis_eats_order:{order_id}",
        file_name="orders.jsonl",
        id_field="order_id",
        fields=(
            FieldSpec("order_id", "str", "Identificador único do pedido", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente que fez o pedido", index="tag"),
            FieldSpec("restaurant_id", "str", "Restaurante que prepara o pedido", index="tag"),
            FieldSpec("driver_id", "str | None", "Motoboy designado", index="tag"),
            FieldSpec("status", "str", "Status do pedido: placed, confirmed, preparing, ready, picked_up, in_transit, delivered, cancelled", index="tag"),
            FieldSpec("order_total", "float", "Valor total cobrado (BRL)", index="numeric", sortable=True),
            FieldSpec("items_summary", "str", "Resumo legível dos itens do pedido", index="text"),
            FieldSpec("placed_at", "str", "Timestamp ISO de quando o pedido foi feito"),
            FieldSpec("estimated_delivery", "str | None", "Timestamp ISO da entrega estimada"),
            FieldSpec("delivered_at", "str | None", "Timestamp ISO da entrega real"),
            FieldSpec("delivery_address", "str | None", "Endereço de entrega deste pedido"),
            FieldSpec("city", "str", "Cidade da entrega", index="tag"),
            FieldSpec("restaurant_name", "str | None", "Nome do restaurante (denormalizado)", index="text", weight=1.2),
            FieldSpec("driver_name", "str | None", "Nome do motoboy (denormalizado)"),
            FieldSpec("cancelled_at", "str | None", "Timestamp ISO do cancelamento"),
            FieldSpec("cancellation_reason", "str | None", "Motivo do cancelamento"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente que fez o pedido", "customer_id", "Customer"),
            RelationshipSpec("restaurant", "Restaurante que prepara o pedido", "restaurant_id", "Restaurant"),
            RelationshipSpec("driver", "Motoboy que entrega o pedido", "driver_id", "Driver"),
        ),
    ),
    # ── OrderItem (Item do Pedido) ──────────────────────────────
    EntitySpec(
        class_name="OrderItem",
        redis_key_template="redis_eats_order_item:{item_id}",
        file_name="order_items.jsonl",
        id_field="item_id",
        fields=(
            FieldSpec("item_id", "str", "Identificador único do item", is_key_component=True),
            FieldSpec("order_id", "str", "Pedido pai", index="tag"),
            FieldSpec("item_name", "str", "Nome do item do cardápio", index="text"),
            FieldSpec("quantity", "int", "Quantidade pedida", index="numeric"),
            FieldSpec("unit_price", "float", "Preço unitário (BRL)", index="numeric"),
            FieldSpec("modifications", "str | None", "Modificações: sem cebola, bem passado, etc."),
            FieldSpec("special_instructions", "str | None", "Instruções especiais de entrega"),
        ),
        relationships=(
            RelationshipSpec("order", "Pedido pai", "order_id", "Order"),
        ),
    ),
    # ── DeliveryEvent (Evento de Entrega) ───────────────────────
    EntitySpec(
        class_name="DeliveryEvent",
        redis_key_template="redis_eats_delivery_event:{event_id}",
        file_name="delivery_events.jsonl",
        id_field="event_id",
        fields=(
            FieldSpec("event_id", "str", "Identificador único do evento", is_key_component=True),
            FieldSpec("order_id", "str", "Pedido associado", index="tag"),
            FieldSpec("event_type", "str", "Tipo: placed, confirmed, preparing, ready, driver_assigned, picked_up, en_route, delivered, cancelled", index="tag"),
            FieldSpec("timestamp", "str", "Timestamp ISO do evento"),
            FieldSpec("description", "str", "Descrição legível do evento", index="text"),
            FieldSpec("actor", "str", "Quem gerou: customer, restaurant, driver, system", index="tag"),
        ),
        relationships=(
            RelationshipSpec("order", "Pedido associado", "order_id", "Order"),
        ),
    ),
    # ── Payment (Pagamento) ─────────────────────────────────────
    EntitySpec(
        class_name="Payment",
        redis_key_template="redis_eats_payment:{payment_id}",
        file_name="payments.jsonl",
        id_field="payment_id",
        fields=(
            FieldSpec("payment_id", "str", "Identificador único do pagamento", is_key_component=True),
            FieldSpec("order_id", "str", "Pedido associado", index="tag"),
            FieldSpec("customer_id", "str", "Cliente que pagou", index="tag"),
            FieldSpec("subtotal", "float", "Subtotal dos itens (BRL)", index="numeric"),
            FieldSpec("delivery_fee", "float", "Taxa de entrega (BRL)", index="numeric"),
            FieldSpec("service_fee", "float", "Taxa de serviço (BRL)", index="numeric"),
            FieldSpec("tax", "float", "Impostos (BRL, geralmente 0 no BR)", index="numeric"),
            FieldSpec("tip", "float", "Gorjeta do motoboy (BRL)", index="numeric"),
            FieldSpec("discount", "float", "Desconto aplicado (BRL)", index="numeric"),
            FieldSpec("total_charged", "float", "Valor final cobrado (BRL)", index="numeric", sortable=True),
            FieldSpec("payment_method", "str", "Forma de pagamento: pix, visa_4242, mastercard_8888, picpay, apple_pay", index="tag"),
            FieldSpec("promo_code", "str | None", "Código promocional aplicado", index="tag"),
            FieldSpec("refund_amount", "float", "Valor de estorno (0 se nenhum)", index="numeric"),
            FieldSpec("refund_status", "str", "Status do estorno: none, pending, completed", index="tag"),
            FieldSpec("refund_reason", "str | None", "Motivo do estorno"),
        ),
        relationships=(
            RelationshipSpec("order", "Pedido associado", "order_id", "Order"),
            RelationshipSpec("customer", "Cliente que pagou", "customer_id", "Customer"),
        ),
    ),
    # ── SupportTicket (Chamado de Atendimento) ──────────────────
    EntitySpec(
        class_name="SupportTicket",
        redis_key_template="redis_eats_support_ticket:{ticket_id}",
        file_name="support_tickets.jsonl",
        id_field="ticket_id",
        fields=(
            FieldSpec("ticket_id", "str", "Identificador único do chamado", is_key_component=True),
            FieldSpec("customer_id", "str", "Cliente que abriu o chamado", index="tag"),
            FieldSpec("order_id", "str | None", "Pedido relacionado", index="tag"),
            FieldSpec("category", "str", "Categoria: late_delivery, wrong_item, missing_item, billing, account, other", index="tag"),
            FieldSpec("status", "str", "Status: open, in_progress, resolved, closed", index="tag"),
            FieldSpec("created_at", "str", "Timestamp ISO de abertura"),
            FieldSpec("resolved_at", "str | None", "Timestamp ISO de resolução"),
            FieldSpec("summary", "str", "Resumo do chamado", index="text"),
            FieldSpec("resolution", "str | None", "Como foi resolvido"),
        ),
        relationships=(
            RelationshipSpec("customer", "Cliente que abriu o chamado", "customer_id", "Customer"),
            RelationshipSpec("order", "Pedido relacionado", "order_id", "Order"),
        ),
    ),
    # ── Policy (Política) ───────────────────────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="redis_eats_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Identificador único da política", is_key_component=True),
            FieldSpec("title", "str", "Título da política", index="text", weight=2.0),
            FieldSpec("category", "str", "Categoria da política", index="tag"),
            FieldSpec("content", "str", "Texto completo da política", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Embedding vetorial do conteúdo da política",
                index="vector", vector_dim=1536, distance_metric="cosine",
            ),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
