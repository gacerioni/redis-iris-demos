"""Flush Redis keys for the ACTIVE demo domain only (never other domains, never Memory).

Multiple demos (itau_assist, banco_inter, serasa_experian, ...) share the same Redis
database. A global flush of all non-memory keys would nuke a demo that's running for
another domain. So this script scopes deletion to the active domain's key namespace:

    {redis_prefix}_*   → entity keys (e.g. banco_inter_account:ACC_001)
    {redis_prefix}:*   → namespace keys (meta, checkpoints, event stream)

The separator (`_` or `:`) is required so a prefix like "serasa" never matches
"serasa_experian_*". Agent Memory (memory:*) and every other domain's keys are left
untouched. Pass --all to force the legacy global flush (still preserves memory:*).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import get_active_domain
from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings


def main() -> None:
    settings = get_settings()
    r = create_redis_client(settings)

    flush_all = "--all" in sys.argv
    domain = get_active_domain(settings)
    prefix = domain.manifest.namespace.redis_prefix
    scoped_prefixes = (f"{prefix}_", f"{prefix}:")

    def should_delete(name: str) -> bool:
        if name.startswith("memory:"):
            return False  # Agent Memory: preservar sempre
        if flush_all:
            return True
        return name.startswith(scoped_prefixes)

    cursor = 0
    deleted = 0
    preserved = 0
    while True:
        cursor, keys = r.scan(cursor=cursor, count=500)
        if keys:
            to_delete = []
            for k in keys:
                name = k if isinstance(k, str) else k.decode()
                if should_delete(name):
                    to_delete.append(k)
                else:
                    preserved += 1
            if to_delete:
                r.delete(*to_delete)
                deleted += len(to_delete)
        if cursor == 0:
            break

    scope = "ALL non-memory keys" if flush_all else f"domain '{domain.manifest.id}' (prefix '{prefix}_' / '{prefix}:')"
    print(f"Flushed Redis at {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
    print(f"  Scope: {scope}")
    print(f"  Deleted {deleted} keys, preserved {preserved} keys (memory + other domains)")


if __name__ == "__main__":
    main()
