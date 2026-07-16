"""Seed long-term memories for the active domain's demo customer.

Clears all existing long-term memories for the demo owner, then seeds
the entries defined in the domain's manifest.seed_memories.

Usage:
    DOMAIN=reddash uv run python -m scripts.seed_memories
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.domain_loader import get_active_domain
from backend.app.memory_service import MemoryService
from backend.app.redis_connection import create_redis_client
from backend.app.settings import ENV_PATH, get_settings


def main() -> None:
    settings = get_settings()
    domain = get_active_domain(settings)
    service = MemoryService(settings)

    if not service.is_configured():
        print("Memory not configured (skipping). Set MEMORY_API_BASE_URL, MEMORY_STORE_ID, MEMORY_API_KEY to enable.")
        return

    seeds = domain.manifest.seed_memories
    if not seeds:
        print(f"Domain '{domain.manifest.id}' has no seed_memories defined. Nothing to do.")
        return

    env = dotenv_values(ENV_PATH)
    identity = domain.manifest.identity
    owner_id = env.get(identity.id_env_var) or identity.default_id
    print(f"Domain: {domain.manifest.id}")
    print(f"Owner: {owner_id}")
    print(f"Namespace: {settings.effective_memory_namespace}")

    # Memory API only accepts [A-Za-z0-9-] in IDs and namespaces.
    # Sanitize the domain id (e.g. "redis_eats" → "redis-eats") so seed IDs are valid.
    safe_domain_id = domain.manifest.id.replace("_", "-")

    # SCOPED PURGE (was a global wipe). On a SHARED Redis Cloud the demos all live in the
    # same memory store; deleting memory:{store}:ltm:* wiped the LTM of EVERY other demo
    # (this clobbered bradesco/prod). Purge ONLY this domain's own seed keys
    # (seed-<domain>-*); the re-seed below recreates them. Other demos stay intact.
    print(f"Purging existing seed memories for '{safe_domain_id}' (scoped, not global)...")
    r = create_redis_client(settings)
    store_id = settings.memory_store_id
    if store_id:
        prefix = f"memory:{store_id}:ltm:seed-{safe_domain_id}-*"
        cursor, keys = 0, []
        while True:
            cursor, batch = r.scan(cursor=cursor, match=prefix, count=200)
            keys.extend(batch)
            if cursor == 0:
                break
        if keys:
            r.delete(*keys)
            print(f"  Deleted {len(keys)} '{safe_domain_id}' seed LTM keys (other domains untouched)")
        else:
            print("  No existing seed LTM keys for this domain")

    print(f"Seeding {len(seeds)} memories...")
    for i, entry in enumerate(seeds):
        mid = f"seed-{safe_domain_id}-{i}"
        created = service.create_long_term_memory(
            text=entry.text,
            owner_id=owner_id,
            memory_type=entry.memory_type,
            topics=entry.topics,
            memory_id=mid,
        )
        print(f"  Seeded: {entry.text!r} -> {created}")

    _ensure_memory_index(settings)
    print("Done.")


def _ensure_memory_index(settings) -> None:
    """Ensure the Memory API's FT search index exists.

    A prior FLUSHDB destroys the index and the hosted Memory API won't
    rebuild it automatically.  We recreate it from the known schema so
    that search works immediately after seeding.
    """
    store_id = settings.memory_store_id
    if not store_id:
        return
    index_name = f"memory:{store_id}:ltm"
    prefix = f"memory:{store_id}:ltm:"
    r = create_redis_client(settings)
    try:
        r.execute_command("FT.INFO", index_name)
        return
    except Exception:
        pass
    print(f"  Recreating memory search index '{index_name}'...")
    try:
        r.execute_command(
            "FT.CREATE", index_name,
            "ON", "HASH",
            "PREFIX", "1", prefix,
            "SCHEMA",
            "text", "TEXT",
            "owner_id", "TAG",
            "namespace", "TAG",
            "memory_type", "TAG",
            "topics", "TAG", "SEPARATOR", ",",
            "session_id", "TAG",
            "id", "TAG",
            "created_at", "NUMERIC",
            "updated_at", "NUMERIC",
            "text_vector", "VECTOR", "HNSW", "6",
            "TYPE", "FLOAT32",
            "DIM", "3072",
            "DISTANCE_METRIC", "COSINE",
        )
        print("  Index created.")
    except Exception as e:
        print(f"  Index creation failed: {e}")


if __name__ == "__main__":
    main()
