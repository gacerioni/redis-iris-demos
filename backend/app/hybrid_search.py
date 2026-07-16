"""StrideLane shared hybrid-search engine.

ONE function powers both surfaces: the storefront /api/search endpoint and the
concierge's search_products_semantic tool. Identical embedding model, index, and
weights, so the browsable catalog and the conversational answer never drift.

Retrieval runs in Redis as a single FT.AGGREGATE over a backend-owned product index
(setup_index.py) that fuses vector + geo + text + tag + numeric in one index, since
the Context Surfaces SDK cannot index GEO:

    (<hard facet filters>)=>[KNN <over> @search_vector $BLOB AS vec_dist]
    APPLY geodistance(...) AS dist_m        # when a shopper location is known
    LOAD <fields + name + search_text + vec_dist>
    SORTBY vec_dist ASC  LIMIT 0 <over>  PARAMS 2 BLOB <blob>  DIALECT 2

Redis does the expensive part (filtered vector KNN + geo distance). The weighted
fusion (vector + geo + rating + lexical text overlap) is computed in the app so the
four signals are explicit, the weight sliders re-rank instantly without re-querying,
and the score breakdown is honest. Facets are hard filters; the semantic signal comes
from the vector, so a product with zero keyword overlap still surfaces.
"""

from __future__ import annotations

import re
import struct
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI

from backend.app.redis_connection import create_async_redis_client
from backend.app.settings import Settings

PRODUCT_INDEX = "stridelane_product_idx"
STORE_INDEX = "stridelane_store_idx"

DEFAULT_WEIGHTS = {"text": 0.40, "vector": 0.35, "geo": 0.15, "rating": 0.10}
KNN_OVERFETCH = 80            # over-fetch before the weighted re-rank

_LOAD_FIELDS = [
    "product_id", "name", "search_text", "brand", "category", "subcategory", "gender",
    "color", "use_case", "price", "sale_price", "rating", "review_count", "stock",
    "in_stock", "availability_status", "primary_store_id", "store_geo", "fit_summary",
]

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "the", "to", "for", "of", "on", "in", "with", "and", "or", "my", "me",
    "i", "you", "is", "are", "something", "some", "any", "that", "this", "it", "want",
    "need", "looking", "show", "find", "get", "give", "good", "best", "please", "can",
}


def _pack_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if len(t) > 1}


def _content_tokens(text: str) -> set[str]:
    return _tokens(text)


def _query_tokens(query: str) -> set[str]:
    return {t for t in _tokens(query) if t not in _STOPWORDS}


def _text_overlap(query_tokens: set[str], content: str) -> float:
    """Fraction of meaningful query terms present in the product text (0..1)."""
    if not query_tokens:
        return 0.0
    ctoks = _content_tokens(content)
    hit = sum(1 for t in query_tokens if t in ctoks)
    return hit / len(query_tokens)


def _esc_tag(value: str) -> str:
    """Escape a TAG value so spaces and punctuation match a single stored tag."""
    out = []
    for ch in str(value).strip():
        if not ch.isalnum():
            out.append("\\")
        out.append(ch)
    return "".join(out)


def _tag_clause(field: str, values: list[str]) -> str:
    safe = [_esc_tag(v) for v in values if str(v).strip()]
    return f"@{field}:{{{'|'.join(safe)}}}" if safe else ""


def _build_filter_prefix(filters: dict[str, Any] | None) -> str:
    filters = filters or {}
    clauses: list[str] = []
    for field in ("brand", "category", "subcategory", "gender", "color", "use_case"):
        if filters.get(field):
            c = _tag_clause(field, filters[field])
            if c:
                clauses.append(c)
    if filters.get("max_price") is not None:
        clauses.append(f"@price:[-inf {float(filters['max_price'])}]")
    if filters.get("min_price") is not None:
        clauses.append(f"@price:[{float(filters['min_price'])} +inf]")
    if filters.get("min_rating") is not None:
        clauses.append(f"@rating:[{float(filters['min_rating'])} +inf]")
    if filters.get("in_stock_only"):
        clauses.append("@stock:[1 +inf]")
    return " ".join(clauses).strip() or "*"


