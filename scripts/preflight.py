"""Preflight de infra — falha rápido e com diagnóstico claro, ANTES do setup.

Testa cada peça do stack Iris com chamadas reais e baratas:
  1. .env com credenciais obrigatórias
  2. Redis Cloud: PING + módulo Search (FT._LIST)
  3. OpenAI: auth (models.list, zero tokens)
  4. Agent Memory API: search leve (auth + store + namespace reais)
  5. LangCache: search leve (auth + cache reais)
  6. Context Engine: admin key presente (validação completa no setup_surface)

Uso:
    uv run python scripts/preflight.py
Exit 0 = infra pronta. Exit 1 = lista de falhas no stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
import redis  # noqa: E402

from backend.app.settings import get_settings  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

failures: list[str] = []


def report(label: str, ok: bool, detail: str = "") -> None:
    mark = f"{GREEN}OK{RESET}" if ok else f"{RED}FAIL{RESET}"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{mark:>4}] {label}{suffix}")
    if not ok:
        failures.append(f"{label}: {detail}" if detail else label)


def check_env(s) -> None:
    required = {
        "OPENAI_API_KEY": s.openai_api_key,
        "REDIS_HOST": s.redis_host,
        "REDIS_PASSWORD": s.redis_password,
        "CTX_ADMIN_KEY": s.ctx_admin_key,
        "MEMORY_API_BASE_URL": s.memory_api_base_url,
        "MEMORY_STORE_ID": s.memory_store_id,
        "MEMORY_API_KEY": s.memory_api_key,
        "LANGCACHE_HOST": s.langcache_host,
        "LANGCACHE_CACHE_ID": s.langcache_cache_id,
        "LANGCACHE_API_KEY": s.langcache_api_key,
    }
    missing = [k for k, v in required.items() if not v]
    report("env: credenciais obrigatórias", not missing, ", ".join(missing) if missing else "")


def check_redis(s) -> None:
    try:
        r = redis.Redis(
            host=s.redis_host, port=s.redis_port,
            username=s.redis_username, password=s.redis_password,
            ssl=s.redis_ssl, socket_connect_timeout=5, socket_timeout=5,
        )
        r.ping()
        n_idx = len(r.execute_command("FT._LIST"))
        report("Redis Cloud: PING + Search module", True, f"{n_idx} índices")
    except Exception as exc:  # noqa: BLE001
        report("Redis Cloud: PING + Search module", False, str(exc)[:120])


def check_openai(s) -> None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=s.openai_api_key, timeout=10)
        client.models.list()
        report("OpenAI: auth", True)
    except Exception as exc:  # noqa: BLE001
        report("OpenAI: auth", False, str(exc)[:120])


def check_memory_api(s) -> None:
    api_key = s.memory_api_key
    if not api_key.lower().startswith(("bearer ", "basic ")):
        api_key = f"Bearer {api_key}"
    url = f"{s.memory_api_base_url.rstrip('/')}/v1/stores/{s.memory_store_id}/long-term-memory/search"
    try:
        resp = httpx.post(
            url,
            headers={"Authorization": api_key},
            json={"text": "ping", "limit": 1},
            timeout=10,
        )
        # 424 = store sem memórias ainda — auth e store válidos
        ok = resp.status_code in (200, 424)
        report("Agent Memory API: auth + store", ok, "" if ok else f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        report("Agent Memory API: auth + store", False, str(exc)[:120])


def check_langcache(s) -> None:
    url = f"{s.langcache_host.rstrip('/')}/v1/caches/{s.langcache_cache_id}/entries/search"
    try:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {s.langcache_api_key}"},
            json={"prompt": "ping"},
            timeout=10,
        )
        ok = resp.status_code == 200
        report("LangCache: auth + cache", ok, "" if ok else f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        report("LangCache: auth + cache", False, str(exc)[:120])


def main() -> int:
    s = get_settings()
    print("")
    print("Preflight de infra")
    print("──────────────────")
    check_env(s)
    check_redis(s)
    check_openai(s)
    check_memory_api(s)
    check_langcache(s)
    report("Context Engine: admin key presente", bool(s.ctx_admin_key))
    print("")
    if failures:
        print(f"{RED}Preflight FALHOU{RESET} ({len(failures)} problema(s)). Corrige antes do setup:")
        for f in failures:
            print(f"  • {f}")
        return 1
    print(f"{GREEN}Infra pronta.{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
