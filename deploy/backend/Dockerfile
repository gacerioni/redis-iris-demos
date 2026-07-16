# Backend FastAPI — Itaú Assist demo
# Roda na porta 8040, fala com Redis Cloud + Memory API + LangCache + OpenAI

FROM python:3.12-slim AS base

# Dependências do sistema (curl pra healthcheck, build-essential pra rust deps quando necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv (gerenciador de deps Python)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Camada de dependências (cached enquanto pyproject não muda)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Código da aplicação
COPY backend ./backend
COPY domains ./domains
COPY scripts ./scripts

# Output gerado (JSONL + generated_models.py) — virá via volume ou COPY em tempo de build
COPY output ./output

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8040

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8040/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8040", "--no-access-log"]
