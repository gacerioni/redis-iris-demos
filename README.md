# Redis Iris Demos — fork BR (Itaú Assist + Serasa Limpa Nome IA)

> Dois demos em **português brasileiro** sobre Redis Iris coexistindo no mesmo codebase:
> **Itaú Assist** (banco Personnalité — contestação, Pix, cross-sell) e
> **Limpa Nome IA** (consumer credit Serasa — descoberta real-time de pendências
> escondidas, aceite de proposta, projeção de score, contestação de consulta suspeita).

Fork de [`redis/redis-iris-demos`](https://github.com/redis/redis-iris-demos) com:

- Domínio novo **`itau_assist`** (perfil Personnalité, Itaú The One, alta renda)
- Domínio novo **`serasa_limpa_nome`** (score 950 Premium Plus, descoberta real-time de pendências escondidas em credores parceiros)
- Domínio novo **`picpay_assist`** (carteira social: racha a conta, cashback → Cofrinho, anti-golpe do Pix — 3 tools determinísticas)
- Domínio novo **`bradesco_bia`** (banco premium BIA: next-best-offer lendo um feature store online no Redis + ML em tempo real, com explicabilidade)
- Domínio derivado **`redis_eats`** (food delivery brasileiro com humor Copa do Mundo)
- Tools determinísticas: `simulate_pix_transfer` (Itaú) + 4 tools Serasa (`discover_pending_debts_realtime`, `simulate_proposal_accept`, `simulate_score_projection`, `dispute_inquiry`) — todas escrevem no Context Surface real
- Tema visual customizável por domínio via classe CSS `body.domain-<id>` (Itaú = navy+orange, Serasa = magenta+orange)
- Pacote `deploy/` pra subir em VM GCP com Caddy + Let's Encrypt
- Validador anti-drift entre `starter_prompts` e `guardrail.references`
- Toggle `DEMO_LTM_PERSIST` pra modo "teatro" em produção pública

---

## Sumário

- [Componentes Redis Iris](#componentes-redis-iris)
- [Domínios disponíveis](#domínios-disponíveis)
- [Quick start (local)](#quick-start-local)
- [Configuração via `.env`](#configuração-via-env)
- [Deploy em produção (GCP + Caddy)](#deploy-em-produção-gcp--caddy)
- [Arquitetura](#arquitetura)
- [Demo paths do Itaú Assist](#demo-paths-do-itaú-assist)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Criando um novo domínio](#criando-um-novo-domínio)
- [Troubleshooting](#troubleshooting)
- [Crédito ao upstream](#crédito-ao-upstream)

---

## Componentes Redis Iris

| Componente | O que faz nesta demo |
|---|---|
| **Context Retriever** | Expõe entidades bancárias (Customer, Card, Transaction, BillingCycle, Dispute, PixContact, RewardsAccount, Policy…) como ferramentas MCP geradas a partir do schema. Agente consulta estado operacional vivo, não PDF de política. |
| **Agent Memory** | Memória de curto prazo da sessão + longo prazo escopada por usuário. Reconhece padrões recorrentes (AMAZON PAY LU como assinatura do cliente), suporta cross-sell (LCI, Visa Infinite Plus, Wine Club) e respeita opt-outs (consignado). |
| **LangCache** | Cache semântico pra perguntas de política recorrentes (limites Pix, regras de contestação) — devolve resposta em milissegundos sem token de LLM. |
| **Semantic Router** | Guardrail que classifica a query antes do agente. Default permissivo: bloqueia SÓ off-topic com confiança (batata frita, signo, cor favorita), deixa borderline-banking passar. |

## Domínios disponíveis

| ID | App | Setor | Linguagem |
|---|---|---|---|
| `itau_assist` ⭐ | **Itaú Assist** | Banco — Personnalité | PT-BR |
| `serasa_limpa_nome` ⭐ | **Limpa Nome IA** | Consumer credit — descoberta real-time | PT-BR |
| `serasa_experian` ⭐ | **Serasa Experian** | Consumer credit — Serasa Score + eCred (feature store + motor de decisão) | PT-BR |
| `picpay_assist` ⭐ | **PicPay Assist** | Carteira social — racha, cashback, anti-golpe | PT-BR |
| `bradesco_bia` ⭐ | **BIA** | Banco premium — feature store + next-best-offer | PT-BR |
| `redis_eats` | **Redis Eats** | Food delivery brasileiro | PT-BR |
| `reddash` | Reddash (upstream) | Food delivery genérico | EN |
| `electrohub` | ElectroHub | Eletrônicos | EN |
| `finance-researcher` | ShiftIQ | Research financeiro | EN |
| `healthcare` | RedHealthConnect | Saúde | EN |
| `radish-bank` | Radish Bank | Bank genérico | EN |

Ativo via `DEMO_DOMAIN=<id>` no `.env`. Para alternar entre os domínios BR
localmente use os scripts one-shot (5 fases: preflight → config → setup → dev → health):

```bash
bash scripts/start_itau_demo.sh     # bootstrap Itaú Assist
bash scripts/start_serasa_demo.sh   # bootstrap Limpa Nome IA
bash scripts/start_picpay_demo.sh   # bootstrap PicPay Assist
bash scripts/start_bradesco_demo.sh # bootstrap Bradesco BIA
```

Cada um troca `DEMO_DOMAIN`, ajusta `MEMORY_NAMESPACE` (Memory API exige hyphen),
roda `make setup` e levanta backend+frontend. Não rodam simultaneamente — o `.env`
aponta para um por vez — mas convivem no mesmo codebase sem sujeira cruzada: CSS
scoped via `body.domain-<id>`, namespace de memória isolado (`itau-assist-demo`,
`serasa-limpa-nome-demo`, `picpay-assist-demo`), prefixo Redis distinto
(`itau_assist_*`, `serasa_limpa_nome_*`, `picpay_assist_*`), e cada um cria seu
próprio Context Surface em `make setup` (com stash do anterior em `CTX_SURFACE_ID_<DOMÍNIO>`).

---

## Quick start (local)

### Pré-requisitos

- Python 3.12+ com [`uv`](https://docs.astral.sh/uv/)
- Node 20+ com npm
- Conta Redis Cloud com:
  - Database Redis 8.6+
  - Context Retriever provisionado (admin key)
  - Agent Memory store
  - LangCache cache
- Chave OpenAI

### Setup completo do zero

```bash
# 1. Clone + dependências
git clone <este-repo>
cd redis-iris-demos
make install

# 2. Configuração (preencha as 11 credenciais)
cp .env.example .env
$EDITOR .env

# 3. Subir o domínio Itaú e a app
bash scripts/start_itau_demo.sh
```

`start_itau_demo.sh` (e o irmão `start_serasa_demo.sh`) roda 5 fases, do zero ao validado:

1. **Preflight de infra** — testa Redis (PING + Search), OpenAI, Agent Memory API, LangCache e Context Engine com chamadas reais; falha rápido com diagnóstico por componente
2. **Configuração do `.env`** — `DEMO_DOMAIN`, `MEMORY_NAMESPACE` (Memory API rejeita underscore) e stash do `CTX_SURFACE_ID` do domínio anterior
3. **Setup do zero** — `make setup`: gera modelos, dados sintéticos, cria Context Surface, popula Redis, seed de LTMs e LangCache + validação anti-drift
4. **Backend (8040) + frontend (3040)**
5. **Health check** — espera `/api/health` confirmar o domínio e imprime resumo (app, tools, serviços)

Com tudo já setado, `--skip-setup` pula a fase 3 e sobe em segundos.

Acesse em <http://localhost:3040>.

### Quick reset durante iteração

```bash
bash scripts/reset_itau_light.sh
```

Regen JSONLs + flush seletivo + reload + reseed memórias/cache, **sem** recriar o Context Surface. ~10s vs ~40s do `make setup` full.

### Trocar pra outro domínio (ex: `redis_eats`)

```bash
make setup DOMAIN=redis_eats
make dev
```

---

## Configuração via `.env`

| Variável | Obrigatório | Descrição |
|---|---|---|
| `DEMO_DOMAIN` | sim | Domínio ativo (`itau_assist`, `redis_eats`, …) |
| `OPENAI_API_KEY` | sim | OpenAI |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | sim | Redis Cloud database |
| `REDIS_SSL` | não | `true` se sua database exigir TLS |
| `CTX_ADMIN_KEY` | sim | Admin key do Context Retriever |
| `CTX_SURFACE_ID` | auto | Preenchido pelo `make setup` |
| `MCP_AGENT_KEY` | auto | Preenchido pelo `make setup` |
| `MEMORY_API_BASE_URL` / `MEMORY_STORE_ID` / `MEMORY_API_KEY` | sim | Agent Memory |
| `MEMORY_NAMESPACE` | recomendado | Memory API só aceita `[A-Za-z0-9-]`. Use `itau-assist-demo` (hyphen!) pra `itau_assist`. |
| `LANGCACHE_HOST` / `LANGCACHE_CACHE_ID` / `LANGCACHE_API_KEY` | sim | LangCache |
| `GUARDRAIL_ENABLED` | não | Default `true`. Setar `false` desliga o semantic router. |
| `DEMO_LTM_PERSIST` | não | Default `true` (dev). Setar `false` em prod pública: `remember_customer_detail` ecoa sucesso sem persistir no Memory store compartilhado. |
| `CORS_ORIGIN` | não | Default `http://localhost:3040`. Em prod, `https://seu-dominio.com`. |

Ver `.env.example` na raiz e `deploy/.env.example.prod` pra produção.

---

## Deploy em produção (GCP + Caddy)

Stack pra rodar em VM Linux com Caddy do host servindo HTTPS (Let's Encrypt) +
backend Docker. Sem Redis local — usa Redis Cloud gerenciado.

Documentação completa em [`deploy/README.md`](./deploy/README.md). TL;DR do laptop:

```bash
# 1. DNS: A record  seu-dominio.com  →  <IP-da-VM>
# 2. Caddyfile snippet no host (uma vez só)
gcloud compute scp deploy/Caddyfile.snippet <VM>:/tmp/ --zone <ZONE>
gcloud compute ssh <VM> --zone <ZONE> --command \
  "sudo tee -a /etc/caddy/Caddyfile < /tmp/Caddyfile.snippet && \
   sudo chown -R caddy:caddy /var/log/caddy && \
   sudo systemctl reload caddy"

# 3. .env de prod na VM (uma vez só)
#    Recomendado: DEMO_LTM_PERSIST=false em prod pública.
gcloud compute scp deploy/.env.example.prod <VM>:/tmp/.env.prod --zone <ZONE>
gcloud compute ssh <VM> --zone <ZONE> --command \
  "sudo mkdir -p /opt/iris-bank && sudo mv /tmp/.env.prod /opt/iris-bank/.env && \
   sudo chmod 600 /opt/iris-bank/.env"

# 4. Deploy contínuo (do laptop, qualquer iteração)
bash scripts/deploy_iris_bank.sh
```

O script faz: build do frontend (Vite), gera dados sintéticos, rsync de código +
dist + output pra VM, `docker compose up -d --build`, healthcheck.

### Validação antes de deploy

```bash
make validate
```

Roda `domain.validate()` no domínio ativo. Cobre:

- Schema das entidades íntegro
- Arquivo de logo existe
- Pelo menos um starter prompt definido
- **Anti-drift**: todo `starter_prompts[].prompt` tem match exato em
  `guardrail.routes[].references` (banking ou off_topic). Sem isso, clicar no
  card em produção pode ser bloqueado pelo semantic router.

Build falha se algo estiver inconsistente.

---

## Arquitetura

```
                                 https://irisbank.platformengineer.io
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │   Caddy     │  Let's Encrypt + reverse proxy
                                       └──────┬──────┘
                                              │
                       ┌──────────────────────┼───────────────────────┐
                       │                                              │
                /api/* │                                              │ /*
                       ▼                                              ▼
              ┌────────────────────┐                       ┌────────────────────┐
              │  Backend FastAPI   │                       │  Frontend dist     │
              │  (Docker, :8040)   │                       │  /opt/iris-bank/   │
              └────────┬───────────┘                       │  dist (Vite SPA)   │
                       │                                   └────────────────────┘
                       │
         ┌─────────────┼─────────────┬──────────────┬────────────────┐
         ▼             ▼             ▼              ▼                ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐
   │ OpenAI   │  │  Redis   │  │  Agent   │  │  LangCache │  │ Context  │
   │   API    │  │  Cloud   │  │  Memory  │  │   API      │  │ Surface  │
   └──────────┘  └──────────┘  └──────────┘  └────────────┘  │ admin API│
                                                              └──────────┘
```

Todos os serviços de IA (Memory, LangCache, Context Retriever) são gerenciados
externamente pela Redis. A VM hospeda APENAS o backend FastAPI e o frontend estático.

---

## Demo paths do Itaú Assist

| Card | Pergunta | O que mostra |
|---|---|---|
| **Raio-X do mês** ⭐ | "Faz um diagnóstico do meu mês." | 13 tools encadeadas, panorama financeiro com 2 insights proativos (pontos vencendo + aumento de limite em análise) |
| **Cobrança suspeita** | "Não reconheço uma cobrança de R$ 432 da AMAZON PAY LU." | Agent reconhece padrão recorrente via Agent Memory, sugere NÃO contestar |
| **Próximos pagamentos** | "Quais meus próximos compromissos do mês?" | Faturas abertas + recorrentes |
| **Parcelados na fatura** | "Quais os parcelados na minha fatura esse mês?" | Lista todos os 5 parcelados (paginação 50) + total comprometido futuro |
| **Salvar: assinatura** | "Lembra que AMAZON PAY LU é minha assinatura recorrente." | Write em LTM via `remember_customer_detail` (ephemeral em prod, real em dev) |
| **Salvar: opt-out consignado** | "Anota: não me ofereçam crédito consignado, em hipótese alguma." | Marketing opt-out persistido |
| **Salvar: viagem 1ª classe** | "Lembra que sempre viajo em primeira classe nas internacionais." | Sinalização pra cross-sell de concierge premium |
| **Categoria top** | "Qual minha categoria top em pontos?" | Consulta cruzada Rewards + Transaction |
| **Minha história** | "Há quanto tempo eu sou Personnalité?" | Relationship tenure + tier path |
| **Enviar Pix** | "Manda R$ 200 pro Carlos pelo Pix." | **Tool determinística** `simulate_pix_transfer` — cria Transaction no Surface, retorna protocolo, atualiza saldo |
| **Resgatar pontos** | "Quero resgatar meus pontos vencendo." | Combina Rewards + LTM (categoria preferida) |
| **Política Pix** (cache hit) | "Quais os limites do Pix Itaú?" | LangCache devolve sem chamar LLM |
| **Política contestação** | "Como funciona contestação de cobrança?" | Cache ou policy search |

---

## Estrutura do projeto

```
.
├── backend/                          # FastAPI + LangGraph + serviços Iris
│   └── app/
│       ├── main.py                   # SSE streaming, pipeline 7 fases
│       ├── langgraph_agent.py        # ReAct agent
│       ├── memory_service.py         # Agent Memory client
│       ├── context_surface_service.py
│       ├── guardrail_service.py      # Semantic router (default permissivo)
│       ├── langcache_service.py
│       ├── settings.py               # Pydantic BaseSettings (inclui DEMO_LTM_PERSIST)
│       └── core/
│           ├── domain_contract.py    # DomainPack protocol
│           ├── domain_schema.py      # EntitySpec
│           └── domain_loader.py
│
├── domains/
│   ├── itau_assist/                  # ⭐ Demo bancário Itaú
│   │   ├── schema.py                 # 10 entidades bancárias
│   │   ├── data_generator.py         # Seed PT-BR (5 clientes, 25+ txns, parcelados, disputes…)
│   │   ├── domain.py                 # Branding, guardrail, LTMs, simulate_pix_transfer
│   │   ├── prompt.py                 # System prompt PT-BR sóbrio com workflows
│   │   ├── assets/logo.svg           # Logo placeholder (real via fetch_itau_brand.sh)
│   │   └── docs/
│   ├── redis_eats/                   # Demo de delivery BR com humor Copa
│   ├── reddash/                      # Upstream original
│   ├── electrohub/
│   ├── finance-researcher/
│   ├── healthcare/
│   └── radish-bank/
│
├── frontend/                         # React + Vite
│   ├── src/
│   │   ├── App.tsx                   # Topbar com UserBadge condicional (Itaú)
│   │   ├── components/
│   │   │   ├── UserBadge.tsx         # Avatar redondo + ring verde "online"
│   │   │   ├── BattleCard.tsx        # GitHub + LinkedIn credits
│   │   │   └── ...
│   │   └── styles.css                # Tema base + override `body.domain-itau_assist`
│   ├── public/backgrounds/
│   │   └── itau_assist/              # SVGs geométricos navy+laranja
│   └── .env.production               # DEIXAR VAZIO → URL relativa em prod
│
├── deploy/                           # Pacote pra produção
│   ├── backend/Dockerfile            # Python 3.12 + uv + uvicorn
│   ├── docker-compose.prod.yml       # Só backend (Caddy do host serve dist)
│   ├── Caddyfile.snippet             # Bloco pra apendar no host Caddyfile
│   ├── .env.example.prod             # Template (com DEMO_LTM_PERSIST=false)
│   └── README.md                     # Doc detalhada de deploy
│
├── scripts/
│   ├── start_itau_demo.sh            # Boot one-shot do Itaú em dev local
│   ├── reset_itau_light.sh           # Reseed sem recriar Surface
│   ├── deploy_iris_bank.sh           # Build + rsync + docker up + healthcheck
│   ├── fetch_itau_brand.sh           # Pull do logo oficial via favicon API (opcional)
│   ├── setup_surface.py              # Cria Context Surface no Cloud
│   ├── load_data.py                  # Importa JSONLs no Surface
│   ├── seed_memories.py              # LTM seed (sanitiza domain_id pra Memory API)
│   ├── seed_langcache.py
│   └── ...
│
├── tests/
├── pyproject.toml
├── Makefile
└── UPSTREAM_README.md                # README original do redis/redis-iris-demos
```

---

## Criando um novo domínio

```bash
make create-domain DOMAIN=meu-banco
```

Scaffold em `domains/meu-banco/`. Implemente o protocol `DomainPack` em
`backend/app/core/domain_contract.py`. Skill detalhada em
`.codex/skills/domain-pack-authoring/SKILL.md`.

Use `domains/itau_assist/` como referência — é o exemplo mais completo,
com tool determinística, validador anti-drift, theme custom e suporte a `DEMO_LTM_PERSIST`.

---

## Troubleshooting

| Sintoma | Causa provável | Fix |
|---|---|---|
| Memory API `400 invalid-data: namespace` | Underscore em `MEMORY_NAMESPACE` | Use hyphen: `itau-assist-demo` |
| LangCache `400 attributes: no attributes configured` | Cache foi criado na UI sem attributes | Passe `attributes={}` (dict vazio) no SeedLangCacheEntry — o service skipa |
| Pergunta nova bloqueada por guardrail | Starter prompt sem match no `guardrail.references` | `make validate` aponta. Adicione o texto ao `references`. |
| Frontend hitando outro backend em prod | `VITE_API_BASE_URL` cravado em `frontend/.env.production` | Deixe **vazio** pra URL relativa. Build + redeploy. |
| Caddy `irisbank.log: permission denied` em loop | `/var/log/caddy/` sem write pro user `caddy` | `sudo chown -R caddy:caddy /var/log/caddy && sudo systemctl restart caddy` |
| Tool chain trunca em 10 itens | Default da MCP é `limit=10`. Agent não pagina. | Prompt do agent foi atualizado pra exigir `limit=50` em queries de listagem. |
| Container backend `docker compose: unknown command` | Docker v1 sem o plugin `compose` v2 | `sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/libexec/docker/cli-plugins/docker-compose && sudo chmod +x` |

---

## Crédito ao upstream

Este fork é baseado em [`redis/redis-iris-demos`](https://github.com/redis/redis-iris-demos),
o framework de demos multi-domínio do Redis Iris. O README original do upstream
está preservado em [`UPSTREAM_README.md`](./UPSTREAM_README.md).

Domínios `reddash`, `electrohub`, `finance-researcher`, `healthcare` e `radish-bank`
são do upstream. Os domínios `itau_assist` e `redis_eats` são contribuições deste fork.

## Aviso de uso de marca

Esta é uma demo **interna** de Redis SAs. Não tem afiliação oficial com Itaú
Unibanco S.A. — todos os dados são fictícios, e o uso de assets visuais oficiais
do Itaú depende de autorização do operador (script `scripts/fetch_itau_brand.sh`
fica desabilitado por padrão). Use com responsabilidade.

---

**Autor do fork:** Gabriel Cerioni · [GitHub](https://github.com/gacerioni) · [LinkedIn](https://www.linkedin.com/in/gabrielcerioni)

Licença: MIT (herdada do upstream).
