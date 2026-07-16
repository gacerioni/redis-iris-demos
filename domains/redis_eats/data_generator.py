"""Gera dados de exemplo pro Redis Eats — demo de delivery brasileiro com humor Copa do Mundo.

Personagens, restaurantes e eventos foram desenhados pra:
1. Mostrar Context Surface ganhando do RAG simples (riqueza de contexto operacional)
2. Tornar a demo memorável em PT-BR com humor paulistano
3. Cobrir todos os 4 demo paths originais (pedido atrasado, pagamento+assinatura,
   suporte, multi-entidade)
"""

from __future__ import annotations

import json
import os
import sys
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "redis_eats"


def ts(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input=texts, model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in resp.data]


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMERS (5) — paulistanos com personagem
# ═══════════════════════════════════════════════════════════════════════════

DEMO_USER_ID = "CUST_DEMO_001"

CUSTOMERS = [
    {
        "customer_id": DEMO_USER_ID,
        "name": "Gabriel Cerioni",
        "email": "gabriel.cerioni@redis.com",
        "phone": "+55 11 98765-4321",
        "account_status": "active",
        "membership_tier": "plus",
        "city": "São Paulo",
        "default_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP, 05433-010",
        "lifetime_orders": 47,
        "account_created_at": ts(now - timedelta(days=420)),
    },
    {
        "customer_id": "CUST_002",
        "name": "Janine Marjoub",
        "email": "janine.marjoub@example.com.br",
        "phone": "+55 11 99123-4567",
        "account_status": "active",
        "membership_tier": "premium",
        "city": "São Paulo",
        "default_address": "Rua Aspicuelta, 320, Vila Madalena, São Paulo - SP, 05433-010",
        "lifetime_orders": 112,
        "account_created_at": ts(now - timedelta(days=820)),
    },
    {
        "customer_id": "CUST_003",
        "name": "Diego Linke",
        "email": "diego.linke@example.com.br",
        "phone": "+55 11 98555-0303",
        "account_status": "active",
        "membership_tier": "none",
        "city": "São Paulo",
        "default_address": "Rua das Palmeiras, 850, Pompeia, São Paulo - SP, 05021-010",
        "lifetime_orders": 23,
        "account_created_at": ts(now - timedelta(days=180)),
    },
    {
        "customer_id": "CUST_004",
        "name": "Gabriella Candelaria",
        "email": "gabriella.candelaria@example.com.br",
        "phone": "+55 11 97444-0404",
        "account_status": "suspended",
        "membership_tier": "none",
        "city": "São Paulo",
        "default_address": "Av. Celso Garcia, 1500, Tatuapé, São Paulo - SP, 03014-001",
        "lifetime_orders": 8,
        "account_created_at": ts(now - timedelta(days=95)),
    },
    {
        "customer_id": "CUST_005",
        "name": "Miller Moreno",
        "email": "miller.moreno@example.com.br",
        "phone": "+55 11 96333-0505",
        "account_status": "active",
        "membership_tier": "plus",
        "city": "São Paulo",
        "default_address": "Rua Funchal, 320, Itaim Bibi, São Paulo - SP, 04551-060",
        "lifetime_orders": 61,
        "account_created_at": ts(now - timedelta(days=540)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  RESTAURANTS (10) — paulistanos com personalidade
# ═══════════════════════════════════════════════════════════════════════════

RESTAURANTS = [
    {
        "restaurant_id": "REST_001",
        "name": "Borracharia e Pizzaria o Rato que Ri",
        "cuisine_type": "Pizzaria",
        "city": "São Paulo",
        "address": "Rua Teodoro Sampaio, 1985, Pinheiros, São Paulo - SP",
        "rating": 4.6,
        "avg_prep_time_mins": 28,
        "status": "open",
    },
    {
        "restaurant_id": "REST_002",
        "name": "Bar do Juca: Cerveja Gelada, Documentos Reconhecidos",
        "cuisine_type": "Boteco",
        "city": "São Paulo",
        "address": "Rua Aspicuelta, 480, Vila Madalena, São Paulo - SP",
        "rating": 4.3,
        "avg_prep_time_mins": 18,
        "status": "open",
    },
    {
        "restaurant_id": "REST_003",
        "name": "Pastelaria da Dona Cida — Sem Caixa Eletrônico",
        "cuisine_type": "Pastelaria",
        "city": "São Paulo",
        "address": "Largo da Batata, 145, Pinheiros, São Paulo - SP",
        "rating": 4.5,
        "avg_prep_time_mins": 12,
        "status": "open",
    },
    {
        "restaurant_id": "REST_004",
        "name": "Sushi do Seu Joaquim (Filho do Dono da Padaria)",
        "cuisine_type": "Japonesa",
        "city": "São Paulo",
        "address": "Alameda Lorena, 1300, Jardins, São Paulo - SP",
        "rating": 4.4,
        "avg_prep_time_mins": 25,
        "status": "open",
    },
    {
        "restaurant_id": "REST_005",
        "name": "Pizzaria Forno a Lenha do Vô — Sem Lenha Desde 2003",
        "cuisine_type": "Pizzaria",
        "city": "São Paulo",
        "address": "Rua Tagipuru, 220, Barra Funda, São Paulo - SP",
        "rating": 4.2,
        "avg_prep_time_mins": 32,
        "status": "open",
    },
    {
        "restaurant_id": "REST_006",
        "name": "Espetinho do Magrão (Mas o Magrão Engordou)",
        "cuisine_type": "Espetinho",
        "city": "São Paulo",
        "address": "Rua Aurora, 555, Santa Cecília, São Paulo - SP",
        "rating": 4.7,
        "avg_prep_time_mins": 15,
        "status": "open",
    },
    {
        "restaurant_id": "REST_007",
        "name": "Açaí da Tia Wanda — Aberto Até a Primeira Chuva",
        "cuisine_type": "Açaí",
        "city": "São Paulo",
        "address": "Rua dos Pinheiros, 720, Pinheiros, São Paulo - SP",
        "rating": 4.8,
        "avg_prep_time_mins": 10,
        "status": "temporarily_closed",
    },
    {
        "restaurant_id": "REST_008",
        "name": "Yakisoba do Toninho — Família Japonesa Há Duas Gerações",
        "cuisine_type": "Japonesa",
        "city": "São Paulo",
        "address": "Rua Galvão Bueno, 200, Liberdade, São Paulo - SP",
        "rating": 4.5,
        "avg_prep_time_mins": 20,
        "status": "open",
    },
    {
        "restaurant_id": "REST_009",
        "name": "Hamburgueria Vira-Lata — Burger de Rua, Quase Gourmet",
        "cuisine_type": "Hambúrguer",
        "city": "São Paulo",
        "address": "Rua Augusta, 2840, Cerqueira César, São Paulo - SP",
        "rating": 4.6,
        "avg_prep_time_mins": 22,
        "status": "open",
    },
    {
        "restaurant_id": "REST_010",
        "name": "Casa do Pamonha — A Original, A Outra é Pirata",
        "cuisine_type": "Brasileira",
        "city": "São Paulo",
        "address": "Rua Harmonia, 102, Vila Madalena, São Paulo - SP",
        "rating": 4.4,
        "avg_prep_time_mins": 14,
        "status": "open",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  DRIVERS (4) — motoboys paulistanos
# ═══════════════════════════════════════════════════════════════════════════

DRIVERS = [
    {
        "driver_id": "DRV_001",
        "name": "Wagner Fernandes",
        "phone": "+55 11 95222-1001",
        "vehicle_type": "scooter",
        "current_status": "available",
        "rating": 4.8,
        "city": "São Paulo",
        "active_order_id": None,
        "status_update": None,
        "status_updated_at": None,
    },
    {
        "driver_id": "DRV_002",
        "name": "Carlos Eduardo Souza",
        "phone": "+55 11 95333-2002",
        "vehicle_type": "bike",
        "current_status": "delivering",
        "rating": 4.9,
        "city": "São Paulo",
        "active_order_id": "ORD_008",
        "status_update": "Saí com o pedido, trânsito tranquilo. Chego em uns 8 min.",
        "status_updated_at": ts(now - timedelta(minutes=4)),
    },
    {
        "driver_id": "DRV_003",
        "name": "João Pedro Convocado",
        "phone": "+55 11 95444-3003",
        "vehicle_type": "scooter",
        "current_status": "delivering",
        "rating": 4.5,
        "city": "São Paulo",
        "active_order_id": "ORD_001",
        "status_update": (
            "Furei o pneu na Teodoro Sampaio quando saía da Borracharia o Rato que Ri. "
            "Já troquei (aproveitei e comi uma fatia), tô na Faria Lima mas tá um buzinaço pós-convocação — "
            "tô desviando pela Cardeal Arcoverde. Chego em uns 12 min."
        ),
        "status_updated_at": ts(now - timedelta(minutes=6)),
    },
    {
        "driver_id": "DRV_004",
        "name": "Maicon Junior da Silva",
        "phone": "+55 11 95555-4004",
        "vehicle_type": "car",
        "current_status": "offline",
        "rating": 4.6,
        "city": "São Paulo",
        "active_order_id": None,
        "status_update": None,
        "status_updated_at": None,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  ORDERS (8) — ORD_001 é o flagship da demo (LATE com humor Copa)
# ═══════════════════════════════════════════════════════════════════════════

# ORD_001: pedido atrasado do Gabriel (placed 70min atrás, ETA era 30min atrás, ainda em trânsito)
ord1_placed = now - timedelta(minutes=70)
ord1_est = now - timedelta(minutes=30)

ORDERS = [
    {
        "order_id": "ORD_001", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_001",
        "driver_id": "DRV_003", "status": "in_transit", "order_total": 87.90,
        "items_summary": "Pizza Calabresa Sem Crise (grande) com borda de catupiry, Coca-Cola 2L",
        "placed_at": ts(ord1_placed), "estimated_delivery": ts(ord1_est), "delivered_at": None,
        "delivery_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Borracharia e Pizzaria o Rato que Ri",
        "driver_name": "João Pedro Convocado",
        "cancelled_at": None, "cancellation_reason": None,
    },
    {
        "order_id": "ORD_002", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_008",
        "driver_id": "DRV_002", "status": "delivered", "order_total": 68.50,
        "items_summary": "Yakisoba de Frango Grande, Rolinho Primavera (3un), Coca-Cola Lata",
        "placed_at": ts(now - timedelta(days=2)),
        "estimated_delivery": ts(now - timedelta(days=2) + timedelta(minutes=35)),
        "delivered_at": ts(now - timedelta(days=2) + timedelta(minutes=33)),
        "delivery_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Yakisoba do Toninho — Família Japonesa Há Duas Gerações",
        "driver_name": "Carlos Eduardo Souza",
        "cancelled_at": None, "cancellation_reason": None,
    },
    {
        "order_id": "ORD_003", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_009",
        "driver_id": "DRV_001", "status": "delivered", "order_total": 54.00,
        "items_summary": "Burger Vira-Lata Clássico, Fritas Rústicas, Milkshake Ovomaltine",
        "placed_at": ts(now - timedelta(days=5)),
        "estimated_delivery": ts(now - timedelta(days=5) + timedelta(minutes=30)),
        "delivered_at": ts(now - timedelta(days=5) + timedelta(minutes=28)),
        "delivery_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Hamburgueria Vira-Lata — Burger de Rua, Quase Gourmet",
        "driver_name": "Wagner Fernandes",
        "cancelled_at": None, "cancellation_reason": None,
    },
    {
        "order_id": "ORD_004", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_007",
        "driver_id": "DRV_002", "status": "delivered", "order_total": 32.00,
        "items_summary": "Açaí Tradicional 500ml com banana, granola e leite condensado, Água Mineral",
        "placed_at": ts(now - timedelta(days=10)),
        "estimated_delivery": ts(now - timedelta(days=10) + timedelta(minutes=18)),
        "delivered_at": ts(now - timedelta(days=10) + timedelta(minutes=20)),
        "delivery_address": "Rua Aspicuelta, 750, apto 1804, Pinheiros, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Açaí da Tia Wanda — Aberto Até a Primeira Chuva",
        "driver_name": "Carlos Eduardo Souza",
        "cancelled_at": None, "cancellation_reason": None,
    },
    # Outros clientes ─────────────────────────────────────────────
    {
        "order_id": "ORD_005", "customer_id": "CUST_002", "restaurant_id": "REST_002",
        "driver_id": "DRV_002", "status": "delivered", "order_total": 145.00,
        "items_summary": "Porção de Calabresa Acebolada, Pastel de Queijo (4un), Brahma Long Neck (6un)",
        "placed_at": ts(now - timedelta(days=1)),
        "estimated_delivery": ts(now - timedelta(days=1) + timedelta(minutes=25)),
        "delivered_at": ts(now - timedelta(days=1) + timedelta(minutes=27)),
        "delivery_address": "Rua Aspicuelta, 320, Vila Madalena, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Bar do Juca: Cerveja Gelada, Documentos Reconhecidos",
        "driver_name": "Carlos Eduardo Souza",
        "cancelled_at": None, "cancellation_reason": None,
    },
    {
        "order_id": "ORD_006", "customer_id": "CUST_003", "restaurant_id": "REST_005",
        "driver_id": "DRV_003", "status": "delivered", "order_total": 78.90,
        "items_summary": "Pizza Margherita Grande, Pizza Doce de Chocolate Grande",
        "placed_at": ts(now - timedelta(days=3)),
        "estimated_delivery": ts(now - timedelta(days=3) + timedelta(minutes=42)),
        "delivered_at": ts(now - timedelta(days=3) + timedelta(minutes=50)),
        "delivery_address": "Rua das Palmeiras, 850, Pompeia, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Pizzaria Forno a Lenha do Vô — Sem Lenha Desde 2003",
        "driver_name": "João Pedro Convocado",
        "cancelled_at": None, "cancellation_reason": None,
    },
    {
        "order_id": "ORD_007", "customer_id": "CUST_004", "restaurant_id": "REST_003",
        "driver_id": None, "status": "cancelled", "order_total": 28.00,
        "items_summary": "Pastel de Queijo, Pastel de Carne, Caldo de Cana",
        "placed_at": ts(now - timedelta(days=1)),
        "estimated_delivery": None, "delivered_at": None,
        "delivery_address": "Av. Celso Garcia, 1500, Tatuapé, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Pastelaria da Dona Cida — Sem Caixa Eletrônico",
        "driver_name": None,
        "cancelled_at": ts(now - timedelta(days=1) + timedelta(minutes=4)),
        "cancellation_reason": "Cliente cancelou antes do preparo iniciar",
    },
    {
        "order_id": "ORD_008", "customer_id": "CUST_002", "restaurant_id": "REST_006",
        "driver_id": "DRV_002", "status": "in_transit", "order_total": 42.00,
        "items_summary": "Espetinho Misto (5un), Mandioca Frita, Caldo Verde",
        "placed_at": ts(now - timedelta(minutes=30)),
        "estimated_delivery": ts(now + timedelta(minutes=10)),
        "delivered_at": None,
        "delivery_address": "Rua Aspicuelta, 320, Vila Madalena, São Paulo - SP",
        "city": "São Paulo", "restaurant_name": "Espetinho do Magrão (Mas o Magrão Engordou)",
        "driver_name": "Carlos Eduardo Souza",
        "cancelled_at": None, "cancellation_reason": None,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  ORDER ITEMS — itens de linha de cada pedido
# ═══════════════════════════════════════════════════════════════════════════

ORDER_ITEMS = [
    # ORD_001 — pizza calabresa da Borracharia o Rato que Ri
    {"item_id": "ITEM_001", "order_id": "ORD_001", "item_name": "Pizza Calabresa Sem Crise (grande, 8 fatias)",
     "quantity": 1, "unit_price": 72.00,
     "modifications": "borda recheada de catupiry",
     "special_instructions": "Tocar a campainha primeiro, ligar só se não atender. Porteiro Seu Genival raramente atende interfone depois das 22h."},
    {"item_id": "ITEM_002", "order_id": "ORD_001", "item_name": "Coca-Cola 2L",
     "quantity": 1, "unit_price": 12.00,
     "modifications": None, "special_instructions": None},

    # ORD_002 — Yakisoba do Toninho (Gabriel)
    {"item_id": "ITEM_003", "order_id": "ORD_002", "item_name": "Yakisoba de Frango Grande",
     "quantity": 1, "unit_price": 38.00,
     "modifications": "sem brócolis, mais cenoura, SEM COENTRO", "special_instructions": None},
    {"item_id": "ITEM_004", "order_id": "ORD_002", "item_name": "Rolinho Primavera",
     "quantity": 3, "unit_price": 6.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_005", "order_id": "ORD_002", "item_name": "Coca-Cola Lata",
     "quantity": 1, "unit_price": 5.00, "modifications": None, "special_instructions": None},

    # ORD_003 — Hamburgueria Vira-Lata (esse pedido teve o milkshake faltando → TKT_001)
    {"item_id": "ITEM_006", "order_id": "ORD_003", "item_name": "Burger Vira-Lata Clássico",
     "quantity": 1, "unit_price": 26.00, "modifications": "sem cebola roxa", "special_instructions": None},
    {"item_id": "ITEM_007", "order_id": "ORD_003", "item_name": "Fritas Rústicas",
     "quantity": 1, "unit_price": 11.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_008", "order_id": "ORD_003", "item_name": "Milkshake Ovomaltine",
     "quantity": 1, "unit_price": 13.00, "modifications": "sem flocos por cima", "special_instructions": None},

    # ORD_004 — Açaí da Tia Wanda
    {"item_id": "ITEM_009", "order_id": "ORD_004", "item_name": "Açaí Tradicional 500ml",
     "quantity": 1, "unit_price": 24.00,
     "modifications": "extras: banana, granola, leite condensado", "special_instructions": None},
    {"item_id": "ITEM_010", "order_id": "ORD_004", "item_name": "Água Mineral 500ml",
     "quantity": 1, "unit_price": 8.00, "modifications": None, "special_instructions": None},

    # ORD_005 — Bar do Juca (Janine)
    {"item_id": "ITEM_011", "order_id": "ORD_005", "item_name": "Porção de Calabresa Acebolada",
     "quantity": 1, "unit_price": 45.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_012", "order_id": "ORD_005", "item_name": "Pastel de Queijo",
     "quantity": 4, "unit_price": 10.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_013", "order_id": "ORD_005", "item_name": "Brahma Long Neck",
     "quantity": 6, "unit_price": 10.00, "modifications": "bem geladas", "special_instructions": None},

    # ORD_006 — Pizzaria Forno a Lenha do Vô (Diego)
    {"item_id": "ITEM_014", "order_id": "ORD_006", "item_name": "Pizza Margherita Grande",
     "quantity": 1, "unit_price": 42.00, "modifications": "borda tradicional", "special_instructions": None},
    {"item_id": "ITEM_015", "order_id": "ORD_006", "item_name": "Pizza Doce de Chocolate Grande",
     "quantity": 1, "unit_price": 36.90, "modifications": None, "special_instructions": None},

    # ORD_007 — Pastelaria da Dona Cida (cancelado)
    {"item_id": "ITEM_016", "order_id": "ORD_007", "item_name": "Pastel de Queijo",
     "quantity": 1, "unit_price": 10.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_017", "order_id": "ORD_007", "item_name": "Pastel de Carne",
     "quantity": 1, "unit_price": 12.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_018", "order_id": "ORD_007", "item_name": "Caldo de Cana 500ml",
     "quantity": 1, "unit_price": 6.00, "modifications": None, "special_instructions": None},

    # ORD_008 — Espetinho do Magrão (Janine)
    {"item_id": "ITEM_019", "order_id": "ORD_008", "item_name": "Espetinho Misto",
     "quantity": 5, "unit_price": 6.00, "modifications": "carne mal passada", "special_instructions": None},
    {"item_id": "ITEM_020", "order_id": "ORD_008", "item_name": "Mandioca Frita",
     "quantity": 1, "unit_price": 8.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_021", "order_id": "ORD_008", "item_name": "Caldo Verde Mini",
     "quantity": 1, "unit_price": 4.00, "modifications": None, "special_instructions": None},
]


# ═══════════════════════════════════════════════════════════════════════════
#  DELIVERY EVENTS — timeline detalhada do ORD_001 (LATE, humor Copa)
# ═══════════════════════════════════════════════════════════════════════════

DELIVERY_EVENTS = [
    # ORD_001 — a história principal: 70 minutos de saga
    {"event_id": "EVT_001", "order_id": "ORD_001", "event_type": "placed",
     "timestamp": ts(ord1_placed),
     "description": "Pedido feito por Gabriel Cerioni via app.",
     "actor": "customer"},
    {"event_id": "EVT_002", "order_id": "ORD_001", "event_type": "confirmed",
     "timestamp": ts(ord1_placed + timedelta(minutes=2)),
     "description": "Borracharia e Pizzaria o Rato que Ri confirmou o pedido.",
     "actor": "restaurant"},
    {"event_id": "EVT_003", "order_id": "ORD_001", "event_type": "preparing",
     "timestamp": ts(ord1_placed + timedelta(minutes=4)),
     "description": "Forno aceso. Pizza Calabresa Sem Crise entrou no preparo.",
     "actor": "restaurant"},
    {"event_id": "EVT_004", "order_id": "ORD_001", "event_type": "ready",
     "timestamp": ts(ord1_placed + timedelta(minutes=26)),
     "description": "Pedido pronto pra retirada. Embalagem dupla pra Coca não chacoalhar.",
     "actor": "restaurant"},
    {"event_id": "EVT_005", "order_id": "ORD_001", "event_type": "driver_assigned",
     "timestamp": ts(ord1_placed + timedelta(minutes=30)),
     "description": "Motoboy atribuído: João Pedro Convocado (scooter Honda Pop 110, placa OZB-1453).",
     "actor": "system"},
    {"event_id": "EVT_006", "order_id": "ORD_001", "event_type": "picked_up",
     "timestamp": ts(ord1_placed + timedelta(minutes=34)),
     "description": "João Pedro pegou o pedido na Borracharia. Saindo pela Teodoro Sampaio em direção à Aspicuelta.",
     "actor": "driver"},
    {"event_id": "EVT_007", "order_id": "ORD_001", "event_type": "en_route",
     "timestamp": ts(ord1_placed + timedelta(minutes=36)),
     "description": "Em rota pela Rua Cardeal Arcoverde. Trânsito normal.",
     "actor": "driver"},
    {"event_id": "EVT_008", "order_id": "ORD_001", "event_type": "en_route",
     "timestamp": ts(ord1_placed + timedelta(minutes=42)),
     "description": (
         "Parada de ~3min na Rua Aspicuelta. João Pedro parou pra ver a convocação da Seleção "
         "pela Copa anunciada pelo Adulto Ney em telão de bar — esperava ouvir o próprio nome "
         "(de novo não foi). Voltou pra rota."
     ),
     "actor": "driver"},
    {"event_id": "EVT_009", "order_id": "ORD_001", "event_type": "en_route",
     "timestamp": ts(ord1_placed + timedelta(minutes=52)),
     "description": (
         "Pneu furado na Rua Teodoro Sampaio. João Pedro entrou na Borracharia e Pizzaria o Rato que Ri "
         "pra trocar — 8min de parada (e ele aproveitou pra comer uma fatia)."
     ),
     "actor": "driver"},
    {"event_id": "EVT_010", "order_id": "ORD_001", "event_type": "en_route",
     "timestamp": ts(ord1_placed + timedelta(minutes=62)),
     "description": (
         "De volta na rota, mas a Av. Brigadeiro Faria Lima virou buzinaço pós-convocação do Adulto Ney "
         "(uns gritando bravo, outros aliviados). Desviando pela Cardeal Arcoverde."
     ),
     "actor": "driver"},

    # ORD_002 — entrega normal
    {"event_id": "EVT_011", "order_id": "ORD_002", "event_type": "placed",
     "timestamp": ts(now - timedelta(days=2)),
     "description": "Pedido feito por Gabriel Cerioni.", "actor": "customer"},
    {"event_id": "EVT_012", "order_id": "ORD_002", "event_type": "delivered",
     "timestamp": ts(now - timedelta(days=2) + timedelta(minutes=33)),
     "description": "Entregue. Carlos Eduardo avisou que tocou a campainha duas vezes — Gabriel atendeu.",
     "actor": "driver"},

    # ORD_007 — cancelado pelo cliente
    {"event_id": "EVT_013", "order_id": "ORD_007", "event_type": "placed",
     "timestamp": ts(now - timedelta(days=1)),
     "description": "Pedido feito por Gabriella Candelaria.", "actor": "customer"},
    {"event_id": "EVT_014", "order_id": "ORD_007", "event_type": "cancelled",
     "timestamp": ts(now - timedelta(days=1) + timedelta(minutes=4)),
     "description": "Cancelado pelo cliente antes do restaurante iniciar o preparo.",
     "actor": "customer"},

    # ORD_008 — em rota agora (Mariana)
    {"event_id": "EVT_015", "order_id": "ORD_008", "event_type": "placed",
     "timestamp": ts(now - timedelta(minutes=30)),
     "description": "Pedido feito por Janine Marjoub.", "actor": "customer"},
    {"event_id": "EVT_016", "order_id": "ORD_008", "event_type": "picked_up",
     "timestamp": ts(now - timedelta(minutes=8)),
     "description": "Carlos Eduardo pegou o pedido no Espetinho do Magrão.", "actor": "driver"},
    {"event_id": "EVT_017", "order_id": "ORD_008", "event_type": "en_route",
     "timestamp": ts(now - timedelta(minutes=5)),
     "description": "Em rota. Trânsito tranquilo.", "actor": "driver"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  PAYMENTS — um por pedido, breakdown em BRL
# ═══════════════════════════════════════════════════════════════════════════

PAYMENTS = [
    # ORD_001 — Gabriel (Plus: entrega grátis > R$ 25)
    {"payment_id": "PAY_001", "order_id": "ORD_001", "customer_id": DEMO_USER_ID,
     "subtotal": 84.00, "delivery_fee": 0.00, "service_fee": 3.90, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 87.90, "payment_method": "visa_4242", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    # ORD_002 — Gabriel (Plus)
    {"payment_id": "PAY_002", "order_id": "ORD_002", "customer_id": DEMO_USER_ID,
     "subtotal": 61.00, "delivery_fee": 0.00, "service_fee": 4.00, "tax": 0.00, "tip": 3.50,
     "discount": 0.00, "total_charged": 68.50, "payment_method": "pix", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    # ORD_003 — Gabriel (Plus) — milkshake faltou
    {"payment_id": "PAY_003", "order_id": "ORD_003", "customer_id": DEMO_USER_ID,
     "subtotal": 50.00, "delivery_fee": 0.00, "service_fee": 4.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 54.00, "payment_method": "visa_4242", "promo_code": None,
     "refund_amount": 13.00, "refund_status": "completed",
     "refund_reason": "Item faltante (Milkshake Ovomaltine) — TKT_001"},

    # ORD_004 — Gabriel (Plus)
    {"payment_id": "PAY_004", "order_id": "ORD_004", "customer_id": DEMO_USER_ID,
     "subtotal": 32.00, "delivery_fee": 0.00, "service_fee": 0.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 32.00, "payment_method": "pix", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    # ORD_005 — Janine (Premium)
    {"payment_id": "PAY_005", "order_id": "ORD_005", "customer_id": "CUST_002",
     "subtotal": 145.00, "delivery_fee": 0.00, "service_fee": 0.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 145.00, "payment_method": "mastercard_8888",
     "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    # ORD_006 — Diego (sem tier, cobra delivery)
    {"payment_id": "PAY_006", "order_id": "ORD_006", "customer_id": "CUST_003",
     "subtotal": 68.90, "delivery_fee": 7.00, "service_fee": 3.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 78.90, "payment_method": "picpay", "promo_code": "BEMVINDO10",
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    # ORD_007 — Gabriella, cancelado — refund integral
    {"payment_id": "PAY_007", "order_id": "ORD_007", "customer_id": "CUST_004",
     "subtotal": 28.00, "delivery_fee": 6.90, "service_fee": 0.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 34.90, "payment_method": "visa_5678", "promo_code": None,
     "refund_amount": 34.90, "refund_status": "completed",
     "refund_reason": "Pedido cancelado antes do preparo iniciar"},

    # ORD_008 — Janine (Premium)
    {"payment_id": "PAY_008", "order_id": "ORD_008", "customer_id": "CUST_002",
     "subtotal": 42.00, "delivery_fee": 0.00, "service_fee": 0.00, "tax": 0.00, "tip": 0.00,
     "discount": 0.00, "total_charged": 42.00, "payment_method": "apple_pay", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},
]


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS — chamados anteriores
# ═══════════════════════════════════════════════════════════════════════════

SUPPORT_TICKETS = [
    {
        "ticket_id": "TKT_001", "customer_id": DEMO_USER_ID, "order_id": "ORD_003",
        "category": "missing_item", "status": "resolved",
        "created_at": ts(now - timedelta(days=5, hours=1)),
        "resolved_at": ts(now - timedelta(days=5)),
        "summary": "Faltou o Milkshake Ovomaltine no meu pedido da Hamburgueria Vira-Lata.",
        "resolution": "Reembolso de R$ 13,00 processado na forma de pagamento original (Visa final 4242).",
    },
    {
        "ticket_id": "TKT_002", "customer_id": "CUST_004", "order_id": "ORD_007",
        "category": "billing", "status": "resolved",
        "created_at": ts(now - timedelta(days=1, hours=2)),
        "resolved_at": ts(now - timedelta(days=1)),
        "summary": "Fui cobrado pelo pedido cancelado.",
        "resolution": "Reembolso integral de R$ 34,90 processado em 2 dias úteis.",
    },
    {
        "ticket_id": "TKT_003", "customer_id": "CUST_003", "order_id": "ORD_006",
        "category": "late_delivery", "status": "closed",
        "created_at": ts(now - timedelta(days=3)),
        "resolved_at": ts(now - timedelta(days=3) + timedelta(hours=1)),
        "summary": "Entrega atrasou 8 minutos do horário previsto.",
        "resolution": "Atraso inferior a 15min. Sem crédito aplicado conforme Política de Atraso de Entrega.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (9) — embedding gerado em runtime
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "Política de Atraso de Entrega — Voucher de Cortesia", "category": "delivery",
        "content": (
            "Se seu pedido chegar com mais de 15 minutos de atraso em relação ao horário estimado, "
            "você tem direito a um voucher de cortesia automático pra usar no próximo pedido. "
            "Os valores são em reais e variam de acordo com o tempo de atraso real:\n\n"
            "- Atraso de 15 a 29 minutos: voucher de R$ 10\n"
            "- Atraso de 30 a 44 minutos: voucher de R$ 20\n"
            "- Atraso de 45 a 59 minutos: voucher de R$ 50\n"
            "- Atraso de 60 minutos ou mais: voucher de R$ 100\n\n"
            "O voucher é aplicado automaticamente na conta em até 24h e tem validade de 30 dias. "
            "Em situações de força maior em vias públicas (carreatas, manifestações, comemorações "
            "esportivas de grande porte como Copa do Mundo), o Redis Eats pode adicionar um bônus extra "
            "por boa vontade — consulte a Política de Eventos de Força Maior em Vias Públicas."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Política de Reembolso", "category": "refund",
        "content": (
            "Reembolsos estão disponíveis pra pedidos que chegam com itens faltando, errados ou "
            "com problemas de qualidade. Solicitações de reembolso devem ser enviadas em até 24h "
            "após a entrega. Pode ser solicitada foto pra reclamações de qualidade. Reembolsos "
            "são processados em 3 a 5 dias úteis na forma de pagamento original."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Política de Cancelamento", "category": "cancellation",
        "content": (
            "Pedidos podem ser cancelados sem custo até 2 minutos após serem feitos. Depois que "
            "o restaurante começa o preparo, pode ser cobrada taxa de cancelamento de até 30% "
            "do valor do pedido. Pedidos já retirados pelo motoboy não podem ser cancelados."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Rastreamento e ETA da Entrega", "category": "delivery",
        "content": (
            "Os tempos estimados de entrega são calculados com base no preparo do restaurante, "
            "disponibilidade de motoboys e distância. ETAs podem mudar em função de alta demanda, "
            "clima ou trânsito. Você acompanha o pedido em tempo real. Se o ETA mudar mais de "
            "10 minutos, você recebe notificação."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Suspensão de Conta", "category": "general",
        "content": (
            "Contas podem ser suspensas por violações repetidas da política, pedidos fraudulentos "
            "de reembolso, ou comportamento abusivo com motoboys ou restaurantes. Contas suspensas "
            "não conseguem fazer novos pedidos. Pra contestar uma suspensão, contate o atendimento "
            "com seus dados de conta."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Plano Plus e Premium (Benefícios)", "category": "general",
        "content": (
            "Membros Plus têm taxa de entrega grátis em pedidos acima de R$ 25 e 5% de cashback. "
            "Membros Premium têm taxa de entrega grátis em todos os pedidos, 10% de cashback, "
            "prioridade na designação de motoboys e atendimento prioritário. Os benefícios "
            "renovam mensalmente."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Compensação por Atraso do Motoboy", "category": "delivery",
        "content": (
            "Quando o atraso é causado por problemas do lado do motoboy (problema mecânico, "
            "erro de navegação, múltiplos pedidos), o Redis Eats aplica crédito automaticamente. "
            "Tabela: 10-20 min de atraso = 10% de crédito, 20-30 min = 20% de crédito, "
            "30+ min = elegível pra reembolso integral. Membros Premium recebem 1,5x o crédito padrão."
        ),
    },
    {
        "policy_id": "POL_008", "title": "Segurança Alimentar", "category": "general",
        "content": (
            "Todos os restaurantes parceiros precisam cumprir as normas locais de saúde e segurança. "
            "Se você receber comida que pareça estragada ou insegura, não consuma. Reporte o problema "
            "imediatamente pra reembolso integral e investigação."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Eventos de Força Maior em Vias Públicas", "category": "delivery",
        "content": (
            "Em datas com eventos significativos em vias públicas (carreatas, buzinaços, "
            "manifestações ou comemorações esportivas de larga escala — Copa do Mundo, "
            "finais de Libertadores e afins), o sistema de ETA pode apresentar variações relevantes. "
            "Atrasos comprovadamente decorrentes desses eventos são reconhecidos pelo Redis Eats, "
            "e o crédito proporcional é aplicado automaticamente conforme a Política de Atraso de Entrega. "
            "Em alguns casos a Redis Eats pode aplicar bônus adicional 'a título de boa vontade' — "
            "fique de olho na próxima fatura."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — gera embeddings + escreve arquivos JSONL
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} registros")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={safe_value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    print("Gerando embeddings das políticas...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Escrevendo arquivos JSONL:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "restaurants.jsonl", RESTAURANTS)
    write_jsonl(resolved_output_dir, "drivers.jsonl", DRIVERS)
    write_jsonl(resolved_output_dir, "orders.jsonl", ORDERS)
    write_jsonl(resolved_output_dir, "order_items.jsonl", ORDER_ITEMS)
    write_jsonl(resolved_output_dir, "delivery_events.jsonl", DELIVERY_EVENTS)
    write_jsonl(resolved_output_dir, "payments.jsonl", PAYMENTS)
    write_jsonl(resolved_output_dir, "support_tickets.jsonl", SUPPORT_TICKETS)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['name']} ({demo['customer_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["customer_id"],
            "DEMO_USER_NAME": demo["name"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "customers": len(CUSTOMERS),
            "restaurants": len(RESTAURANTS),
            "drivers": len(DRIVERS),
            "orders": len(ORDERS),
            "order_items": len(ORDER_ITEMS),
            "delivery_events": len(DELIVERY_EVENTS),
            "payments": len(PAYMENTS),
            "support_tickets": len(SUPPORT_TICKETS),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
