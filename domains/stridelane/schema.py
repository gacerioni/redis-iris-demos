"""StrideLane entity schema (single source of truth).

StrideLane is a brandless, global sporting-goods / footwear / fashion storefront,
built to showcase Redis hybrid search (BM25 text + vector + geo + rating) plus a
conversational concierge. Greenfield domain, learns from electrohub.

Design notes that the rest of the code depends on:
  * Vector fields (Product.search_vector, Policy.content_embedding) are 1536-d cosine.
    They are NEVER exposed to auto-generated tools: the LLM cannot pass a raw vector,
    so semantic search runs through the server-side-embedding engine (hybrid_search.py).
  * Geo: the Context Surfaces SDK cannot index a GEO field, so store_geo / location are
    PLAIN (index=None) here. A backend-owned FT.CREATE (setup_index.py) adds the GEO +
    vector + text + numeric index used by the hybrid engine. The SDK still indexes the
    text/tag/numeric/vector fields for the auto-generated filter tools.
  * Recency sort uses *_epoch ints (numeric, sortable). ISO-string timestamps are NOT
    sortable through the SDK, so never sort by a str date.
  * Every id / FK / SKU stays str: tag-on-numeric is a hard validate_entity_specs error.
  * Color and size are split onto Variant rows; multi-value TAGs on a single Product
    would depend on the SDK default separator, so we avoid them.
"""

from __future__ import annotations

