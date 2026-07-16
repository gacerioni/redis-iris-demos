"""Generated Context Surface models for the StrideLane domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Product(ContextModel):
    """Product entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_product:{product_id}"

    product_id: str = ContextField(
        description="Unique product identifier",
        is_key_component=True,
    )

    sku: str = ContextField(
        description="Retail SKU",
        index="tag",
        no_stem=True,
    )

    name: str = ContextField(
        description="Product name",
        index="text",
        weight=2.4,
    )

    brand: str = ContextField(
        description="House brand",
        index="tag",
    )

    category: str = ContextField(
        description="Top-level category",
        index="tag",
    )

    subcategory: str = ContextField(
        description="Subcategory such as road, trail, sneakers",
        index="tag",
    )

    gender: str = ContextField(
        description="Target gender: men, women, unisex, kids",
        index="tag",
    )

    color: str = ContextField(
        description="Primary color (full color set lives on variants)",
        index="tag",
    )

    use_case: str = ContextField(
        description="Primary use case: road, trail, gym, football, hike, casual",
        index="tag",
    )

    price: float = ContextField(
        description="Current selling price in BRL",
        index="numeric",
        sortable=True,
    )

    sale_price: float | None = ContextField(
        description="Promotional price in BRL",
        index="numeric",
    )

    rating: float = ContextField(
        description="Average customer rating 0 to 5",
        index="numeric",
        sortable=True,
    )

    review_count: int = ContextField(
        description="Number of customer reviews",
        index="numeric",
        sortable=True,
    )

    stock: int = ContextField(
        description="Units available across stores",
        index="numeric",
        sortable=True,
    )

    in_stock: bool = ContextField(
        description="Whether the product is currently in stock",
    )

    availability_status: str = ContextField(
        description="Availability status",
        index="tag",
    )

    pickup_eligible: bool = ContextField(
        description="Whether local store pickup is available",
    )

    shipping_eligible: bool = ContextField(
        description="Whether shipping is available",
    )

    specs_summary: str = ContextField(
        description="Readable spec and material summary",
        index="text",
    )

    search_text: str = ContextField(
        description="Combined searchable description for discovery",
        index="text",
        weight=1.8,
    )

    fit_summary: str = ContextField(
        description="Short fit and use summary",
        index="text",
        weight=1.4,
    )

    primary_store_id: str = ContextField(
        description="Nearest fulfilling store for geo ranking",
        index="tag",
    )

    store_geo: str = ContextField(
        description="Fulfilling store coordinate as 'lon,lat' (backend GEO index only)",
    )

    updated_at_epoch: int = ContextField(
        description="Catalog update time, epoch seconds, for recency sort",
        index="numeric",
        sortable=True,
    )

    search_vector: list[float] = ContextField(
        description="Vector embedding of name + description for semantic search",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )

    variants: Any = ContextRelationship(
        description="Size and color variants for this product",
        target="Variant",
        source_field="product_id",
    )

    store: Any = ContextRelationship(
        description="Nearest fulfilling store",
        target="Store",
        source_field="primary_store_id",
    )


