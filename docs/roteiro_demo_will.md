# Demo script — Itaú LangCache/KYC PoC (Will)

Happy path for the customer's use case: semantic cache (token reduction BC) +
customer-360 slicing (the semantic search service his team is building).
Every prompt below is a starter chip on the board, except the paraphrase in
act 2 (typed on purpose, to prove semantic matching). Live-tested via
`bash scripts/test_golden_paths_itau.sh kyc|cached|nba`.

**Setup:** `bash scripts/reset_itau_light.sh`, then click **Reset** on the
FinOps tab so the session tells a clean story.

| # | Prompt | What shows up | Line for Will |
|---|--------|---------------|---------------|
| 1 | ★ Meus seguros ("O que você sabe sobre meus seguros?") | `get_customer_profile_slice` in Activity; badge "~49k LLM tokens · 11s" | "Esse é o SEU momento de vida, no SEU schema (macrocategoria, justificativa, indiceConfianca). O agente não comeu o payloadzão: a busca semântica devolveu só o bloco de seguros, ~400 tokens de um doc de 3 mil. É o serviço que seu time está construindo, pronto." |
| 2 | Momento de vida ("Qual meu momento de vida?") | Same tool, another slice of the same doc | "Mesmo documento, outra fatia. Dynamo + pgvector viram um JSON com índice vetorial no mesmo Redis." |
| 3 | Perdi meu cartão (starter LangCache) | ⚡ CACHE HIT + badge "~47k tokens avoided" | "Cada turno completo custa ~47 mil tokens de prompt. O hit evita o turno INTEIRO: 47k tokens e 12s viram ~1s." |
| 4 | Digitar: "Roubaram meu cartão, e agora?" | ⚡ CACHE HIT (different wording) | "Não é a mesma frase, é semanticamente igual. 'Machine learning' vs 'aprendizado de máquina', versão banco. Bank of America: ~30% de redução." |
| 5 | ★ O que faz sentido pra mim? | LCI + cartão Palmeiras (NBA) | "KYC 360 é o que o banco SABE de você; next best action é o que ele FAZ com isso. Mesmo Redis servindo as duas pontas. É o caminho pra 'TV no deep link'." |
| 6 | FinOps tab | Hit rate, tokens spent vs avoided ($), Customer-360 Slicing (−86%), latency p50, projection | Ask his requests/day, type it into the projection, watch the monthly $ recalc live. |
| 7 | (optional) "Me dá uma receita de bolo de cenoura." | 🛡 blocked before the LLM | "Guardrail semântico também é token não gasto." |

**Why this order:** acts 1-2 and 5 produce real LLM turns (they calibrate the
"tokens avoided" average), acts 3-4 produce the hits, act 6 harvests
everything. Inverted, the panel opens empty.

**Sizing close (terminal):**

```bash
DEMO_DOMAIN=itau_assist uv run python -m scripts.measure_footprint     # ~8 KB/entry measured; 1M entries ≈ 9 GB
DEMO_DOMAIN=itau_assist uv run python -m scripts.estimate_langcache_bc # markdown BC table from measured averages
```

Answers his exact fear from 2026-07-13: "não tenho ideia da dimensão da minha
base semântica".
