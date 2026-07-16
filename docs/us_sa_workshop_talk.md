# US SA Workshop: Bradesco story + 2 demos (10-15 min)

Slot starts at slide 7 of Diego's deck. Four content slides, two live demos.
Timing plan: 2 min event story, 4 min LangCache (tell-show-tell), 6 min IRIS
BIA (tell-show-tell), 1 min close. Demos: langcache.platformengineer.io and
the local `bradesco_en` stack (`bash scripts/start_bradesco_en_demo.sh --skip-setup`).

---

## Slide 7 · "Bradesco Immersion Day, São Paulo" (photo collage)

On-slide bullets (short, over the photos):
- 60+ people, full-day immersion: platform engineering, data, AI teams and leadership
- We only paused for the World Cup match (with a little surprise for the customers)
- Standing-room moments: Redis for streaming, Redis as a system of record
- 2 net-new opportunities on top of the AWS motion: semantic cache for BIA (their GenAI assistant) and the on-prem OSS Redis 6.0.9 takeout

### Talking track (~2 min)

> "Quick story from Brazil before the demos. We ran a full-day immersion at
> Bradesco, one of the largest banks in Latin America. Sixty-plus people in
> the room, from platform engineers to leadership, and they stayed the whole
> day. We only stopped when the World Cup match started, and we used that
> break to give the customers a nice surprise, which honestly bought us more
> goodwill than any slide.
>
> Two moments made eyebrows go up. First, Redis for streaming: most of the
> room had Redis boxed as 'the cache', and seeing streams plus consumer
> groups handling real pipelines reframed it. Second, Redis as a system of
> record for a set of noble use cases: feature stores, agent memory, session
> state. Not 'can it cache this', but 'this data LIVES here'.
>
> The pipeline outcome: on top of the AWS opportunity we were already
> working, the day generated two net-new ones. One, a semantic cache for
> BIA, which is Bradesco's own GenAI assistant, and that's exactly the
> LangCache demo I'll show you first. Two, a takeout of their on-prem open
> source Redis, which is back-level on 6.0.9, so there's a real modernization
> conversation attached.
>
> The point of my 15 minutes: both opportunities came out of two demos you
> can run yourselves tomorrow. Let me show you."

---

## Slide 8 · "Demo 1: LangCache, the 5-minute story" (single diagram)

One diagram, no more than this on the slide:
`user -> [LangCache search] -> HIT: answer in ~50ms  |  MISS: LLM -> store -> answer`
plus a small box: `attributes: { company, business_unit, person }` and a
counter: `every hit = a full LLM call you did not pay for`.

### TELL (~1 min)

> "LangCache is semantic caching as a managed API on Redis Cloud. The
> mental model is one sentence: before you call the model, you vector-search
> the question against everything you've already answered; on a hit you skip
> the LLM entirely. Same meaning, different words, still a hit.
>
> The piece people underestimate is scoping. Every entry carries attributes,
> company, business unit, person, so a cached answer can be private to one
> user, shared within a team, or global. That's the difference between a toy
> and something a bank will deploy.
>
> The business case is one multiplication: every hit is a full agent turn
> you didn't pay for. At Bradesco's scale that's the whole pitch. Bank of
> America published around 30 percent token reduction with semantic caching."

### SHOW (~3 min, langcache.platformengineer.io, guided script on the right rail)

Follow the 5 clickable steps, narrating one line each:
1. Per-person identity: two users store different roles, writes are scoped.
2. Per-person cache: same question, each gets their own answer back. "Scopes never leak."
3. BU scope + disambiguation: 'what does deploy mean' becomes software for
   engineering and process for finance. "Same word, different worlds."
4. Company scope: one person asks about machine learning, now it's cached for everyone.
5. Cross-language hit: ask in another language, hit the cached answer.
   "It searches meaning, not words. This is the moment the room goes quiet."

### TELL (~30 s)

> "That's the demo that turned into the BIA cache opportunity. It's one
> FastAPI file and a static page, it's on GitHub in our SA org, README takes
> you from clone to demo in five minutes. Steal it."

