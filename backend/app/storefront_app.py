"""StrideLane storefront, standalone FastAPI app (port 8060).

Separate process by design (mirrors the token gateway): it never touches the chat
backend, so it cannot affect a running demo. It serves the brandless retail search UX
and calls the shared hybrid engine over the stridelane_* catalog in Redis.

Endpoints:
  GET  /                         the storefront single-page UI
  GET  /api/health               liveness
  GET  /api/config               brands / categories / colors / defaults
  GET  /api/search               hybrid product search (q + facets + weights + geo)
  GET  /api/suggest              FT.SUGGET FUZZY autocomplete
  GET  /api/facets               facet counts for the current filter
  GET  /api/stores_near          nearest stores to the shopper
  GET  /api/cart                 current cart
  POST /api/cart/add|remove|update|clear|coupon   cart mutations
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.app import cart_service
from backend.app.hybrid_search import facet_counts, geo_stores_near, hybrid_product_search
from backend.app.redis_connection import create_async_redis_client
from backend.app.settings import get_settings

settings = get_settings()
_STATIC = Path(__file__).parent / "storefront_static"

CUSTOMER_ID = os.getenv("DEMO_USER_ID", "CUST_DEMO_001")
HOME_GEO = os.getenv("DEMO_USER_HOME_GEO", "-46.6566,-23.5614")
SUGGEST_KEY = "autocomplete:stridelane_products"

app = FastAPI(title="StrideLane Storefront")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _list_arg(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _build_filters(brand, category, color, gender, use_case, max_price, min_rating, in_stock_only) -> dict[str, Any]:
    f: dict[str, Any] = {}
    if brand: f["brand"] = _list_arg(brand)
    if category: f["category"] = _list_arg(category)
    if color: f["color"] = _list_arg(color)
    if gender: f["gender"] = _list_arg(gender)
    if use_case: f["use_case"] = _list_arg(use_case)
    if max_price is not None: f["max_price"] = max_price
    if min_rating is not None: f["min_rating"] = min_rating
    if in_stock_only: f["in_stock_only"] = True
    return f


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "stridelane-storefront", "customer_id": CUSTOMER_ID, "home_geo": HOME_GEO}


@app.get("/api/config")
async def config() -> dict[str, Any]:
    facets = await facet_counts(settings=settings)
    return {
        "currency": "BRL",
        "home_geo": HOME_GEO,
        "default_weights": {"text": 0.40, "vector": 0.35, "geo": 0.15, "rating": 0.10},
        "facets": facets,
    }


@app.get("/api/search")
async def search(
    q: str = "",
    k: int = 12,
    brand: str | None = None,
    category: str | None = None,
    color: str | None = None,
    gender: str | None = None,
    use_case: str | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    in_stock_only: bool = False,
    geo: bool = True,
    w_text: float | None = None,
    w_vector: float | None = None,
    w_geo: float | None = None,
    w_rating: float | None = None,
) -> dict[str, Any]:
    filters = _build_filters(brand, category, color, gender, use_case, max_price, min_rating, in_stock_only)
    weights = None
    if None not in (w_text, w_vector, w_geo, w_rating):
        weights = {"text": w_text, "vector": w_vector, "geo": w_geo, "rating": w_rating}
    if not q.strip():
        # empty query: show a broad popular set (use a generic seed query for the vector)
        q = "popular sporting goods shoes apparel"
    return await hybrid_product_search(
        query=q, settings=settings, filters=filters, k=k,
        user_location=HOME_GEO if geo else None, weights=weights,
    )


@app.get("/api/suggest")
async def suggest(prefix: str = "", max: int = 8) -> dict[str, Any]:
    prefix = prefix.strip()
    if len(prefix) < 2:
        return {"suggestions": []}
    client = create_async_redis_client(settings)
    try:
        raw = await client.execute_command(
            "FT.SUGGET", SUGGEST_KEY, prefix, "FUZZY", "WITHSCORES", "WITHPAYLOADS", "MAX", str(max)
        )
    except Exception:  # noqa: BLE001
        return {"suggestions": []}
    out = []
    i = 0
    while i < len(raw):
        term = raw[i]
        score = raw[i + 1] if i + 1 < len(raw) else None
        payload = raw[i + 2] if i + 2 < len(raw) else None
        pid = None
        if payload:
            try:
                pid = json.loads(payload).get("product_id")
            except Exception:  # noqa: BLE001
                pid = None
        out.append({"text": term, "score": float(score) if score else 0.0, "product_id": pid})
        i += 3
    return {"suggestions": out}


@app.get("/api/facets")
async def facets(
    brand: str | None = None, category: str | None = None, color: str | None = None,
    gender: str | None = None, max_price: float | None = None, min_rating: float | None = None,
    in_stock_only: bool = False,
) -> dict[str, Any]:
    filters = _build_filters(brand, category, color, gender, None, max_price, min_rating, in_stock_only)
    return await facet_counts(settings=settings, filters=filters)


@app.get("/api/stores_near")
async def stores_near(radius_km: float = 50, limit: int = 6) -> dict[str, Any]:
    lon, lat = HOME_GEO.split(",", 1)
    stores = await geo_stores_near(lon=float(lon), lat=float(lat), radius_km=radius_km, settings=settings, limit=limit)
    return {"stores": stores}


@app.get("/api/cart")
async def get_cart() -> dict[str, Any]:
    return await cart_service.view_cart(settings, CUSTOMER_ID)


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


class CouponBody(BaseModel):
    code: str


class ClearBody(BaseModel):
    confirm: bool = True


@app.post("/api/cart/add")
async def cart_add(body: CartItem) -> dict[str, Any]:
    return await cart_service.add_to_cart(settings, CUSTOMER_ID, body.product_id, max(1, body.quantity))


@app.post("/api/cart/update")
async def cart_update(body: CartItem) -> dict[str, Any]:
    return await cart_service.update_quantity(settings, CUSTOMER_ID, body.product_id, body.quantity)


@app.post("/api/cart/remove")
async def cart_remove(body: CartItem) -> dict[str, Any]:
    return await cart_service.remove_item(settings, CUSTOMER_ID, body.product_id)


@app.post("/api/cart/clear")
async def cart_clear(body: ClearBody) -> dict[str, Any]:
    return await cart_service.clear_cart(settings, CUSTOMER_ID, body.confirm)


@app.post("/api/cart/coupon")
async def cart_coupon(body: CouponBody) -> dict[str, Any]:
    return await cart_service.apply_coupon(settings, CUSTOMER_ID, body.code)
