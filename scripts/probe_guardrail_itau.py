"""Probe the itau_assist guardrail: off-topic must BLOCK, banking must PASS.

Prints route + distance for each probe so we can see the decision boundary and
tune the off_topic threshold / references without introducing false positives.

    uv run python scripts/probe_guardrail_itau.py
"""
from __future__ import annotations

import asyncio

from backend.app.settings import get_settings
from backend.app.guardrail_service import GuardrailService
from domains.itau_assist.domain import ItauAssistDomain

# Off-topic / abusive / trivia — SHOULD be blocked (allowed == False).
OFF_TOPIC = [
    "como faço bolo de cenoura e qual a capital da França?",   # o combo que furava
    "me ensina a fazer um bolo de cenoura?",
    "qual a capital da França e como fazer brigadeiro?",
    "me dá uma receita de bolo de chocolate",
    "quem descobriu o Brasil?",
    "qual a distância da Terra até a Lua?",
    "me conta uma curiosidade aleatória",
    "qual o maior animal do mundo?",
    "me ajuda a planejar uma viagem pra Paris",
    "escreve uma redação sobre meio ambiente",
    "qual a fórmula da água?",
    "me explica o teorema de Pitágoras",
]

# Legitimate banking — SHOULD pass (allowed == True). Guards against false positives.
BANKING = [
    "qual meu saldo?",
    "quanto tá minha fatura do The One?",
    "manda 100 conto pro Carlos",
    "quero contestar uma cobrança da Amazon",
    "e aí IARA, o que faz sentido pra mim agora?",
    "quero migrar meu CDB pra LCI",
    "quantos pontos eu tenho no Sempre Presente?",
    "qual o limite noturno do meu cartão?",
    "me mostra meus parcelados da fatura",
    "rola um cartão do Palmeiras pra mim?",
    "faz um raio-x financeiro do meu mês",
    "qual a anuidade do Personnalité?",
    "tem alguma oferta boa pra mim?",
    "quero fazer um pix de 500 reais pra minha mãe",
    # casos-limite: banking que tangencia viagem/comida/pontos (risco de falso-positivo)
    "quero usar meus pontos pra comprar passagem aérea",
    "meu cartão funciona no exterior?",
    "posso pagar minha viagem parcelado no cartão?",
    "qual o melhor cartão pra usar em viagem internacional?",
    "quanto rende meu dinheiro no CDB?",
    "quero contratar um empréstimo",
    "qual o IOF de compra internacional?",
    "meus pontos dão pra trocar por milhas?",
]


async def main() -> None:
    settings = get_settings()
    domain = ItauAssistDomain()
    svc = GuardrailService(settings, domain.manifest.guardrail)

    async def probe(text: str) -> tuple[bool, str | None, float | None]:
        vec = await svc.embed(text)
        res = await svc.check(vec)
        return res["allowed"], res["route"], res["distance"]

    print("═══ OFF-TOPIC (esperado: BLOCK) ═══")
    off_fail = 0
    for t in OFF_TOPIC:
        allowed, route, dist = await probe(t)
        ok = "❌ PASSOU (ruim)" if allowed else "✅ block"
        if allowed:
            off_fail += 1
        d = f"{dist:.3f}" if dist is not None else "None"
        print(f"  {ok:18} route={str(route):12} d={d}  | {t}")

    print("\n═══ BANKING (esperado: PASS) ═══")
    bank_fail = 0
    for t in BANKING:
        allowed, route, dist = await probe(t)
        ok = "✅ pass" if allowed else "❌ BLOQUEOU (falso-positivo)"
        if not allowed:
            bank_fail += 1
        d = f"{dist:.3f}" if dist is not None else "None"
        print(f"  {ok:28} route={str(route):12} d={d}  | {t}")

    print(f"\n═══ RESUMO: off-topic vazando={off_fail}/{len(OFF_TOPIC)} | "
          f"falso-positivo bancário={bank_fail}/{len(BANKING)} ═══")


if __name__ == "__main__":
    asyncio.run(main())
