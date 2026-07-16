# Demo script — BS2 Pay / Adiq (ADA, merchant concierge)

Same golden mold as the Itaú demo, translated to acquiring: semantic cache
(token BC) + business-360 slicing + receivables-advance NBA. Every prompt is a
starter chip on the board. Live-tested via `bash scripts/test_golden_paths_bs2.sh <cenario>`.

**Setup:** `bash scripts/start_bs2_demo.sh` (from scratch) or
`bash scripts/reset_bs2_light.sh` (re-seed), then **Reset** on the FinOps tab.

| # | Prompt | What shows up | Line for the customer |
|---|--------|---------------|----------------------|
| 1 | Raio-X do negócio ("Me dá um raio-X do meu negócio.") | Saldo PJ, agenda, 2 disputas, POS instável, gancho da BF | "Um agente que conhece a OPERAÇÃO do lojista: caixa, agenda, disputas e até a maquininha instável do quiosque." |
| 2 | Disputas abertas ("Tem alguma disputa de chargeback aberta?") | Chargeback esperto: Marcos Vinicius = contestável (recorrente + entregas confirmadas); Juliana = reembolso | "O agente não aceita a perda: cruza histórico + memória + política antes de responder. Chargeback é dinheiro." |
| 3 | ★ Meu negócio ("O que você sabe sobre o meu negócio?") | `get_customer_profile_slice` fatia o business-360 | "O momento do negócio no schema de vocês, fatiado semanticamente: o agente nunca come o payload inteiro (economia no painel FinOps)." |
| 4 | ★ O que faz sentido pra mim? ("O que faz sentido pro meu negócio agora?") | NBA: antecipação R$ 150 mil + WOW Black Friday/estoque 2025 | "A memória vira oferta: o agente LEMBRA que faltou estoque na BF 2025 e antecipa a solução." |
| 5 | ★ Antecipar R$ 150 mil ("Antecipa R$ 150 mil da minha agenda.") → "Confirmado, pode antecipar." | Turno 1 = resumo + confirmação (gate); turno 2 = executa, persiste (saldo 84,3k → 232k, agenda recalcula) | "Execução de verdade com recompute-on-write: o próximo NBA já enxerga a agenda menor." |
| 6 | Pagar fornecedor ("Paga R$ 32 mil pro meu fornecedor Almeida.") → "Isso, pode confirmar." | Resolve o contato, preview de saldo, gate, protocolo | Natural language payment, PJ. |
| 7 | Taxas MDR / Prazo de repasse / Chargeback / Antecipação (Cached) | ⚡ CACHE HIT nos 4 | "Pergunta recorrente não gasta token: ~50k tokens e ~15s evitados por hit (badge na resposta)." |
| 8 | FinOps tab | Hit rate, tokens spent vs avoided, slicing −87%, latências, projeção | Plug the customer's requests/day, watch monthly $ recalc. |
| 9 | (optional) "Me dá uma receita de bolo de cenoura." | 🛡 blocked before the LLM | Guardrail semântico. |

**Sizing close (terminal):** same scripts as Itaú, generic per domain:

```bash
DEMO_DOMAIN=bs2_adiq uv run python -m scripts.measure_footprint
DEMO_DOMAIN=bs2_adiq uv run python -m scripts.estimate_langcache_bc
```

**Gotchas:**
- ONE local demo at a time. `stash_surface_id` only SAVES the surface id
  (`CTX_SURFACE_ID_<SLUG>`); there is NO auto-restore on switch-back, so a
  `--skip-setup` switch leaves DEMO_DOMAIN pointing at one domain and
  CTX_SURFACE_ID at another (mixed state: agent gets the wrong tools). The
  supported path is: boot the target demo from zero (`start_*_demo.sh`), or
  manually set DEMO_DOMAIN + CTX_SURFACE_ID from the stash before
  `--skip-setup`. Always reseed LangCache after a switch (single global cache,
  flushed+reseeded per domain by `seed_langcache`).
- LangCache seeds must NEVER include live-data phrasings ("qual meu saldo",
  "quanto tenho..."): they get semantically swallowed by policy answers.
  Tariff/FAQ wordings only.
- Never push past turn 1 without confirming on advance/payment paths: the gate
  is the golden rule (anti double-apply). "Pedido ≠ confirmação" even when the
  request already carries the exact amount.
