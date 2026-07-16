# Demo script — aiqfome workshop (AIQ, delivery concierge)

Golden mold applied to food delivery: concierge + natural-language cart +
feature-store refund decision + semantic dish search + FinOps. Every prompt is
a starter chip. Live-tested via `bash scripts/test_golden_paths_aiqfome.sh <cenario>`.

**Setup:** take ownership in YOUR terminal first (kills any stray stack):
`bash scripts/start_aiqfome_demo.sh --skip-setup` (env is already set; from
scratch works too but recreates the surface). Pre-workshop: `bash
scripts/reset_aiqfome_light.sh` + **Reset** on the FinOps tab.

| # | Prompt | What shows up | Line for the customer |
|---|--------|---------------|----------------------|
| 1 | Rastrear entrega ("Cadê meu pedido?") | #AIQ-8842 em rota, Jonas de moto a 1,2 km | "Concierge com contexto REAL: pedido, entregador, posição, ETA, tudo do Redis em tempo real." |
| 2 | ★ Bateu a fome de japa ("Tô com vontade de comer comida japonesa.") | Busca vetorial nos pratos + EXCLUI o temaki de camarão citando a alergia | "Busca semântica no catálogo + memória de longo prazo: ele filtra o alérgeno SOZINHO. Esse mesmo índice de pratos vira o retail search de vocês." |
| 3 | Adicionar temaki → "Adiciona um hot roll também." → Ver carrinho → "Tira o hot roll do carrinho." | CRUD do carrinho em linguagem natural, totais recalculados, frete grátis clube | "Carrinho de verdade num JSON do Redis: o agente mantém estado transacional sem alucinar." |
| 4 | Fechar pedido ("Fecha o pedido.") → "Confirma sim!" | Turno 1 = resumo + gate; turno 2 = pedido #AIQ-88XX criado, visível no histórico na hora | "Pedido ≠ confirmação: o agente nunca fecha sem confirmar. E o pedido novo já aparece nas tools no turno seguinte." |
| 5 | ★ Reembolso sem burocracia ("Meu combo veio sem a batata, quero reembolso.") | Auto-aprovado + voucher R$ 10, explicado pelo histórico (214 pedidos desde 2019) | "A feature store online decidindo challenge vs aprovação em tempo real: o caso iFood. Cliente ouro não manda foto." |
| 6 | ★ O que peço hoje? ("O que você me recomenda hoje?") | NBA: combo japonês + xodó + voucher R$ 15 (sexta: pizza com a Sofia vence) | "Recomendação servida por features online + memória virando oferta." |
| 7 | Meu perfil de fome ("O que você sabe sobre meu perfil de fome?") | Fatias do perfil 360 (economia no FinOps) | "O customer-360 fatiado semanticamente: o agente nunca come o payload inteiro." |
| 8 | Cached: Reembolso / Clube aiqfome / Prazo / Taxa | ⚡ CACHE HIT nos 4 | "Pergunta recorrente não gasta token nem segundos: LangCache." |
| 9 | FinOps tab | Hit rate, tokens avoided, slicing, latências, projeção | Plug o volume real de chats deles e mostra o $/mês. |
| 10 | (safety WOW) "Põe um temaki de camarão no carrinho." | Recusa + alerta + alternativa (o xodó) | "Segurança alimentar por memória: o agente NUNCA adiciona alérgeno silenciosamente." |

**Retail search bridge (o gancho do fork):** o índice vetorial dos 72 pratos
(nome+descrição embedados, categoria/tags/alérgenos TAG, preço/rating/popularity
NUMERIC, lat/lon prontos pra GEO) é EXATAMENTE a base do demo de retail search
(autocomplete, FTS, sinônimos, vector, RRF). Mesmo Redis, mesma base, duas
superfícies.

**Sizing close (terminal):**
```bash
DEMO_DOMAIN=aiqfome uv run python -m scripts.measure_footprint
DEMO_DOMAIN=aiqfome uv run python -m scripts.estimate_langcache_bc
```

**Gotchas:**
- UMA demo local por vez (stash de surface é save-only): trocar de domínio =
  subir do zero, ou acertar DEMO_DOMAIN + CTX_SURFACE_ID no .env antes do
  `--skip-setup`; SEMPRE reseed LangCache após troca.
- Seeds do LangCache sem frases de dado vivo ("quanto tempo", "cadê", "tem
  cupom") — política/FAQ apenas.
- Nos caminhos de escrita (checkout), o gate é regra de ouro: turno 1 resume e
  pergunta, turno 2 executa.
