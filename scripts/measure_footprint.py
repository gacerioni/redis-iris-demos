"""Measure the REAL Redis footprint of the demo's semantic structures.

Answers the sizing question ("qual o tamanho da base semântica?") with measured
bytes instead of guesses: scans the active domain's keys, samples MEMORY USAGE
per key-group, and extrapolates the semantic-cache dataset size for a target
entry count.

A KYC-360 slice here (hash: text + metadata + 1536-dim FLOAT32 embedding) is
byte-equivalent to a semantic cache entry, so its measured size anchors the
LangCache sizing.

Usage:
    DEMO_DOMAIN=itau_assist uv run python -m scripts.measure_footprint
    DEMO_DOMAIN=itau_assist uv run python -m scripts.measure_footprint --cache-entries 5000000
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.domain_loader import get_active_domain
from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings

SAMPLE_CAP = 100  # MEMORY USAGE samples per key-group


def _group_of(key: str, prefix: str) -> str:
    """itau_assist:kyc360_chunk:CUST:cat -> itau_assist:kyc360_chunk ;
    itau_assist_account:ACC_001 -> itau_assist_account"""
    rest = key[len(prefix):]
    sep = rest[0] if rest else ":"
    first = rest[1:].split(":", 1)[0] if rest[1:] else ""
    return f"{prefix}{sep}{first}"


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-entries", type=int, default=1_000_000,
                        help="Target semantic-cache entry count for the extrapolation (default 1M).")
    args = parser.parse_args()

    settings = get_settings()
    domain = get_active_domain(settings)
    prefix = domain.manifest.namespace.redis_prefix
    r = create_redis_client(settings)

    keys_by_group: dict[str, list[str]] = defaultdict(list)
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor=cursor, count=500)
        for k in keys:
            name = k if isinstance(k, str) else k.decode()
            if name.startswith((f"{prefix}_", f"{prefix}:")):
                keys_by_group[_group_of(name, prefix)].append(name)
        if cursor == 0:
            break

    print(f"\nRedis footprint — domain '{prefix}' ({sum(len(v) for v in keys_by_group.values())} keys)\n")
    print(f"{'key group':<44} {'count':>7} {'avg/key':>12} {'est. total':>12}")
    print("-" * 80)

    slice_avg = 0
    for group in sorted(keys_by_group):
        keys = keys_by_group[group]
        sample = keys[:SAMPLE_CAP]
        sizes = [int(r.execute_command("MEMORY", "USAGE", k) or 0) for k in sample]
        avg = sum(sizes) / len(sizes) if sizes else 0
        total = avg * len(keys)
        print(f"{group:<44} {len(keys):>7} {human(avg):>12} {human(total):>12}")
        if "kyc360_chunk" in group:
            slice_avg = avg

    if slice_avg:
        n = args.cache_entries
        dataset = slice_avg * n
        print("\nSemantic-cache sizing (anchored on the measured slice: text + metadata")
        print(f"+ 1536-dim FLOAT32 embedding = {human(slice_avg)}/entry):\n")
        for entries in sorted({100_000, 500_000, n, 5_000_000}):
            print(f"  {entries:>12,} entries  →  {human(slice_avg * entries):>10}  (+ index overhead ~20%)")
        print(f"\nTarget ({n:,} entries): ~{human(dataset * 1.2)} with index overhead.")
        print("Embedding dim dominates the entry size: 1536-dim FLOAT32 = 6 KB of the")
        print("entry. Smaller dims or quantization shrink the dataset near-linearly.")


if __name__ == "__main__":
    main()
