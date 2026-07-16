"""StrideLane cart + session service (RedisJSON, additive, namespaced).

The cart is a RedisJSON document keyed by customer (one cart per shopper), mutated by
deterministic tools so the LLM never does arithmetic. Totals are always recomputed
server-side. The session document (recent searches + last result ids) is keyed by
session id and powers the storefront-to-concierge handoff.

Keys (never collide with EntitySpec catalog keys or other demos):
  stridelane:cart:{customer_id}
  stridelane:session:{session_id}
Both expire after 24h, refreshed on every write. No DB flush, ever.
"""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from backend.app.redis_connection import create_async_redis_client
from backend.app.settings import Settings

CART_TTL_S = 86_400
SESSION_TTL_S = 86_400
MAX_QTY_PER_LINE = 10

# small brandless coupon registry (demo)
_COUPONS: dict[str, dict[str, Any]] = {
    "WELCOME10": {"type": "percent", "value": 10, "min_subtotal": 0, "label": "10% off your order"},
    "RUN20": {"type": "percent", "value": 20, "min_subtotal": 500, "label": "20% off orders above R$ 500"},
    "STRIDE50": {"type": "amount", "value": 50, "min_subtotal": 300, "label": "R$ 50 off orders above R$ 300"},
}


def _cart_key(customer_id: str) -> str:
    return f"stridelane:cart:{customer_id}"


def _session_key(session_id: str) -> str:
    return f"stridelane:session:{session_id}"


def _empty_cart(customer_id: str) -> dict[str, Any]:
    return {
        "cart_id": customer_id, "customer_id": customer_id, "currency": "BRL",
        "items": [], "coupon": None,
        "subtotal": 0.0, "discount_total": 0.0, "total": 0.0, "item_count": 0,
    }


def _recompute(cart: dict[str, Any]) -> dict[str, Any]:
    subtotal = 0.0
    item_count = 0
    for it in cart.get("items", []):
        it["line_total"] = round(float(it["unit_price"]) * int(it["quantity"]), 2)
        subtotal += it["line_total"]
        item_count += int(it["quantity"])
    discount = 0.0
    coupon = cart.get("coupon")
    if coupon and subtotal >= float(coupon.get("min_subtotal", 0)):
        if coupon["type"] == "percent":
            discount = round(subtotal * float(coupon["value"]) / 100.0, 2)
        elif coupon["type"] == "amount":
            discount = min(round(float(coupon["value"]), 2), subtotal)
    cart["subtotal"] = round(subtotal, 2)
    cart["discount_total"] = round(discount, 2)
    cart["total"] = round(subtotal - discount, 2)
    cart["item_count"] = item_count
    return cart


async def _get_cart(client, customer_id: str) -> dict[str, Any]:
    raw = await client.execute_command("JSON.GET", _cart_key(customer_id))
    if not raw:
        return _empty_cart(customer_id)
    raw = raw.decode() if isinstance(raw, bytes) else raw
    data = json.loads(raw)
    if isinstance(data, list):
        data = data[0] if data else None
    return data or _empty_cart(customer_id)


async def _save_cart(client, customer_id: str, cart: dict[str, Any]) -> None:
    _recompute(cart)
    await client.execute_command("JSON.SET", _cart_key(customer_id), "$", json.dumps(cart, ensure_ascii=False))
    await client.expire(_cart_key(customer_id), CART_TTL_S)


async def _get_product(client, product_id: str) -> dict[str, Any] | None:
    raw = await client.execute_command("JSON.GET", f"stridelane_product:{product_id}")
    if not raw:
        return None
    raw = raw.decode() if isinstance(raw, bytes) else raw
    data = json.loads(raw)
    if isinstance(data, list):
        data = data[0] if data else None
    return data


# ── cart tools ──────────────────────────────────────────────────────────────
async def view_cart(settings: Settings, customer_id: str) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    cart = await _get_cart(client, customer_id)
    await client.expire(_cart_key(customer_id), CART_TTL_S)
    return {"success": True, "cart": cart}


