"""StrideLane backend-owned indexes, synonyms, and autocomplete.

Run AFTER the catalog is in Redis. Creates everything the hybrid engine needs that the
Context Surfaces SDK cannot (GEO + a single index fusing vector + geo + text + tag +
numeric), plus retail synonym groups and a typo-tolerant autocomplete dictionary.

Idempotent and additive: only touches stridelane_* keys and stridelane_* indexes, never
flushes the DB, never touches other demos.

Standalone usage (also loads the JSONL into Redis as JSON for the engine to query):
    PYTHONPATH=. uv run python -m domains.stridelane.setup_index
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.redis_connection import create_redis_client
from backend.app.settings import Settings, get_settings

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output" / "stridelane"

PRODUCT_INDEX = "stridelane_product_idx"
STORE_INDEX = "stridelane_store_idx"
SUGGEST_KEY = "autocomplete:stridelane_products"

# entity file -> (key prefix, id field)
_LOAD_MAP = {
    "products.jsonl": ("stridelane_product", "product_id"),
    "variants.jsonl": ("stridelane_variant", "variant_id"),
    "stores.jsonl": ("stridelane_store", "store_id"),
    "policies.jsonl": ("stridelane_policy", "policy_id"),
    "customers.jsonl": ("stridelane_customer", "customer_id"),
    "features.jsonl": ("stridelane_feature", "customer_id"),
}

# single-token synonym groups (multi-word phrases are unreliable in FT.SYNUPDATE)
_SYNONYMS = {
    "footwear_running_en": ["sneaker", "trainer", "runner", "kicks"],
    "footwear_pt": ["tenis", "calcado", "sapatilha"],
    "jacket_outerwear": ["jacket", "windbreaker", "shell", "anorak"],
    "tee_top": ["tee", "tshirt", "shirt", "camiseta", "blusa"],
    "backpack": ["backpack", "daypack", "rucksack", "mochila"],
    "color_teal": ["teal", "petrol", "turquoise", "aqua"],
    "color_maroon": ["maroon", "burgundy", "wine", "vinho"],
    "waterproof": ["waterproof", "rainproof", "impermeavel"],
}

# product index: every field referenced by the hybrid engine's LOAD must be an attribute
_PRODUCT_SCHEMA = [
    "$.product_id", "AS", "product_id", "TAG",
    "$.name", "AS", "name", "TEXT", "WEIGHT", "2.4",
    "$.search_text", "AS", "search_text", "TEXT", "WEIGHT", "1.8",
    "$.specs_summary", "AS", "specs_summary", "TEXT",
    "$.fit_summary", "AS", "fit_summary", "TEXT",
    "$.brand", "AS", "brand", "TAG",
    "$.category", "AS", "category", "TAG",
    "$.subcategory", "AS", "subcategory", "TAG",
    "$.gender", "AS", "gender", "TAG",
    "$.color", "AS", "color", "TAG",
    "$.use_case", "AS", "use_case", "TAG",
    "$.availability_status", "AS", "availability_status", "TAG",
    "$.in_stock", "AS", "in_stock", "TAG",
    "$.primary_store_id", "AS", "primary_store_id", "TAG",
    "$.price", "AS", "price", "NUMERIC", "SORTABLE",
    "$.sale_price", "AS", "sale_price", "NUMERIC",
    "$.rating", "AS", "rating", "NUMERIC", "SORTABLE",
    "$.review_count", "AS", "review_count", "NUMERIC", "SORTABLE",
    "$.stock", "AS", "stock", "NUMERIC", "SORTABLE",
    "$.updated_at_epoch", "AS", "updated_at_epoch", "NUMERIC", "SORTABLE",
    "$.store_geo", "AS", "store_geo", "GEO",
    "$.search_vector", "AS", "search_vector", "VECTOR", "HNSW", "6",
    "TYPE", "FLOAT32", "DIM", "1536", "DISTANCE_METRIC", "COSINE",
]

_STORE_SCHEMA = [
    "$.store_id", "AS", "store_id", "TAG",
    "$.name", "AS", "name", "TEXT",
    "$.store_type", "AS", "store_type", "TAG",
    "$.city", "AS", "city", "TAG",
    "$.state", "AS", "state", "TAG",
    "$.location", "AS", "location", "GEO",
]


def _drop(client, index: str) -> None:
    try:
        client.execute_command("FT.DROPINDEX", index)
    except Exception:  # noqa: BLE001 - index may not exist
        pass


def _create_index(client, index: str, prefix: str, schema: list[str]) -> None:
    _drop(client, index)
    client.execute_command(
        "FT.CREATE", index, "ON", "JSON", "PREFIX", "1", f"{prefix}:", "SCHEMA", *schema
    )
    print(f"  created index {index} over {prefix}:*")


def load_jsonl_to_redis(client, output_dir: Path | None = None) -> dict[str, int]:
    """Load the generated JSONL into Redis as JSON docs (additive, namespaced)."""
    out = output_dir or OUTPUT_DIR
    counts: dict[str, int] = {}
    for filename, (prefix, id_field) in _LOAD_MAP.items():
        path = out / filename
        if not path.exists():
            continue
        n = 0
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            key = f"{prefix}:{doc[id_field]}"
            client.execute_command("JSON.SET", key, "$", json.dumps(doc, ensure_ascii=False))
            n += 1
        counts[prefix] = n
        print(f"  loaded {n} -> {prefix}:*")
    return counts


def setup_synonyms(client) -> None:
    for group_id, terms in _SYNONYMS.items():
        client.execute_command("FT.SYNUPDATE", PRODUCT_INDEX, group_id, *terms)
    print(f"  applied {len(_SYNONYMS)} synonym groups")


def seed_autocomplete(client) -> int:
    """Seed the suggestion dictionary from loaded product names + brands."""
    try:
        client.execute_command("DEL", SUGGEST_KEY)
    except Exception:  # noqa: BLE001
        pass
    seen: set[str] = set()
    n = 0
    for key in client.scan_iter(match="stridelane_product:*", count=300):
        raw = client.execute_command("JSON.GET", key if isinstance(key, str) else key.decode())
        if not raw:
            continue
        raw = raw.decode() if isinstance(raw, bytes) else raw
        doc = json.loads(raw)
        if isinstance(doc, list):
            doc = doc[0] if doc else None
        if not doc:
            continue
        name = (doc.get("name") or "").strip()
        review_count = float(doc.get("review_count") or 1)
        weight = 1.0 + review_count / 1000.0
        for term in (name, doc.get("brand")):
            term = (term or "").strip()
            if term and term.lower() not in seen:
                payload = json.dumps({"product_id": doc.get("product_id")}) if term == name else "{}"
                client.execute_command("FT.SUGADD", SUGGEST_KEY, term, f"{weight:.3f}", "PAYLOAD", payload)
                seen.add(term.lower())
                n += 1
    print(f"  seeded {n} autocomplete suggestions")
    return n


def setup_indexes(settings: Settings, *, load_data: bool = False, output_dir: Path | None = None) -> dict[str, Any]:
    client = create_redis_client(settings)
    result: dict[str, Any] = {}
    if load_data:
        print("Loading JSONL into Redis:")
        result["loaded"] = load_jsonl_to_redis(client, output_dir)
    print("Creating backend indexes:")
    _create_index(client, PRODUCT_INDEX, "stridelane_product", _PRODUCT_SCHEMA)
    _create_index(client, STORE_INDEX, "stridelane_store", _STORE_SCHEMA)
    print("Synonyms:")
    setup_synonyms(client)
    print("Autocomplete:")
    result["suggestions"] = seed_autocomplete(client)
    print("Done.")
    return result


if __name__ == "__main__":
    setup_indexes(get_settings(), load_data=True)
