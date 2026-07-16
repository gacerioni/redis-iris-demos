"""Generate the StrideLane synthetic catalog (brandless sporting goods / footwear / fashion).

Builds a lean but convincing catalog to showcase Redis hybrid search:
  * ~220 products across 6 categories, brandless house brands, EN-US copy (no em dash)
  * 7 hand-crafted HERO products, each engineered for one demo beat
    (semantic-only, typo/fuzzy, geo-proximity, find-similar, synonym+color, facet-drilldown, cross-category)
  * variants (size x color), stores with geo (Sao Paulo / Rio cluster + one far CD),
    policy docs for RAG, an online feature row for recommendations, and the demo customer
  * server-side embeddings for Product.search_vector and Policy.content_embedding (1536-d)

Prices are BRL. store_geo is "lon,lat" (longitude FIRST, what Redis GEO expects).
Recency uses updated_at_epoch (int epoch seconds), never an ISO string.
"""

from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "stridelane"

NOW_EPOCH = int(datetime.now(timezone.utc).timestamp())


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    out: list[list[float]] = []
    # batch to stay well under input limits
    for i in range(0, len(texts), 256):
        chunk = texts[i : i + 256]
        resp = client.embeddings.create(
            input=chunk,
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        )
        out.extend(item.embedding for item in resp.data)
    return out


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0] * 1536
    n = len(vectors)
    dim = len(vectors[0])
    acc = [0.0] * dim
    for v in vectors:
        for i in range(dim):
            acc[i] += v[i]
    return [x / n for x in acc]


# ═══════════════════════════════════════════════════════════════════════════
#  STORES — Sao Paulo / Rio cluster + one deliberately far distribution center
#  location is "lon,lat" (longitude FIRST) for the Redis GEO field.
# ═══════════════════════════════════════════════════════════════════════════
def _store(store_id, name, store_type, city, state, address, lon, lat, pickup, hours):
    return {
        "store_id": store_id, "name": name, "store_type": store_type,
        "city": city, "state": state, "address": address,
        "lat": lat, "lon": lon, "location": f"{lon},{lat}",
        "pickup_supported": pickup, "hours_summary": hours,
    }


STORES = [
    _store("STORE_SP_PAULISTA", "StrideLane Paulista Flagship", "flagship", "Sao Paulo", "SP",
           "Av. Paulista 1500", -46.6566, -23.5614, True, "Mon-Sat 10am-10pm, Sun 12pm-8pm"),
    _store("STORE_SP_PINHEIROS", "StrideLane Pinheiros", "store", "Sao Paulo", "SP",
           "Rua dos Pinheiros 800", -46.6920, -23.5670, True, "Mon-Sat 10am-9pm, Sun 12pm-7pm"),
    _store("STORE_SP_MORUMBI", "StrideLane Morumbi Mall", "store", "Sao Paulo", "SP",
           "Av. Roque Petroni 1000", -46.7000, -23.6230, True, "Mon-Sun 10am-10pm"),
    _store("STORE_RJ_COPA", "StrideLane Copacabana", "store", "Rio de Janeiro", "RJ",
           "Av. Nossa Senhora de Copacabana 700", -43.1850, -22.9710, True, "Mon-Sat 10am-9pm, Sun 12pm-7pm"),
    _store("STORE_RJ_BARRA", "StrideLane Barra", "store", "Rio de Janeiro", "RJ",
           "Av. das Americas 4500", -43.3650, -23.0040, True, "Mon-Sun 10am-10pm"),
    _store("STORE_MG_BH", "StrideLane Belo Horizonte", "store", "Belo Horizonte", "MG",
           "Av. do Contorno 6000", -43.9450, -19.9170, True, "Mon-Sat 10am-9pm"),
    _store("STORE_PR_CWB", "StrideLane Curitiba", "store", "Curitiba", "PR",
           "Rua XV de Novembro 300", -49.2730, -25.4290, True, "Mon-Sat 10am-9pm"),
    _store("STORE_SP_CAMPINAS", "StrideLane Campinas", "store", "Campinas", "SP",
           "Av. Norte-Sul 2000", -47.0600, -22.9050, True, "Mon-Sat 10am-9pm"),
    _store("CD_MANAUS", "StrideLane Manaus Distribution Center", "distribution_center", "Manaus", "AM",
           "Distrito Industrial 100", -60.0250, -3.1190, False, "Fulfillment only"),
    _store("CD_RECIFE", "StrideLane Recife Distribution Center", "distribution_center", "Recife", "PE",
           "Av. Recife 5000", -34.8810, -8.0540, False, "Fulfillment only"),
]
_STORE_BY_ID = {s["store_id"]: s for s in STORES}
_RETAIL_STORE_IDS = [s["store_id"] for s in STORES if s["store_type"] != "distribution_center"]


