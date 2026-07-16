"""Token Control Plane — app FastAPI standalone (porta 8050).

Separado do servidor de chat (8040) de propósito: concern diferente, e assim
nunca encosta no demo do Itaú que roda em 8040.

Endpoints:
  GET  /api/health           — liveness + flags dos serviços
  GET  /api/gateway/state    — snapshot dos baldes + usage (dashboard)
  GET  /api/gateway/config   — áreas, estratégias disponíveis
  POST /api/gateway/config   — muda estratégia / capacidade / refill ao vivo
  POST /api/gateway/reset    — zera SÓ as keys tcp:
  POST /api/gateway/ask      — SSE: roda o gauntlet
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.app.gateway import config as cfg
from backend.app.gateway.gateway_service import GatewayService
from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings

settings = get_settings()
_redis = create_redis_client(settings)
gateway = GatewayService(settings, _redis)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await gateway.warm_up()
    yield


app = FastAPI(title="Token Control Plane", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_STATIC = Path(__file__).parent / "static"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "token-control-plane",
        "model": cfg.GATEWAY_MODEL,
        "router_enabled": gateway._guard.is_configured(),
        "cache_enabled": gateway._cache.is_configured(),
        "areas": [a.id for a in cfg.AREAS],
    }


@app.get("/api/gateway/state")
def state() -> dict[str, Any]:
    return gateway.state()


@app.get("/api/gateway/config")
def get_config() -> dict[str, Any]:
    return {
        "strategies": ["token_bucket", "sliding_window"],
        "areas": [{"id": a.id, "label": a.label, "color": a.color,
                   "default_capacity": a.capacity} for a in cfg.AREAS],
        "model": cfg.GATEWAY_MODEL,
    }


class ConfigUpdate(BaseModel):
    strategy: str | None = None
    overrides: dict[str, dict[str, float]] | None = None


@app.post("/api/gateway/config")
def set_config(body: ConfigUpdate) -> dict[str, Any]:
    gateway.set_config(strategy=body.strategy, overrides=body.overrides)
    return gateway.state()


@app.post("/api/gateway/reset")
def reset() -> dict[str, Any]:
    gateway.reset()
    return gateway.state()


class AskRequest(BaseModel):
    area: str
    prompt: str


@app.post("/api/gateway/ask")
async def ask(body: AskRequest) -> StreamingResponse:
    async def gen():
        async for event in gateway.process(body.area, body.prompt):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