def _parse_aggregate(reply: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in reply[1:]:
        if not isinstance(row, (list, tuple)):
            continue
        rows.append({row[i]: row[i + 1] for i in range(0, len(row) - 1, 2)})
    return rows


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def embed_query(query: str, settings: Settings) -> list[float]:
    client_kw: dict[str, Any] = {"api_key": settings.openai_api_key}
    if getattr(settings, "openai_base_url", None):
        client_kw["base_url"] = settings.openai_base_url
    resp = await AsyncOpenAI(**client_kw).embeddings.create(input=[query], model=settings.openai_embedding_model)
    return resp.data[0].embedding


async def hybrid_product_search(
    *,
    query: str,
    settings: Settings,
    filters: dict[str, Any] | None = None,
    k: int = 12,
    user_location: str | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    has_geo = bool(user_location)
    if not has_geo:
        total = w["text"] + w["vector"] + w["rating"] or 1.0
        w = {"text": w["text"] / total, "vector": w["vector"] / total, "geo": 0.0, "rating": w["rating"] / total}

    t0 = perf_counter()
    vector = await embed_query(query, settings)
    embed_ms = round((perf_counter() - t0) * 1000, 1)

    filter_prefix = _build_filter_prefix(filters)
    knn = f"({filter_prefix})=>[KNN {KNN_OVERFETCH} @search_vector $BLOB AS vec_dist]"

    args: list[Any] = ["FT.AGGREGATE", PRODUCT_INDEX, knn,
                       "LOAD", str(len(_LOAD_FIELDS) + 1), "@vec_dist", *[f"@{f}" for f in _LOAD_FIELDS]]
    if has_geo:
        lon_s, lat_s = user_location.split(",", 1)
        lon, lat = float(lon_s), float(lat_s)
        args += ["APPLY", f"geodistance(@store_geo, {lon:.6f}, {lat:.6f})", "AS", "dist_m"]
    args += ["SORTBY", "2", "@vec_dist", "ASC", "LIMIT", "0", str(KNN_OVERFETCH),
             "PARAMS", "2", "BLOB", _pack_vector(vector), "DIALECT", "2"]

    client = create_async_redis_client(settings)
    t1 = perf_counter()
    reply = await client.execute_command(*args)
    search_ms = round((perf_counter() - t1) * 1000, 1)

    candidates = int(reply[0]) if reply else 0
    rows = _parse_aggregate(reply)

    q_tokens = _query_tokens(query)
    scored: list[dict[str, Any]] = []
    for r in rows:
        vec_dist = _num(r.get("vec_dist"), 2.0)
        sim_vec = 1.0 / (1.0 + vec_dist)
        rating_norm = _num(r.get("rating")) / 5.0
        text_norm = _text_overlap(q_tokens, f"{r.get('name', '')} {r.get('search_text', '')}")
        geo_norm = 0.0
        dist_km = None
        if has_geo:
            dist_m = _num(r.get("dist_m"), 1e12)
            geo_norm = 1.0 / (1.0 + dist_m / 1000.0)
            dist_km = round(dist_m / 1000.0, 1)
        hybrid = (w["text"] * text_norm + w["vector"] * sim_vec + w["geo"] * geo_norm + w["rating"] * rating_norm)
        scored.append({
            "product_id": r.get("product_id"),
            "name": r.get("name"),
            "brand": r.get("brand"),
            "category": r.get("category"),
            "subcategory": r.get("subcategory"),
            "gender": r.get("gender"),
            "color": r.get("color"),
            "use_case": r.get("use_case"),
            "price": _num(r.get("price")),
            "sale_price": _num(r.get("sale_price")) or None,
            "rating": _num(r.get("rating")),
            "review_count": int(_num(r.get("review_count"))),
            "stock": int(_num(r.get("stock"))),
            "in_stock": str(r.get("in_stock", "")).lower() in {"1", "true", "yes"},
            "availability_status": r.get("availability_status"),
            "primary_store_id": r.get("primary_store_id"),
            "fit_summary": r.get("fit_summary"),
            "distance_km": dist_km,
            "hybrid_score": round(hybrid, 4),
            "score_breakdown": {
                "text": round(w["text"] * text_norm, 4),
                "vector": round(w["vector"] * sim_vec, 4),
                "geo": round(w["geo"] * geo_norm, 4),
                "rating": round(w["rating"] * rating_norm, 4),
                "vector_distance": round(vec_dist, 4),
            },
        })

    scored.sort(key=lambda x: (x["hybrid_score"], x["rating"]), reverse=True)
    results = scored[:k]

    return {
        "query": query,
        "results": results,
        "metrics": {
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "candidates_scanned": candidates,
            "reranked": len(scored),
            "returned": len(results),
            "weights": {kk: round(vv, 3) for kk, vv in w.items()},
            "geo_applied": has_geo,
            "filter_prefix": filter_prefix,
        },
    }


async def facet_counts(
    *, settings: Settings, filters: dict[str, Any] | None = None,
    fields: tuple[str, ...] = ("category", "brand", "color", "gender"),
) -> dict[str, list[dict[str, Any]]]:
    """Counts per value for each facet field, scoped to the active hard filters."""
    prefix = _build_filter_prefix(filters)
    client = create_async_redis_client(settings)
    out: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        try:
            reply = await client.execute_command(
                "FT.AGGREGATE", PRODUCT_INDEX, prefix,
                "GROUPBY", "1", f"@{field}", "REDUCE", "COUNT", "0", "AS", "count",
                "SORTBY", "2", "@count", "DESC", "LIMIT", "0", "40", "DIALECT", "2",
            )
        except Exception:  # noqa: BLE001
            out[field] = []
            continue
        rows = _parse_aggregate(reply)
        out[field] = [{"value": r.get(field), "count": int(_num(r.get("count")))}
                      for r in rows if r.get(field)]
    return out


async def geo_stores_near(
    *, lon: float, lat: float, radius_km: float, settings: Settings, limit: int = 5
) -> list[dict[str, Any]]:
    args = [
        "FT.AGGREGATE", STORE_INDEX, f"@location:[{lon} {lat} {radius_km} km]",
        "LOAD", "5", "@store_id", "@name", "@store_type", "@city", "@location",
        "APPLY", f"geodistance(@location, {lon}, {lat})", "AS", "dist_m",
        "SORTBY", "2", "@dist_m", "ASC", "LIMIT", "0", str(limit), "DIALECT", "2",
    ]
    client = create_async_redis_client(settings)
    reply = await client.execute_command(*args)
    return [{
        "store_id": r.get("store_id"), "name": r.get("name"), "store_type": r.get("store_type"),
        "city": r.get("city"), "distance_km": round(_num(r.get("dist_m")) / 1000.0, 1),
    } for r in _parse_aggregate(reply)]