# ═══════════════════════════════════════════════════════════════════════════
#  CATALOG TAXONOMY
# ═══════════════════════════════════════════════════════════════════════════
HOUSE_BRANDS = [
    "Velora", "Northpeak", "Apex Forge", "Strideworks", "Lumen Athletics",
    "Terra Co", "Kinetic Nine", "Halcyon", "Ridgeline Supply", "Solstice Wear", "Boreal", "Crimson Lane",
]

COLORS = ["black", "white", "teal", "coral", "navy", "maroon", "grey", "olive", "royal blue", "vintage white"]
GENDERS = ["men", "women", "unisex", "kids"]

# category -> (subcategories, use_case, brands, price range, size system + sizes, descriptor words)
CATEGORIES = {
    "Running and Training Footwear": {
        "subs": ["road", "trail", "gym"],
        "use_case": "running",
        "brands": ["Velora", "Apex Forge", "Kinetic Nine", "Strideworks", "Northpeak"],
        "price": (399, 1299),
        "size_system": "BR", "sizes": ["37", "38", "39", "40", "41", "42", "43", "44"],
        "words": ["cushioned ride", "lightweight mesh upper", "responsive foam", "breathable knit", "durable rubber outsole"],
    },
    "Lifestyle Sneakers": {
        "subs": ["sneakers", "casual"],
        "use_case": "casual",
        "brands": ["Lumen Athletics", "Halcyon", "Solstice Wear", "Crimson Lane", "Velora"],
        "price": (299, 899),
        "size_system": "BR", "sizes": ["35", "36", "37", "38", "39", "40", "41", "42", "43"],
        "words": ["retro court look", "canvas build", "everyday comfort", "clean minimalist style", "low-profile sole"],
    },
    "Performance Apparel": {
        "subs": ["tops", "bottoms", "outerwear"],
        "use_case": "gym",
        "brands": ["Boreal", "Kinetic Nine", "Apex Forge", "Lumen Athletics", "Strideworks"],
        "price": (149, 699),
        "size_system": "alpha", "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "words": ["moisture wicking fabric", "four-way stretch", "seamless construction", "quick dry", "soft hand feel"],
    },
    "Outdoor and Hiking": {
        "subs": ["hike", "climb", "camp"],
        "use_case": "hike",
        "brands": ["Ridgeline Supply", "Terra Co", "Northpeak", "Boreal"],
        "price": (349, 1899),
        "size_system": "BR", "sizes": ["38", "39", "40", "41", "42", "43", "44"],
        "words": ["waterproof membrane", "grippy lugged outsole", "insulated for cold mornings", "rugged ripstop shell", "all-terrain support"],
    },
    "Team Sports and Equipment": {
        "subs": ["football", "basketball", "volleyball"],
        "use_case": "football",
        "brands": ["Apex Forge", "Kinetic Nine", "Velora", "Strideworks", "Northpeak"],
        "price": (99, 799),
        "size_system": "BR", "sizes": ["38", "39", "40", "41", "42", "43"],
        "words": ["match grade", "indoor court grip", "reinforced toe", "pro level control", "training ready"],
    },
    "Bags and Accessories": {
        "subs": ["backpack", "duffel", "cap", "belt"],
        "use_case": "casual",
        "brands": ["Terra Co", "Boreal", "Lumen Athletics", "Ridgeline Supply", "Halcyon"],
        "price": (79, 599),
        "size_system": "alpha", "sizes": ["one size"],
        "words": ["lightweight daypack", "water resistant", "padded straps", "multiple compartments", "trail ready hydration"],
    },
}