class Variant(ContextModel):
    """Variant entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_variant:{variant_id}"

    variant_id: str = ContextField(
        description="Unique variant identifier",
        is_key_component=True,
    )

    product_id: str = ContextField(
        description="Parent product identifier",
        index="tag",
    )

    product_name: str = ContextField(
        description="Parent product name",
        index="text",
    )

    sku: str = ContextField(
        description="Variant SKU",
        index="tag",
        no_stem=True,
    )

    size: str = ContextField(
        description="Size label",
        index="tag",
    )

    size_system: str = ContextField(
        description="Size system: EU, US, BR, alpha",
        index="tag",
    )

    color: str = ContextField(
        description="Variant color",
        index="tag",
    )

    price: float = ContextField(
        description="Variant price in BRL",
        index="numeric",
        sortable=True,
    )

    stock: int = ContextField(
        description="Units available for this variant",
        index="numeric",
        sortable=True,
    )

    product: Any = ContextRelationship(
        description="Parent product",
        target="Product",
        source_field="product_id",
    )


class Store(ContextModel):
    """Store entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_store:{store_id}"

    store_id: str = ContextField(
        description="Unique store identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Store name",
        index="text",
        weight=2.0,
    )

    store_type: str = ContextField(
        description="store, flagship or distribution_center",
        index="tag",
    )

    city: str = ContextField(
        description="Store city",
        index="tag",
    )

    state: str = ContextField(
        description="Store state",
        index="tag",
    )

    address: str = ContextField(
        description="Street address",
    )

    lat: float = ContextField(
        description="Latitude (plain, SDK has no geo index)",
    )

    lon: float = ContextField(
        description="Longitude (plain, SDK has no geo index)",
    )

    location: str = ContextField(
        description="Coordinate as 'lon,lat' for the backend GEO index",
    )

    pickup_supported: bool = ContextField(
        description="Whether in-store pickup is supported",
    )

    hours_summary: str = ContextField(
        description="Store operating hours",
    )


class Policy(ContextModel):
    """Policy entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_policy:{policy_id}"

    policy_id: str = ContextField(
        description="Unique policy identifier",
        is_key_component=True,
    )

    title: str = ContextField(
        description="Policy title",
        index="text",
        weight=2.0,
    )

    category: str = ContextField(
        description="Policy category: shipping, returns, warranty, membership",
        index="tag",
    )

    content: str = ContextField(
        description="Policy body",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding for the policy content (RAG)",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )


class Customer(ContextModel):
    """Customer entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Unique customer identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Customer full name",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Customer email",
        index="text",
        no_stem=True,
    )

    city: str = ContextField(
        description="Customer city",
        index="tag",
    )

    state: str = ContextField(
        description="Customer state",
        index="tag",
    )

    member_tier: str = ContextField(
        description="Loyalty tier: standard, plus, elite",
        index="tag",
    )

    home_store_id: str = ContextField(
        description="Preferred local store",
        index="tag",
    )

    home_store_name: str = ContextField(
        description="Preferred store name",
        index="text",
    )

    home_geo: str = ContextField(
        description="Customer location as 'lon,lat' for default geo ranking",
    )

    account_created_at: str = ContextField(
        description="ISO timestamp for account creation",
    )


class FeatureRow(ContextModel):
    """FeatureRow entity for the StrideLane domain."""

    __redis_key_template__ = "stridelane_feature:{customer_id}"

    customer_id: str = ContextField(
        description="Customer identifier (one online feature row per customer)",
        is_key_component=True,
    )

    pref_category: str = ContextField(
        description="Top category affinity",
        index="tag",
    )

    pref_subcategory: str = ContextField(
        description="Top subcategory affinity",
        index="tag",
    )

    pref_use_case: str = ContextField(
        description="Preferred use case",
        index="tag",
    )

    pref_color: str = ContextField(
        description="Preferred color",
        index="tag",
    )

    size_pref: str = ContextField(
        description="Preferred size label",
    )

    price_band_min: float = ContextField(
        description="Lower bound of typical spend, BRL",
        index="numeric",
    )

    price_band_max: float = ContextField(
        description="Upper bound of typical spend, BRL",
        index="numeric",
    )

    propensity_running: float = ContextField(
        description="Affinity 0-1 for running gear",
        index="numeric",
    )

    propensity_outdoor: float = ContextField(
        description="Affinity 0-1 for outdoor gear",
        index="numeric",
    )

    propensity_lifestyle: float = ContextField(
        description="Affinity 0-1 for lifestyle sneakers",
        index="numeric",
    )

    recently_viewed: list[str] = ContextField(
        description="Recently viewed product ids",
    )

    updated_at_epoch: int = ContextField(
        description="Feature row update time, epoch seconds",
        index="numeric",
        sortable=True,
    )

    interest_centroid: list[float] = ContextField(
        description="Centroid embedding of recently viewed products, for KNN recommendation expansion",
        vector_dim=1536,
        distance_metric="cosine",
    )