---

## Slide 9 · "Demo 2: IRIS BIA, the full context engine" (architecture strip)

One horizontal strip on the slide:
`guardrail (semantic router) -> LangCache -> agent memory (STM/LTM) -> context surface tools -> online feature store`, all pointing at ONE Redis box.
Sub-line: "Born from Yusuf's demo. Ported and hyper-personalized per customer with spec-driven development."

### TELL (~1 min)

> "Now the cherry on the cake, and I want to start with credit where it's
> due: this is built on Yusuf's amazing IRIS demo. I don't reinvent the
> wheel. What I do is port it per customer using spec-driven development: I
> write a spec for the customer's world, their entities, their journeys,
> their brand voice, and the coding agent regenerates the domain pack. On
> top of Yusuf's base I add mocked feature-store routes, semantic routing
> and guardrails, RAG over policies, short and long term agent memory, a
> React polish pass, and a FinOps panel that turns cache hits into dollars.
> One customer fork takes me a day, not weeks, and every journey is
> harness-tested before I ever demo it.
>
> What you're about to see is the exact demo from the Bradesco event,
> localized to English: Zelle instead of Pix, dollars, and yes, the 2026
> World Cup easter egg works even better for you, Dallas is a host city."

### SHOW (~4-5 min, local bradesco_en, prompts from the starter chips)

1. **"Give me a snapshot of my month."** One turn, and BIA reads accounts,
   cards, billing cycles, transactions, tickets, memories. "Every tool call
   you see in the right panel is a Redis query through the Context Surface.
   The agent discovered these tools by scanning the indexes, we didn't
   hand-write them."
2. **"There's a charge on my statement I don't recognize."** The smart
   dispute: BIA finds the recurring pattern and pushes back before filing.
   "Feature data plus memory turning a chargeback into a save."
3. **"Where does my money earn more?"** then apply the recommendation with
   the amount, then confirm. "Watch the confirm gate: request is not
   confirmation. And the write persists, the feature store recomputes, the
   next recommendation already sees the new balance. State, not vibes."
4. **"Send $200 to Carlos."** Natural language payment, contact resolution,
   balance preview, gate, protocol. Then "What's my balance now?"
5. Open the **FinOps tab**: hit rate, tokens avoided, latency p50 cache vs
   full turn, monthly projection. "This panel is what turns a cool demo
   into a business case meeting."
6. (If time) **"I'm going to the 2026 World Cup, what does Bradesco have
   for me?"** "Easter eggs matter. This one got a round of applause in São
   Paulo, and the final is basically in your backyard."

### TELL (~30 s)

> "Everything you saw is one Redis: router, cache, memory, tools, feature
> store. The repo has a domain pack per customer, a one-command start
> script, a reset script, and a golden-path harness so the demo can't rot.
> If you have an account that needs this story, bring me the customer's
> world and I'll help you spec a fork."

---

## Slide 10 · "Steal this playbook" (close)

On-slide bullets:
- LangCache demo: GitHub, clone to demo in 5 minutes
- IRIS: domain pack per customer, spec-driven port, harness-tested golden paths
- Credit: Yusuf's base demo. My job is hyper-personalization, not reinvention
- Bring me an account, leave with a fork

### Talking track (~30 s)

> "Two demos, two open playbooks. The LangCache one is a five-minute clone.
> The IRIS one looks like magic but it's a method: Yusuf's base, a spec per
> customer, an agent doing the port, and a harness keeping it honest. My ask:
> pick one account where 'Redis is just a cache' is costing you the deal,
> and let's build their fork together. Thank you!"

---

## Prep checklist (before the call)

- [ ] `bash scripts/start_bradesco_en_demo.sh --skip-setup` in YOUR terminal, then FinOps Reset
- [ ] langcache.platformengineer.io logged in, cache flushed via the UI scope buttons
- [ ] Photos on slide 7, diagram on slide 8, architecture strip on slide 9
- [ ] Run `bash scripts/test_golden_paths_bradesco_en.sh all` in the morning: green = sleep easy