def _sku(seed: str) -> str:
    return "SL-" + sha256(seed.encode()).hexdigest()[:8].upper()


def _product(pid, name, brand, category, subcategory, gender, color, use_case, price,
             rating, review_count, stock, store_id, specs, search_text, fit_summary,
             sale_price=None, availability="in_stock"):
    store = _STORE_BY_ID[store_id]
    return {
        "product_id": pid, "sku": _sku(pid), "name": name, "brand": brand,
        "category": category, "subcategory": subcategory, "gender": gender, "color": color,
        "use_case": use_case, "price": float(price), "sale_price": (float(sale_price) if sale_price else None),
        "rating": float(rating), "review_count": int(review_count), "stock": int(stock),
        "in_stock": stock > 0, "availability_status": availability,
        "pickup_eligible": store["store_type"] != "distribution_center",
        "shipping_eligible": True,
        "specs_summary": specs, "search_text": search_text, "fit_summary": fit_summary,
        "primary_store_id": store_id, "store_geo": store["location"],
        "updated_at_epoch": NOW_EPOCH,
        # search_vector filled later
    }


# ═══════════════════════════════════════════════════════════════════════════
#  HERO PRODUCTS — each engineered for one demo beat (documented in docs/demo_paths.md)
# ═══════════════════════════════════════════════════════════════════════════
HERO_PRODUCTS = [
    # 1) FIND-SIMILAR anchor
    _product(
        "PROD_HERO_PULSE", "Velora Pulse Road Runner", "Velora",
        "Running and Training Footwear", "road", "unisex", "coral", "running", 899.0,
        4.7, 1840, 60, "STORE_SP_PINHEIROS",
        "Neutral cushioned road running shoe, lightweight engineered mesh, responsive foam midsole, 8mm drop.",
        "Velora Pulse Road Runner in sunrise coral, a cushioned daily trainer for road running, smooth responsive ride for long easy miles and tempo days.",
        "True to size, neutral support, best for road and daily training.",
        sale_price=799.0,
    ),
    # 2) SEMANTIC-ONLY beat (query 'keep me warm on a chilly run' has no keyword overlap)
    _product(
        "PROD_HERO_THERMAL", "Boreal Thermal Run Layer", "Boreal",
        "Performance Apparel", "outerwear", "unisex", "navy", "running", 459.0,
        4.6, 540, 45, "STORE_SP_PAULISTA",
        "Insulated brushed-interior half-zip, wind-resistant front panel, thumbholes, reflective trims.",
        "Boreal Thermal Run Layer, an insulated half-zip built for cold early mornings outdoors, traps body heat so you stay comfortable when the temperature drops on a jog.",
        "Slim athletic fit, layer over a base tee for cold-morning outdoor sessions.",
    ),
    # 3) TYPO / FUZZY tolerance
    _product(
        "PROD_HERO_CUSHION", "Kinetic Nine Cushion Max", "Kinetic Nine",
        "Running and Training Footwear", "road", "unisex", "white", "running", 1099.0,
        4.8, 2310, 50, "STORE_RJ_COPA",
        "Max-cushion long-run shoe, high-stack supercritical foam, plush collar, rocker geometry.",
        "Kinetic Nine Cushion Max, maximum cushioning for long runs and recovery days, plush protective ride mile after mile.",
        "Roomy fit, max cushioning, ideal for long runs and recovery.",
    ),
    # 4) GEO-PROXIMITY winner (only at the Paulista flagship)
    _product(
        "PROD_HERO_TRAILGRIP", "Strideworks Trail Grip 2 Flagship Edition", "Strideworks",
        "Outdoor and Hiking", "hike", "unisex", "olive", "hike", 749.0,
        4.5, 320, 8, "STORE_SP_PAULISTA",
        "Aggressive lugged outsole, rock plate, water-resistant ripstop upper, flagship exclusive colorway.",
        "Strideworks Trail Grip 2 flagship edition trail running and hiking shoe, aggressive grip for technical terrain, exclusive to the Paulista flagship store.",
        "Snug technical fit, exclusive to the Paulista flagship, great for trail and light hiking.",
    ),
    # 5) SYNONYM + COLOR facet (listed petrol, matched by 'teal' synonym group)
    _product(
        "PROD_HERO_TEMPO", "Apex Forge Tempo Trainer", "Apex Forge",
        "Running and Training Footwear", "road", "men", "teal", "running", 829.0,
        4.6, 980, 40, "STORE_SP_MORUMBI",
        "Lightweight tempo trainer, firm responsive foam, breathable mesh, in a deep petrol colorway.",
        "Apex Forge Tempo Trainer in petrol teal, a fast lightweight trainer for tempo runs and intervals, snappy and breathable.",
        "Snug performance fit, runs slightly small, built for speed work.",
    ),
    # 6) FACET-DRILLDOWN + rating beat (high rating, many reviews, many sizes)
    _product(
        "PROD_HERO_RETRO", "Lumen Athletics Retro Court", "Lumen Athletics",
        "Lifestyle Sneakers", "sneakers", "unisex", "vintage white", "casual", 549.0,
        4.8, 4120, 120, "STORE_RJ_BARRA",
        "Retro court silhouette, vintage white leather-free upper, cupsole, classic stitching.",
        "Lumen Athletics Retro Court in vintage white, a classic everyday court sneaker with timeless clean style, pairs with everything.",
        "True to size, versatile everyday sneaker, wide size range.",
    ),
    # 7) CROSS-CATEGORY semantic bridge (accessory that neighbors trail-running)
    _product(
        "PROD_HERO_HYDRO", "Ridgeline Supply Hydration Vest", "Ridgeline Supply",
        "Bags and Accessories", "backpack", "unisex", "black", "hike", 489.0,
        4.5, 410, 35, "STORE_SP_PINHEIROS",
        "5L trail hydration vest, two soft flasks included, bounce-free fit, breathable mesh back.",
        "Ridgeline Supply Hydration Vest for trail running and long hikes, carries water and essentials with a bounce-free fit on technical terrain.",
        "Adjustable fit, ideal companion for trail running and long hikes.",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
#  PROCEDURAL FILLER — reach ~220 SKUs with believable variety
# ═══════════════════════════════════════════════════════════════════════════
def _build_catalog(rng: random.Random) -> list[dict]:
    products = list(HERO_PRODUCTS)
    target = 220
    idx = 0
    while len(products) < target:
        cat_name, cfg = rng.choice(list(CATEGORIES.items()))
        brand = rng.choice(cfg["brands"])
        sub = rng.choice(cfg["subs"])
        gender = rng.choice(GENDERS)
        color = rng.choice(COLORS)
        lo, hi = cfg["price"]
        price = round(rng.uniform(lo, hi) / 10) * 10 + 9.0
        on_sale = rng.random() < 0.28
        sale_price = round(price * rng.uniform(0.75, 0.92) / 10) * 10 + 9.0 if on_sale else None
        rating = round(rng.uniform(3.6, 4.9), 1)
        review_count = rng.randint(12, 2600)
        stock = rng.choice([0, 0, 4, 9, 18, 30, 55, 90, 150])
        store_id = rng.choice(_RETAIL_STORE_IDS + ["CD_MANAUS", "CD_RECIFE"])
        descriptor = rng.choice(cfg["words"])
        model_word = rng.choice(["Pro", "Lite", "Edge", "Core", "Flow", "Max", "Trail", "Court", "Sprint", "Summit", "Air", "Knit"])
        number = rng.choice(["", " 2", " 3", " GTX", " X", " Plus"])
        name = f"{brand} {model_word}{number}"
        pid = f"PROD_{cat_name[:3].upper()}_{idx:04d}"
        availability = "in_stock" if stock > 0 else "out_of_stock"
        specs = f"{descriptor.capitalize()}, {sub} {cat_name.split()[0].lower()} built for {cfg['use_case']}."
        search_text = (
            f"{name}, a {color} {sub} {cat_name.lower()} for {cfg['use_case']}. "
            f"{descriptor.capitalize()}. Designed for {gender}."
        )
        fit_summary = f"Standard {gender} fit, good for {cfg['use_case']} use."
        products.append(_product(
            pid, name, brand, cat_name, sub, gender, color, cfg["use_case"], price,
            rating, review_count, stock, store_id, specs, search_text, fit_summary,
            sale_price=sale_price, availability=availability,
        ))
        idx += 1
    return products


def _build_variants(products: list[dict], rng: random.Random) -> list[dict]:
    variants = []
    for p in products:
        cfg = CATEGORIES[p["category"]]
        sizes = cfg["sizes"]
        # 3 to 6 size variants, plus the product color
        chosen = sizes if len(sizes) <= 4 else rng.sample(sizes, k=rng.randint(3, min(6, len(sizes))))
        for size in chosen:
            vid = f"VAR_{p['product_id']}_{str(size).replace(' ', '')}"
            vstock = rng.choice([0, 2, 5, 12, 25, 40])
            variants.append({
                "variant_id": vid, "product_id": p["product_id"], "product_name": p["name"],
                "sku": _sku(vid), "size": str(size), "size_system": cfg["size_system"],
                "color": p["color"], "price": p["price"], "stock": vstock,
            })
    return variants


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (RAG) — shipping / returns / warranty / membership
# ═══════════════════════════════════════════════════════════════════════════
POLICIES = [
    {"policy_id": "POL_SHIPPING", "title": "Shipping and Delivery", "category": "shipping",
     "content": ("Standard shipping arrives in 3 to 7 business days. Express shipping arrives in 1 to 2 business days. "
                 "Orders fulfilled from the nearest store ship faster, and items from a distribution center can take longer. "
                 "Free standard shipping applies to orders above R$ 299.")},
    {"policy_id": "POL_RETURNS", "title": "Returns and Exchanges", "category": "returns",
     "content": ("You can return unworn items within 30 days of delivery for a full refund. Footwear must be returned with the original box. "
                 "Exchanges for a different size or color are free. Start a return online from your order history or at any StrideLane store.")},
    {"policy_id": "POL_PICKUP", "title": "Store Pickup and Reservations", "category": "shipping",
     "content": ("Reserve an item online and pick it up at your selected store, usually ready within 2 hours. "
                 "Distribution centers do not offer pickup. Bring your order confirmation to the pickup counter.")},
    {"policy_id": "POL_WARRANTY", "title": "Product Warranty", "category": "warranty",
     "content": ("Footwear carries a 90 day manufacturing defect warranty. Apparel carries a 60 day warranty against seam and zipper defects. "
                 "Normal wear is not covered. Bring proof of purchase to start a warranty claim.")},
    {"policy_id": "POL_MEMBERSHIP", "title": "StrideLane Membership Tiers", "category": "membership",
     "content": ("Members earn points on every purchase. Standard members earn 1 point per real spent, Plus members earn 2 points and get free express shipping, "
                 "and Elite members earn 3 points plus early access to limited drops. Points convert to store credit.")},
    {"policy_id": "POL_SIZING", "title": "Sizing and Fit Guide", "category": "warranty",
     "content": ("Sizes use the Brazilian numbering system for footwear and alpha sizes for apparel. Performance running shoes often run slightly small, "
                 "so consider a half size up for long runs. Use the fit summary on each product page and our free exchange policy if the fit is off.")},
]


# ═══════════════════════════════════════════════════════════════════════════
#  DEMO CUSTOMER + ONLINE FEATURE ROW
# ═══════════════════════════════════════════════════════════════════════════
DEMO_CUSTOMER = {
    "customer_id": "CUST_DEMO_001",
    "name": "Gabriel Cerioni",
    "email": "gabriel.cerioni@example.com.br",
    "city": "Sao Paulo",
    "state": "SP",
    "member_tier": "elite",
    "home_store_id": "STORE_SP_PAULISTA",
    "home_store_name": "StrideLane Paulista Flagship",
    # near Av. Paulista so the flagship is the nearest store (geo beat)
    "home_geo": "-46.6566,-23.5614",
    "account_created_at": "2021-03-12T10:00:00+00:00",
}


def _build_feature_row(centroid: list[float]) -> dict:
    return {
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "pref_category": "Running and Training Footwear",
        "pref_subcategory": "road",
        "pref_use_case": "running",
        "pref_color": "coral",
        "size_pref": "42",
        "price_band_min": 600.0,
        "price_band_max": 1200.0,
        "propensity_running": 0.91,
        "propensity_outdoor": 0.38,
        "propensity_lifestyle": 0.52,
        "recently_viewed": ["PROD_HERO_PULSE", "PROD_HERO_CUSHION", "PROD_HERO_TEMPO"],
        "updated_at_epoch": NOW_EPOCH,
        "interest_centroid": centroid,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  WRITE
# ═══════════════════════════════════════════════════════════════════════════
def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} records")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = f"{key}={safe_value}"
            break
    else:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = False,
) -> GeneratedDataset:
    rng = random.Random(seed if seed is not None else 42)
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    products = _build_catalog(rng)
    variants = _build_variants(products, rng)

    print(f"Embedding {len(products)} product descriptions...")
    product_vectors = embed([p["search_text"] for p in products])
    for p, vec in zip(products, product_vectors):
        p["search_vector"] = vec

    print(f"Embedding {len(POLICIES)} policies...")
    policy_vectors = embed([pol["content"] for pol in POLICIES])
    policies = [{**pol, "content_embedding": vec} for pol, vec in zip(POLICIES, policy_vectors)]

    # feature centroid = mean of the customer's recently-viewed product vectors
    by_id = {p["product_id"]: p for p in products}
    recently = ["PROD_HERO_PULSE", "PROD_HERO_CUSHION", "PROD_HERO_TEMPO"]
    centroid = _mean_vector([by_id[pid]["search_vector"] for pid in recently if pid in by_id])
    features = [_build_feature_row(centroid)]

    print("Writing JSONL files:")
    write_jsonl(resolved_output_dir, "products.jsonl", products)
    write_jsonl(resolved_output_dir, "variants.jsonl", variants)
    write_jsonl(resolved_output_dir, "stores.jsonl", STORES)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)
    write_jsonl(resolved_output_dir, "customers.jsonl", [DEMO_CUSTOMER])
    write_jsonl(resolved_output_dir, "features.jsonl", features)

    env_updates = {
        "DEMO_USER_ID": DEMO_CUSTOMER["customer_id"],
        "DEMO_USER_NAME": DEMO_CUSTOMER["name"],
        "DEMO_USER_EMAIL": DEMO_CUSTOMER["email"],
        "DEMO_USER_MEMBER_TIER": DEMO_CUSTOMER["member_tier"],
        "DEMO_USER_CITY": DEMO_CUSTOMER["city"],
        "DEMO_USER_STATE": DEMO_CUSTOMER["state"],
        "DEMO_USER_HOME_STORE_ID": DEMO_CUSTOMER["home_store_id"],
        "DEMO_USER_HOME_STORE_NAME": DEMO_CUSTOMER["home_store_name"],
        "DEMO_USER_HOME_GEO": DEMO_CUSTOMER["home_geo"],
    }
    if update_env_file:
        for key, value in env_updates.items():
            update_env(key, value)

    print(f"\nDemo user: {DEMO_CUSTOMER['name']} ({DEMO_CUSTOMER['customer_id']})")
    print(f"Home store: {DEMO_CUSTOMER['home_store_name']} ({DEMO_CUSTOMER['home_store_id']})")
    print("Done.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates=env_updates,
        summary={
            "products": len(products),
            "variants": len(variants),
            "stores": len(STORES),
            "policies": len(policies),
            "customers": 1,
            "features": len(features),
        },
    )


if __name__ == "__main__":
    generate_demo_data(update_env_file=False)
