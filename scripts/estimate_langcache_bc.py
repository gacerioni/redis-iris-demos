"""LangCache business-case calculator: cache hits -> tokens avoided -> $.

Pulls the MEASURED averages from the running demo's FinOps endpoint when
available (avg tokens per uncached agent turn, observed hit rate) so the
projection is anchored on real numbers, then prints a markdown table ready
for the executive doc. Every input can be overridden.

Usage:
    uv run python -m scripts.estimate_langcache_bc
    uv run python -m scripts.estimate_langcache_bc --requests-per-day 500000 --hit-rate 0.30
"""

from __future__ import annotations

import argparse
import json
import urllib.request

FINOPS_URL = "http://localhost:8040/api/finops/summary"

# Fallbacks when the demo backend is not running (anchored on measured runs)
DEFAULT_AVG_TOKENS_IN = 47_000
DEFAULT_AVG_TOKENS_OUT = 450
DEFAULT_HIT_RATE = 0.30          # conservative PoC target (Bank of America ref: ~30%)
DEFAULT_ENTRY_BYTES = 8_054      # measured: text + metadata + 1536-dim FLOAT32 embedding


def _measured() -> dict | None:
    try:
        with urllib.request.urlopen(FINOPS_URL, timeout=3) as resp:
            return json.load(resp)
    except Exception:
        return None


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def human_tokens(n: float) -> str:
    if n >= 1e9:
        return f"{n / 1e9:,.1f}B"
    if n >= 1e6:
        return f"{n / 1e6:,.1f}M"
    return f"{n:,.0f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests-per-day", type=int, default=100_000)
    parser.add_argument("--hit-rate", type=float, default=None,
                        help="Cacheable share of requests (0-1). Default: measured, else 0.30.")
    parser.add_argument("--avg-tokens-in", type=int, default=None,
                        help="Avg prompt tokens per uncached agent turn. Default: measured.")
    parser.add_argument("--avg-tokens-out", type=int, default=None,
                        help="Avg completion tokens per uncached agent turn. Default: measured.")
    parser.add_argument("--price-in", type=float, default=2.5, help="USD per 1M input tokens.")
    parser.add_argument("--price-out", type=float, default=10.0, help="USD per 1M output tokens.")
    parser.add_argument("--cache-entries", type=int, default=1_000_000,
                        help="Semantic-cache entry count for dataset sizing.")
    parser.add_argument("--entry-bytes", type=int, default=DEFAULT_ENTRY_BYTES,
                        help="Bytes per cache entry (see scripts/measure_footprint.py).")
    args = parser.parse_args()

    measured = _measured()
    source = "measured (live demo)" if measured and measured.get("llm_turns") else "defaults"
    avg_in = args.avg_tokens_in or (measured or {}).get("avg_tokens_in_per_llm_turn") or DEFAULT_AVG_TOKENS_IN
    avg_out = args.avg_tokens_out or (measured or {}).get("avg_tokens_out_per_llm_turn") or DEFAULT_AVG_TOKENS_OUT
    hit_rate = args.hit_rate if args.hit_rate is not None else (
        (measured or {}).get("hit_rate") or DEFAULT_HIT_RATE
    )

    daily_hits = args.requests_per_day * hit_rate
    monthly_hits = daily_hits * 30
    monthly_in = monthly_hits * avg_in
    monthly_out = monthly_hits * avg_out
    monthly_usd = (monthly_in / 1e6) * args.price_in + (monthly_out / 1e6) * args.price_out
    dataset_bytes = args.cache_entries * args.entry_bytes * 1.2  # + index overhead

    print(f"\n## LangCache business case ({source})\n")
    print("| Premissa | Valor |")
    print("|---|---|")
    print(f"| Requests/dia | {args.requests_per_day:,} |")
    print(f"| Hit rate do cache semântico | {hit_rate:.0%} |")
    print(f"| Tokens médios por turno SEM cache (prompt) | {avg_in:,} |")
    print(f"| Tokens médios por turno SEM cache (completion) | {avg_out:,} |")
    print(f"| Preço input / output (USD por 1M) | ${args.price_in} / ${args.price_out} |")
    print(f"| Entradas no cache semântico | {args.cache_entries:,} |")
    print(f"| Bytes por entrada (medido) | {args.entry_bytes:,} |")
    print("\n| Resultado | Valor |")
    print("|---|---|")
    print(f"| Hits/mês | {monthly_hits:,.0f} |")
    print(f"| Tokens evitados/mês | {human_tokens(monthly_in + monthly_out)} |")
    print(f"| Custo LLM evitado/mês | ${monthly_usd:,.0f} |")
    print(f"| Custo LLM evitado/ano | ${monthly_usd * 12:,.0f} |")
    print(f"| Dataset do cache (c/ ~20% de índice) | {human_bytes(dataset_bytes)} |")
    print("\nCada hit também troca segundos de turno de agente por milissegundos de")
    print("busca vetorial (ver painel FinOps na demo: p50 hit vs p50 full turn).\n")


if __name__ == "__main__":
    main()
