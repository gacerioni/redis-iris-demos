"""Semantic routing guardrail using redisvl SemanticRouter.

Routes are loaded from the active domain's GuardrailConfig. If the domain
has no guardrail config, the service reports is_configured() == False and
all checks are skipped.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from functools import partial

from openai import AsyncOpenAI
from redisvl.extensions.router import Route, SemanticRouter
from redisvl.extensions.router.schema import DistanceAggregationMethod
from redisvl.utils.vectorize import OpenAITextVectorizer

from backend.app.core.domain_contract import GuardrailConfig
from backend.app.redis_connection import build_redis_url
from backend.app.settings import Settings

log = logging.getLogger("iris.guardrail")


class GuardrailService:
    def __init__(self, settings: Settings, guardrail_config: GuardrailConfig | None = None) -> None:
        self._openai_api_key = settings.openai_api_key
        self._embedding_model = settings.openai_embedding_model
        self._redis_url = build_redis_url(settings)
        self._enabled = settings.guardrail_enabled
        self._config = guardrail_config
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._router: SemanticRouter | None = None
        self._lock = asyncio.Lock()

    def is_configured(self) -> bool:
        return bool(self._enabled and self._config and self._openai_api_key and self._redis_url)

    async def _ensure_router(self) -> SemanticRouter:
        if self._router is not None:
            return self._router
        async with self._lock:
            if self._router is not None:
                return self._router
            if not self._config:
                raise RuntimeError("No guardrail config provided")

            vectorizer = OpenAITextVectorizer(
                model=self._embedding_model,
                api_config={"api_key": self._openai_api_key},
            )

            routes = [
                Route(
                    name=route_cfg.name,
                    references=route_cfg.references,
                    distance_threshold=route_cfg.distance_threshold,
                )
                for route_cfg in self._config.routes
            ]

            router_name = self._config.router_name

            def _build() -> SemanticRouter:
                return SemanticRouter(
                    name=router_name,
                    vectorizer=vectorizer,
                    routes=routes,
                    redis_url=self._redis_url,
                    overwrite=True,
                )

            self._router = await asyncio.to_thread(_build)
            log.info("Semantic router '%s' initialized (%d routes)", router_name, len(routes))
            return self._router

    async def embed(self, text: str) -> list[float]:
        resp = await self._openai.embeddings.create(
            input=[text],
            model=self._embedding_model,
        )
        return resp.data[0].embedding

    async def check(self, vector: list[float]) -> dict[str, Any]:
        if not self._config:
            return {"allowed": True, "route": None, "distance": None}
        try:
            router = await self._ensure_router()
            # route_many + aggregation MIN em vez de router(...) single-match:
            # 1) o caminho single do redisvl 0.18.2 retorna name=None de forma
            #    errática mesmo com match exato no índice;
            # 2) a agregação default (avg) dilui um match exato na média de
            #    TODAS as referências da rota — com 16 refs off_topic e
            #    threshold 0.5, a rota de bloqueio nunca dispara. MIN pergunta
            #    "qual rota tem a referência mais próxima?", que é a semântica
            #    que um guardrail precisa.
            matches = await asyncio.to_thread(
                partial(
                    router.route_many,
                    vector=vector,
                    max_k=max(len(self._config.routes), 2),
                    aggregation_method=DistanceAggregationMethod.min,
                )
            )
            # Default PERMISSIVO: sem nenhuma rota dentro do threshold, deixa
            # passar pro agente decidir. Bloqueia SÓ quando a rota mais próxima
            # é explicitamente não permitida (off_topic).
            if not matches:
                return {"allowed": True, "route": None, "distance": None}
            best = min(matches, key=lambda m: (m.distance is None, m.distance))
            if best.name is None:
                return {"allowed": True, "route": None, "distance": None}
            # Decisão por flags `blocked` por rota (multi-rotas de intenção).
            # Fallback legado: sem flags, tudo que não é allowed_route_name bloqueia.
            blocked_names = {r.name for r in self._config.routes if r.blocked}
            if not blocked_names and self._config.allowed_route_name:
                blocked_names = {
                    r.name for r in self._config.routes
                    if r.name != self._config.allowed_route_name
                }
            allowed = best.name not in blocked_names
            return {"allowed": allowed, "route": best.name, "distance": best.distance}
        except Exception:
            log.warning("Guardrail check failed, allowing through", exc_info=True)
            return {"allowed": True, "route": None, "distance": None}

    async def warm_up(self) -> None:
        if self.is_configured():
            await self._ensure_router()
            log.info("Guardrail service warmed up")

    async def close(self) -> None:
        pass
