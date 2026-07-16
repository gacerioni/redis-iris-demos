"""Sanity: every curated starter prompt (the clickable demo buttons) MUST pass
the guardrail. A starter that gets blocked live = on-stage embarrassment.
Run: PYTHONPATH=. uv run python scripts/probe_starters_pass_guardrail.py
"""
from __future__ import annotations

import asyncio

from backend.app.core.domain_loader import load_domain
from backend.app.guardrail_service import GuardrailService
from backend.app.settings import get_settings

DOMAINS = ("picpay_assist", "serasa_limpa_nome", "itau_assist", "bradesco_bia")


async def main() -> None:
    settings = get_settings()
    total = passed = 0
    blocked: list[str] = []
    for domain_id in DOMAINS:
        domain = load_domain(domain_id)
        g = GuardrailService(settings, domain.manifest.guardrail)
        await g.warm_up()
        starters = [c.prompt for c in domain.manifest.branding.starter_prompts]
        print(f"\n=== {domain_id} ({len(starters)} starters) ===")
        for prompt in starters:
            vec = await g.embed(prompt)
            res = await g.check(vec)
            ok = res["allowed"]
            total += 1
            passed += ok
            tag = "OK  " if ok else "BLOCKED!"
            if not ok:
                blocked.append(f"{domain_id}: {prompt!r} -> route={res['route']} d={res['distance']}")
            print(f"  [{tag}] route={res['route']:<22} <- {prompt!r}")
    print(f"\n===== {passed}/{total} starters pass guardrail =====")
    if blocked:
        print("\nBLOCKED STARTERS (must fix):")
        for b in blocked:
            print(" -", b)
    else:
        print("All curated starters pass. No on-stage block risk.")


if __name__ == "__main__":
    asyncio.run(main())
