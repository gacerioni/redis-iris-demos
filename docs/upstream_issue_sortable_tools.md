# [DRAFT v2] Upstream issue — redislabsdev/cloud-context-engine

> Evidência coletada em 2026-06-10 contra `context-surfaces 0.0.5`, Surface real
> (`itau_assist`, 70 auto-generated tools, 29 Transaction docs). Versão enxuta,
> caso Pix como fio condutor. Cole abaixo na issue.

---

**Title:** `filter_*` tools expose no sort mechanism — temporal queries fail even when the index has SORTABLE fields

Hey team 👋 — we're building customer-facing agent demos on top of Context
Surfaces (a banking domain, ~70 auto-generated tools). Filtering works great,
but any question involving *order* — "my **latest** transactions", "my **last
two** Pix transfers" — has no efficient answer today: the generated tools offer
no way to sort, and nothing tells the LLM what order results arrive in. The
interesting part: the sorting capability already exists in the RediSearch index
that Context Surfaces builds — it just never surfaces (pun intended) in the
tool layer. Repro and suggested fixes below.

## Summary

A user asks the agent: *"what were my last two Pix transfers?"*. There is no
efficient way to answer this with the generated tools today:

- Generated `filter_*` tools accept only `value`, `limit`, `offset` — no
  `sort_by` / `sort_dir` — and their descriptions say nothing about result order.
- Results come back in internal doc order. In our 29-doc Transaction collection,
  the 3 most recent records ranked at positions **15, 27 and 28** — outside the
  first page at the default `limit: 10`.
- The agent's natural first call was `{"limit": 2}`, assuming recency. It got
  two unrelated month-old card purchases.

The index side is *not* the problem: `Field(..., index="numeric",
sortable=True)` correctly produces `NUMERIC SORTABLE` attributes (verified via
`FT.INFO`). Modeling timestamps the Redis way — epoch seconds as a numeric
sortable field — puts the right capability in the index. But no generated tool
ever exposes it, so `FT.SEARCH ... SORTBY` sits unused one layer below.

Note that range tools don't cover this either: the engine already generates
`find_<entity>_by_<field>_range(min_value, max_value)` for numeric fields,
which with epoch timestamps would nicely answer *time-window* questions
("transfers this week"). But "my **last two**" is an ordering question, not a
window question — without `sort_by` the agent would have to probe shrinking
windows to approximate recency.

## Repro (Pix case)

1. Declare a timestamp as epoch numeric: `purchased_at: int =
   Field(index="numeric", sortable=True)` → `FT.INFO` shows
   `['attribute', 'purchased_at', 'type', 'NUMERIC', 'SORTABLE', 'UNF']` ✓
2. Inspect the generated tool via `client.list_tools(agent_key)`:

   ```json
   {
     "name": "filter_transaction_by_customer_id",
     "inputSchema": {
       "properties": {
         "value":  {"type": "string"},
         "limit":  {"type": "number", "description": "Maximum number of results to return (default: 10)"},
         "offset": {"type": "number", "description": "Number of results to skip (default: 0)"}
       },
       "required": ["value"]
     }
   }
   ```

   Across all 70 generated tools: zero occurrences of `sort` in any name,
   description or `inputSchema`.
3. Ask the agent for "the last two Pix transfers" → wrong records, unless you
   prompt-engineer it to fetch every page and sort in-context (2 round-trips +
   29 full documents in the context window for what `SORTBY purchased_at DESC
   LIMIT 0 2` answers with 2).

## Suggested fix

1. **Expose `sort_by` + `sort_dir` on `filter_*` tools** whenever the entity has
   at least one SORTABLE attribute. `sort_by` as an enum of the sortable field
   names, `sort_dir` as `asc`/`desc`, mapped straight to `FT.SEARCH ... SORTBY`.
   This alone closes the gap — the index capability already exists.
2. **State the result order in every generated tool description**, even if it is
   "unspecified". One line of codegen stops LLMs from assuming recency.
3. *(Nice-to-have)* A first-class datetime/epoch convention in `ContextModel`
   (e.g. `Field(index="datetime")` storing epoch + sortable) so every team
   models time the Redis way instead of shipping ISO strings that silently
   don't index. (Our schemas inherited ISO-string timestamps from the official
   `redis/redis-iris-demos` templates — the ecosystem models time this way
   today, and `sortable=True` on a string is dropped without any warning.)

## Workaround we ship today

System-prompt rules forcing `limit=50` + pagination + in-context sorting on
every list-style question. Works for demo-sized data only; token cost grows
linearly with collection size.