async def add_to_cart(settings: Settings, customer_id: str, product_id: str, quantity: int) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    product = await _get_product(client, product_id)
    if not product:
        return {"success": False, "error": f"Product {product_id} not found in the catalog."}
    unit_price = float(product.get("sale_price") or product.get("price") or 0.0)
    cart = await _get_cart(client, customer_id)
    line = next((it for it in cart["items"] if it["product_id"] == product_id), None)
    if line:
        line["quantity"] = min(MAX_QTY_PER_LINE, int(line["quantity"]) + quantity)
    else:
        cart["items"].append({
            "product_id": product_id, "name": product.get("name"),
            "unit_price": round(unit_price, 2), "quantity": min(MAX_QTY_PER_LINE, quantity),
            "line_total": 0.0,
        })
    await _save_cart(client, customer_id, cart)
    return {"success": True, "added": product.get("name"), "cart": cart}


async def update_quantity(settings: Settings, customer_id: str, product_id: str, quantity: int) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    cart = await _get_cart(client, customer_id)
    line = next((it for it in cart["items"] if it["product_id"] == product_id), None)
    if not line:
        return {"success": False, "error": f"{product_id} is not in the cart."}
    if quantity <= 0:
        cart["items"] = [it for it in cart["items"] if it["product_id"] != product_id]
    else:
        line["quantity"] = min(MAX_QTY_PER_LINE, quantity)
    await _save_cart(client, customer_id, cart)
    return {"success": True, "cart": cart}


async def remove_item(settings: Settings, customer_id: str, product_id: str) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    cart = await _get_cart(client, customer_id)
    before = len(cart["items"])
    cart["items"] = [it for it in cart["items"] if it["product_id"] != product_id]
    await _save_cart(client, customer_id, cart)
    return {"success": True, "removed": before - len(cart["items"]), "cart": cart}


async def clear_cart(settings: Settings, customer_id: str, confirm: bool) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    cart = await _get_cart(client, customer_id)
    if not confirm:
        return {"success": True, "needs_confirmation": True,
                "preview": {"item_count": cart["item_count"], "subtotal": cart["subtotal"]},
                "message": "This will remove every item. Confirm to clear."}
    emptied = _empty_cart(customer_id)
    await _save_cart(client, customer_id, emptied)
    return {"success": True, "cleared": True, "cart": emptied}


async def apply_coupon(settings: Settings, customer_id: str, code: str) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    coupon = _COUPONS.get(code.strip().upper())
    cart = await _get_cart(client, customer_id)
    if not coupon:
        return {"success": False, "error": f"Coupon {code} is not valid."}
    if cart["subtotal"] < float(coupon["min_subtotal"]):
        return {"success": False, "error": f"Coupon {code} needs a subtotal of at least R$ {coupon['min_subtotal']:.2f}.",
                "cart": cart}
    cart["coupon"] = {"code": code.strip().upper(), **coupon}
    await _save_cart(client, customer_id, cart)
    return {"success": True, "applied": coupon["label"], "cart": cart}


# ── session (storefront -> concierge handoff) ────────────────────────────────
async def write_session(settings: Settings, session_id: str, *, query: str | None = None,
                        result_ids: list[str] | None = None, result_count: int | None = None,
                        filters: dict[str, Any] | None = None, weights: dict[str, float] | None = None) -> None:
    client = create_async_redis_client(settings)
    raw = await client.execute_command("JSON.GET", _session_key(session_id))
    if raw:
        raw = raw.decode() if isinstance(raw, bytes) else raw
        data = json.loads(raw)
        session = (data[0] if isinstance(data, list) and data else data) or {}
    else:
        session = {"session_id": session_id, "recent_searches": []}
    if query:
        recent = [q for q in session.get("recent_searches", []) if q != query]
        session["recent_searches"] = ([query] + recent)[:5]
        session["last_query"] = query
    if result_ids is not None:
        session["last_result_ids"] = result_ids[:24]
    if result_count is not None:
        session["last_result_count"] = result_count
    if filters is not None:
        session["last_filters"] = filters
    if weights is not None:
        session["last_weights"] = weights
    await client.execute_command("JSON.SET", _session_key(session_id), "$", json.dumps(session, ensure_ascii=False))
    await client.expire(_session_key(session_id), SESSION_TTL_S)


async def read_session(settings: Settings, session_id: str) -> dict[str, Any]:
    client = create_async_redis_client(settings)
    raw = await client.execute_command("JSON.GET", _session_key(session_id))
    if not raw:
        return {"session_id": session_id, "recent_searches": [], "last_query": None}
    raw = raw.decode() if isinstance(raw, bytes) else raw
    data = json.loads(raw)
    return (data[0] if isinstance(data, list) and data else data) or {"session_id": session_id}