from backend.app.core.domain_schema import (
    EntitySpec,
    FieldSpec,
    RelationshipSpec,
)


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    EntitySpec(
        class_name="Product",
        redis_key_template="stridelane_product:{product_id}",
        file_name="products.jsonl",
        id_field="product_id",
        fields=(
            FieldSpec("product_id", "str", "Unique product identifier", is_key_component=True),
            FieldSpec("sku", "str", "Retail SKU", index="tag", no_stem=True),
            FieldSpec("name", "str", "Product name", index="text", weight=2.4),
            FieldSpec("brand", "str", "House brand", index="tag"),
            FieldSpec("category", "str", "Top-level category", index="tag"),
            FieldSpec("subcategory", "str", "Subcategory such as road, trail, sneakers", index="tag"),
            FieldSpec("gender", "str", "Target gender: men, women, unisex, kids", index="tag"),
            FieldSpec("color", "str", "Primary color (full color set lives on variants)", index="tag"),
            FieldSpec("use_case", "str", "Primary use case: road, trail, gym, football, hike, casual", index="tag"),
            FieldSpec("price", "float", "Current selling price in BRL", index="numeric", sortable=True),
            FieldSpec("sale_price", "float | None", "Promotional price in BRL", index="numeric"),
            FieldSpec("rating", "float", "Average customer rating 0 to 5", index="numeric", sortable=True),
            FieldSpec("review_count", "int", "Number of customer reviews", index="numeric", sortable=True),
            FieldSpec("stock", "int", "Units available across stores", index="numeric", sortable=True),
            FieldSpec("in_stock", "bool", "Whether the product is currently in stock"),
            FieldSpec("availability_status", "str", "Availability status", index="tag"),
            FieldSpec("pickup_eligible", "bool", "Whether local store pickup is available"),
            FieldSpec("shipping_eligible", "bool", "Whether shipping is available"),
            FieldSpec("specs_summary", "str", "Readable spec and material summary", index="text"),
            FieldSpec("search_text", "str", "Combined searchable description for discovery", index="text", weight=1.8),
            FieldSpec("fit_summary", "str", "Short fit and use summary", index="text", weight=1.4),
            FieldSpec("primary_store_id", "str", "Nearest fulfilling store for geo ranking", index="tag"),
            FieldSpec("store_geo", "str", "Fulfilling store coordinate as 'lon,lat' (backend GEO index only)"),
            FieldSpec("updated_at_epoch", "int", "Catalog update time, epoch seconds, for recency sort", index="numeric", sortable=True),
            FieldSpec(
                "search_vector",
                "list[float]",
                "Vector embedding of name + description for semantic search",
                index="vector",
                vector_dim=1536,
                distance_metric="cosine",
            ),
        ),
        relationships=(
            RelationshipSpec("variants", "Size and color variants for this product", "product_id", "list[Variant]"),
            RelationshipSpec("store", "Nearest fulfilling store", "primary_store_id", "Store"),
        ),
    ),
    EntitySpec(
        class_name="Variant",
        redis_key_template="stridelane_variant:{variant_id}",
        file_name="variants.jsonl",
        id_field="variant_id",
        fields=(
            FieldSpec("variant_id", "str", "Unique variant identifier", is_key_component=True),
            FieldSpec("product_id", "str", "Parent product identifier", index="tag"),
            FieldSpec("product_name", "str", "Parent product name", index="text"),
            FieldSpec("sku", "str", "Variant SKU", index="tag", no_stem=True),
            FieldSpec("size", "str", "Size label", index="tag"),
            FieldSpec("size_system", "str", "Size system: EU, US, BR, alpha", index="tag"),
            FieldSpec("color", "str", "Variant color", index="tag"),
            FieldSpec("price", "float", "Variant price in BRL", index="numeric", sortable=True),
            FieldSpec("stock", "int", "Units available for this variant", index="numeric", sortable=True),
        ),
        relationships=(
            RelationshipSpec("product", "Parent product", "product_id", "Product"),
        ),
    ),
    EntitySpec(
        class_name="Store",
        redis_key_template="stridelane_store:{store_id}",
        file_name="stores.jsonl",
        id_field="store_id",
        fields=(
            FieldSpec("store_id", "str", "Unique store identifier", is_key_component=True),
            FieldSpec("name", "str", "Store name", index="text", weight=2.0),
            FieldSpec("store_type", "str", "store, flagship or distribution_center", index="tag"),
            FieldSpec("city", "str", "Store city", index="tag"),
            FieldSpec("state", "str", "Store state", index="tag"),
            FieldSpec("address", "str", "Street address"),
            FieldSpec("lat", "float", "Latitude (plain, SDK has no geo index)"),
            FieldSpec("lon", "float", "Longitude (plain, SDK has no geo index)"),
            FieldSpec("location", "str", "Coordinate as 'lon,lat' for the backend GEO index"),
            FieldSpec("pickup_supported", "bool", "Whether in-store pickup is supported"),
            FieldSpec("hours_summary", "str", "Store operating hours"),
        ),
    ),
    EntitySpec(
        class_name="Policy",
        redis_key_template="stridelane_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Unique policy identifier", is_key_component=True),
            FieldSpec("title", "str", "Policy title", index="text", weight=2.0),
            FieldSpec("category", "str", "Policy category: shipping, returns, warranty, membership", index="tag"),
            FieldSpec("content", "str", "Policy body", index="text"),
            FieldSpec(
                "content_embedding",
                "list[float]",
                "Vector embedding for the policy content (RAG)",
                index="vector",
                vector_dim=1536,
                distance_metric="cosine",
            ),
        ),
    ),
    EntitySpec(
        class_name="Customer",
        redis_key_template="stridelane_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Unique customer identifier", is_key_component=True),
            FieldSpec("name", "str", "Customer full name", index="text", weight=2.0),
            FieldSpec("email", "str", "Customer email", index="text", no_stem=True),
            FieldSpec("city", "str", "Customer city", index="tag"),
            FieldSpec("state", "str", "Customer state", index="tag"),
            FieldSpec("member_tier", "str", "Loyalty tier: standard, plus, elite", index="tag"),
            FieldSpec("home_store_id", "str", "Preferred local store", index="tag"),
            FieldSpec("home_store_name", "str", "Preferred store name", index="text"),
            FieldSpec("home_geo", "str", "Customer location as 'lon,lat' for default geo ranking"),
            FieldSpec("account_created_at", "str", "ISO timestamp for account creation"),
        ),
    ),
    EntitySpec(
        class_name="FeatureRow",
        redis_key_template="stridelane_feature:{customer_id}",
        file_name="features.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Customer identifier (one online feature row per customer)", is_key_component=True),
            FieldSpec("pref_category", "str", "Top category affinity", index="tag"),
            FieldSpec("pref_subcategory", "str", "Top subcategory affinity", index="tag"),
            FieldSpec("pref_use_case", "str", "Preferred use case", index="tag"),
            FieldSpec("pref_color", "str", "Preferred color", index="tag"),
            FieldSpec("size_pref", "str", "Preferred size label"),
            FieldSpec("price_band_min", "float", "Lower bound of typical spend, BRL", index="numeric"),
            FieldSpec("price_band_max", "float", "Upper bound of typical spend, BRL", index="numeric"),
            FieldSpec("propensity_running", "float", "Affinity 0-1 for running gear", index="numeric"),
            FieldSpec("propensity_outdoor", "float", "Affinity 0-1 for outdoor gear", index="numeric"),
            FieldSpec("propensity_lifestyle", "float", "Affinity 0-1 for lifestyle sneakers", index="numeric"),
            FieldSpec("recently_viewed", "list[str]", "Recently viewed product ids"),
            FieldSpec("updated_at_epoch", "int", "Feature row update time, epoch seconds", index="numeric", sortable=True),
            FieldSpec(
                "interest_centroid",
                "list[float]",
                "Centroid embedding of recently viewed products, for KNN recommendation expansion",
                index=None,
                vector_dim=1536,
                distance_metric="cosine",
            ),
        ),
    ),
)
