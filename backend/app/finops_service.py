from __future__ import annotations

"""FinOps telemetry for the chat loop.

Persists per-domain counters in Redis so the UI can show the business case
live: cache hit rate, real token spend, estimated tokens avoided by LangCache
hits, and latency percentiles (cache hit vs full agent turn).

Honesty rule: "tokens saved" on a cache hit is estimated from the rolling
average of REAL agent turns measured in this same environment (prompt +
completion, which includes the full system prompt / tool schemas overhead).
The sample count is exposed so the UI can qualify the estimate.
"""

import logging
from typing import Any

import redis.asyncio as redis_asyncio

from backend.app.redis_connection import create_async_redis_client
from backend.app.settings import Settings

log = logging.getLogger("uvicorn.error")

_LATENCY_SAMPLE_CAP = 500


def _percentile(sorted_values: list[int], pct: float) -> int:
    if not sorted_values:
        return 0
    idx = min(int(len(sorted_values) * pct), len(sorted_values) - 1)
    return sorted_values[idx]


class FinOpsService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._prefix = f"{settings.demo_domain}:finops"
        self._redis: redis_asyncio.Redis | None = None

    def _client(self) -> redis_asyncio.Redis:
        if self._redis is None:
            self._redis = create_async_redis_client(self._settings)
        return self._redis

    @property
    def _counters_key(self) -> str:
        return f"{self._prefix}:counters"

    def _latency_key(self, kind: str) -> str:
        return f"{self._prefix}:lat:{kind}"

    async def _push_latency(self, kind: str, latency_ms: int) -> None:
        r = self._client()
        pipe = r.pipeline(transaction=False)
        pipe.lpush(self._latency_key(kind), latency_ms)
        pipe.ltrim(self._latency_key(kind), 0, _LATENCY_SAMPLE_CAP - 1)
        await pipe.execute()

    async def record_llm_turn(self, *, tokens_in: int, tokens_out: int, latency_ms: int) -> None:
        try:
            r = self._client()
            pipe = r.pipeline(transaction=False)
            pipe.hincrby(self._counters_key, "turns", 1)
            pipe.hincrby(self._counters_key, "llm_turns", 1)
            pipe.hincrby(self._counters_key, "tokens_in", tokens_in)
            pipe.hincrby(self._counters_key, "tokens_out", tokens_out)
            await pipe.execute()
            await self._push_latency("llm", latency_ms)
        except Exception as exc:
            log.warning("FinOps record_llm_turn failed: %s", exc)

    async def record_cache_hit(self, *, latency_ms: int, lookup_ms: int | None = None) -> dict[str, int]:
        """Increment hit counters; returns the tokens-avoided estimate used."""
        saved = {"saved_in": 0, "saved_out": 0, "samples": 0}
        try:
            r = self._client()
            counters = await r.hgetall(self._counters_key)
            llm_turns = int(counters.get("llm_turns", 0) or 0)
            if llm_turns > 0:
                saved["saved_in"] = int(counters.get("tokens_in", 0)) // llm_turns
                saved["saved_out"] = int(counters.get("tokens_out", 0)) // llm_turns
                saved["samples"] = llm_turns
            pipe = r.pipeline(transaction=False)
            pipe.hincrby(self._counters_key, "turns", 1)
            pipe.hincrby(self._counters_key, "cache_hits", 1)
            pipe.hincrby(self._counters_key, "saved_in", saved["saved_in"])
            pipe.hincrby(self._counters_key, "saved_out", saved["saved_out"])
            await pipe.execute()
            await self._push_latency("hit", latency_ms)
            if lookup_ms is not None:
                await self._push_latency("lookup", lookup_ms)
        except Exception as exc:
            log.warning("FinOps record_cache_hit failed: %s", exc)
        return saved

    async def record_guardrail_block(self, *, latency_ms: int) -> None:
        try:
            r = self._client()
            pipe = r.pipeline(transaction=False)
            pipe.hincrby(self._counters_key, "turns", 1)
            pipe.hincrby(self._counters_key, "blocked", 1)
            await pipe.execute()
            await self._push_latency("hit", latency_ms)
        except Exception as exc:
            log.warning("FinOps record_guardrail_block failed: %s", exc)

    async def record_context_slice(self, *, full_tokens: int, served_tokens: int) -> None:
        """KYC-360 slicing: context served vs the full document it was cut from."""
        try:
            r = self._client()
            pipe = r.pipeline(transaction=False)
            pipe.hincrby(self._counters_key, "slice_calls", 1)
            pipe.hincrby(self._counters_key, "slice_full_tokens", full_tokens)
            pipe.hincrby(self._counters_key, "slice_served_tokens", served_tokens)
            await pipe.execute()
        except Exception as exc:
            log.warning("FinOps record_context_slice failed: %s", exc)

    async def summary(self) -> dict[str, Any]:
        r = self._client()
        counters = await r.hgetall(self._counters_key)

        def _i(field: str) -> int:
            return int(counters.get(field, 0) or 0)

        hit_lat = sorted(int(v) for v in await r.lrange(self._latency_key("hit"), 0, -1))
        llm_lat = sorted(int(v) for v in await r.lrange(self._latency_key("llm"), 0, -1))
        lookup_lat = sorted(int(v) for v in await r.lrange(self._latency_key("lookup"), 0, -1))

        llm_turns = _i("llm_turns")
        cache_hits = _i("cache_hits")
        answered = llm_turns + cache_hits
        return {
            "turns": _i("turns"),
            "cache_hits": cache_hits,
            "llm_turns": llm_turns,
            "blocked": _i("blocked"),
            "hit_rate": round(cache_hits / answered, 4) if answered else 0.0,
            "tokens_in": _i("tokens_in"),
            "tokens_out": _i("tokens_out"),
            "saved_in": _i("saved_in"),
            "saved_out": _i("saved_out"),
            "avg_tokens_in_per_llm_turn": _i("tokens_in") // llm_turns if llm_turns else 0,
            "avg_tokens_out_per_llm_turn": _i("tokens_out") // llm_turns if llm_turns else 0,
            "latency_hit_ms": {
                "p50": _percentile(hit_lat, 0.50),
                "p95": _percentile(hit_lat, 0.95),
                "samples": len(hit_lat),
            },
            "latency_llm_ms": {
                "p50": _percentile(llm_lat, 0.50),
                "p95": _percentile(llm_lat, 0.95),
                "samples": len(llm_lat),
            },
            "latency_lookup_ms": {
                "p50": _percentile(lookup_lat, 0.50),
                "p95": _percentile(lookup_lat, 0.95),
                "samples": len(lookup_lat),
            },
            "slice_calls": _i("slice_calls"),
            "slice_full_tokens": _i("slice_full_tokens"),
            "slice_served_tokens": _i("slice_served_tokens"),
        }

    async def reset(self) -> None:
        r = self._client()
        await r.delete(
            self._counters_key,
            self._latency_key("hit"),
            self._latency_key("llm"),
            self._latency_key("lookup"),
        )
