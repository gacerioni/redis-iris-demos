"""Gateway service — o gauntlet: router → cache → rate limit → LLM → reconcile.

Cada request passa pelos 3 portões Redis antes de gastar 1 token de LLM.
O serviço emite um evento por etapa (consumido pela UI via SSE) e mantém os
contadores de usage no Redis (que SÃO o dashboard).

Isolamento do Itaú: namespace `tcp:`, router próprio, LangCache reusado só pra
entries (nunca dá flush). Settings lidos, nunca escritos.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import tiktoken
from openai import AsyncOpenAI

from backend.app.gateway import config as cfg
from backend.app.gateway.rate_limiter import TokenRateLimiter
from backend.app.guardrail_service import GuardrailService
from backend.app.langcache_service import LangCacheService
from backend.app.settings import Settings

NS = "tcp"
_USAGE_FIELDS = ("spent", "saved_router", "saved_cache", "requests", "answered", "blocked", "throttled", "cached")

try:
    _ENC = tiktoken.get_encoding("o200k_base")
except Exception:  # noqa: BLE001
    _ENC = None


def _estimate_tokens(text: str) -> int:
    if _ENC is not None:
        return len(_ENC.encode(text))
    return max(1, len(text) // 4)


class GatewayService:
    def __init__(self, settings: Settings, redis_client: Any) -> None:
        self._s = settings
        self._r = redis_client
        self._limiter = TokenRateLimiter(redis_client)
        self._guard = GuardrailService(settings, cfg.build_router_config())
        self._cache = LangCacheService(settings)
        self._oai = AsyncOpenAI(api_key=settings.openai_api_key,
                                base_url=settings.openai_base_url or None)

    async def warm_up(self) -> None:
        if self._guard.is_configured():
            await self._guard.warm_up()

    # ── estado/config viva (UI muda ao vivo via tcp:config) ──
    def _read_runtime(self) -> dict[str, Any]:
        raw = self._r.hgetall(f"{NS}:config") or {}
        strategy = raw.get("strategy", "token_bucket")
        overrides: dict[str, dict[str, float]] = {}
        for a in cfg.AREAS:
            cap = raw.get(f"cap:{a.id}")
            refill = raw.get(f"refill:{a.id}")
            if cap or refill:
                overrides[a.id] = {}
                if cap:
                    overrides[a.id]["capacity"] = int(float(cap))
                if refill:
                    overrides[a.id]["refill_per_sec"] = float(refill)
        return {"strategy": strategy, "overrides": overrides}

    def _policy(self, area_id: str, runtime: dict[str, Any]):
        ov = runtime["overrides"].get(area_id, {})
        return cfg.policy_for(area_id, capacity=ov.get("capacity"), refill_per_sec=ov.get("refill_per_sec"))

    def _bump(self, area: str, **deltas: int) -> None:
        key = f"{NS}:usage:{area}"
        for field, val in deltas.items():
            if val:
                self._r.hincrby(key, field, val)

    def state(self) -> dict[str, Any]:
        """Snapshot pro dashboard: baldes + usage acumulado por área."""
        runtime = self._read_runtime()
        strategy = runtime["strategy"]
        areas = []
        for a in cfg.AREAS:
            pol = self._policy(a.id, runtime)
            peek = self._limiter.peek(pol, strategy)
            usage_raw = self._r.hgetall(f"{NS}:usage:{a.id}") or {}
            usage = {f: int(usage_raw.get(f, 0)) for f in _USAGE_FIELDS}
            areas.append({
                "id": a.id, "label": a.label, "color": a.color,
                "capacity": pol.capacity, "refill_per_sec": round(pol.refill_per_sec, 2),
                "remaining": round(max(0.0, peek.remaining), 1),
                "used": round(min(pol.capacity, max(0.0, peek.used)), 1),
                "usage": usage,
            })
        return {"strategy": strategy, "areas": areas}

    def set_config(self, *, strategy: str | None = None, overrides: dict[str, dict[str, float]] | None = None) -> None:
        key = f"{NS}:config"
        if strategy:
            self._r.hset(key, "strategy", strategy)
        for area_id, vals in (overrides or {}).items():
            if "capacity" in vals:
                self._r.hset(key, f"cap:{area_id}", vals["capacity"])
            if "refill_per_sec" in vals:
                self._r.hset(key, f"refill:{area_id}", vals["refill_per_sec"])

    def reset(self) -> None:
        """Zera SÓ as keys tcp: (baldes, janelas, usage). Nunca toca o resto."""
        for k in self._r.scan_iter(match=f"{NS}:*", count=500):
            self._r.delete(k)

    # ── o gauntlet ──
    async def process(self, area_id: str, prompt: str) -> AsyncIterator[dict[str, Any]]:
        runtime = self._read_runtime()
        strategy = runtime["strategy"]
        policy = self._policy(area_id, runtime)
        input_tokens = _estimate_tokens(cfg.SYSTEM_PROMPT + prompt)
        estimate = input_tokens + cfg.EXPECTED_OUTPUT_TOKENS

        yield {"type": "start", "area": area_id, "strategy": strategy, "estimate": estimate}

        # ── Portão 1: Semantic Router (off-topic não gasta token) ──
        yield {"type": "gate", "gate": "router", "status": "checking"}
        if self._guard.is_configured():
            vec = await self._guard.embed(prompt)
            verdict = await self._guard.check(vec)
            if not verdict.get("allowed", True):
                self._bump(area_id, requests=1, blocked=1, saved_router=estimate)
                yield {"type": "gate", "gate": "router", "status": "blocked",
                       "route": verdict.get("route"), "distance": verdict.get("distance"),
                       "saved": estimate}
                yield {"type": "answer", "text": (
                    "Essa pergunta está fora do escopo do assistente — bloqueada no "
                    "roteador, sem gastar tokens de LLM.")}
                yield {"type": "done", "outcome": "blocked", "spent": 0, "saved": estimate}
                return
        yield {"type": "gate", "gate": "router", "status": "passed"}

        # ── Portão 2: Cache semântico (pergunta repetida não gasta token) ──
        yield {"type": "gate", "gate": "cache", "status": "checking"}
        if self._cache.is_configured():
            hit = await self._cache.search(prompt)
            if hit and hit.get("response"):
                self._bump(area_id, requests=1, cached=1, saved_cache=estimate)
                yield {"type": "gate", "gate": "cache", "status": "hit",
                       "similarity": round(hit.get("similarity", 0), 3), "saved": estimate}
                yield {"type": "answer", "text": hit["response"]}
                yield {"type": "done", "outcome": "cached", "spent": 0, "saved": estimate}
                return
        yield {"type": "gate", "gate": "cache", "status": "miss"}

        # ── Portão 3: Rate limit por área (token bucket / sliding window) ──
        yield {"type": "gate", "gate": "ratelimit", "status": "checking"}
        rl = self._limiter.check(policy, cost=estimate, strategy=strategy)
        if not rl.allowed:
            self._bump(area_id, requests=1, throttled=1)
            yield {"type": "gate", "gate": "ratelimit", "status": "throttled",
                   "remaining": round(rl.remaining, 1), "retry_after_ms": rl.retry_after_ms,
                   "capacity": policy.capacity}
            yield {"type": "answer", "text": (
                f"Área '{area_id}' sem orçamento de tokens no momento "
                f"(retry em ~{rl.retry_after_ms} ms). Request barrada antes do LLM.")}
            yield {"type": "done", "outcome": "throttled", "spent": 0, "saved": 0}
            return
        yield {"type": "gate", "gate": "ratelimit", "status": "passed",
               "remaining": round(rl.remaining, 1), "capacity": policy.capacity}

        # ── LLM: gpt-5.4-mini, streaming, com usage real ──
        yield {"type": "gate", "gate": "llm", "status": "calling"}
        text_parts: list[str] = []
        actual_total = estimate  # fallback se usage não vier
        try:
            stream = await self._oai.chat.completions.create(
                model=cfg.GATEWAY_MODEL,
                messages=[{"role": "system", "content": cfg.SYSTEM_PROMPT},
                          {"role": "user", "content": prompt}],
                reasoning_effort=cfg.REASONING_EFFORT,
                max_completion_tokens=cfg.MAX_OUTPUT_TOKENS,
                stream=True,
                stream_options={"include_usage": True},
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    text_parts.append(delta)
                    yield {"type": "answer-delta", "delta": delta}
                if chunk.usage:
                    actual_total = chunk.usage.total_tokens
        except Exception as exc:  # noqa: BLE001
            # reconcilia o estimate (refund) e reporta erro
            self._limiter.reconcile(policy, estimated=estimate, actual=0, strategy=strategy)
            self._bump(area_id, requests=1)
            yield {"type": "gate", "gate": "llm", "status": "error", "error": str(exc)[:160]}
            yield {"type": "done", "outcome": "error", "spent": 0, "saved": 0}
            return

        # ── Reconcile: estimate → custo real; store no cache; usage ──
        self._limiter.reconcile(policy, estimated=estimate, actual=actual_total, strategy=strategy)
        self._bump(area_id, requests=1, answered=1, spent=actual_total)
        answer = "".join(text_parts)
        if self._cache.is_configured() and answer.strip():
            try:
                await self._cache.store(prompt, answer)
            except Exception:  # noqa: BLE001
                pass

        post = self._limiter.peek(policy, strategy)
        yield {"type": "gate", "gate": "llm", "status": "done",
               "actual_tokens": actual_total, "estimated": estimate}
        yield {"type": "usage", "area": area_id, "spent": actual_total,
               "remaining": round(post.remaining, 1), "capacity": policy.capacity}
        yield {"type": "done", "outcome": "answered", "spent": actual_total, "saved": 0}
