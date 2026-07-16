# Roteiro de demo: Token Control Plane (Redis como rate limiter de LLM)

> Redis no caminho de cada request de IA: roteador semântico, cache semântico e
> token bucket por área. O pitch: controlar custo de inferência por time, em tempo real.
> Antes: `bash scripts/start_token_gateway.sh`, abrir http://localhost:8050.
> Serviço standalone na porta 8050, isolado do chat (8040). Não tem seed: as áreas
> são config (`backend/app/gateway/config.py`) e as keys `tcp:*` nascem sob demanda.

---

## A ideia

Três times compartilham o mesmo modelo (gpt-5.4-mini), cada um com um orçamento de
tokens (balde). Toda pergunta passa por um gauntlet no Redis antes de chegar (ou não)
no LLM:

| Etapa | O que o Redis faz | Efeito no custo |
|---|---|---|
| 1. Roteador semântico | classifica on-topic vs off-topic | off-topic morre aqui, **zero token** |
| 2. Cache semântico | pergunta repetida volta do cache | repeticão **zero token** |
| 3. Token bucket por área | debita o orçamento da área | throttle quando o balde esvazia |
| 4. LLM | só o que sobrou gera de verdade | gasto real, previsível |

Áreas (baldes, números do cliente):

| Área | Capacidade | Cor |
|---|---|---|
| Cartões | 300 | laranja |
| Investimentos | 600 | verde |
| Canais Digitais | 900 | azul |

---

## Beats

### Beat 1: Off-topic morre no roteador (economia 100%)
**Ação:** na área **Cartões**, manda `Me conta uma piada`.
**O que acontece:** o roteador classifica como off_topic e **bloqueia antes do LLM**.
**Olhar no painel:** o request conta como `blocked`, `spent` não mexe e o `saved_router`
sobe (~265 tokens que NÃO foram gastos). O balde de Cartões nem é debitado.
**Fala:** "Troll, off-topic, conteúdo nocivo e prompt injection nem chegam no modelo.
O roteador roda no Redis, antes de qualquer inferência. Isso é custo que você corta na origem."

### Beat 2: Pergunta nova gasta token (uma vez)
**Ação:** na área **Investimentos**, manda `Qual a diferença entre CDB e LCI?`.
**O que acontece:** passa o roteador, dá MISS no cache, debita o balde e o LLM responde.
**Olhar no painel:** `answered` sobe, `spent` reflete os tokens reais (~234), o balde de
Investimentos cai e começa a recarregar (refill por segundo).

### Beat 3: Mesma pergunta de novo bate no cache (economia 100%)
**Ação:** repete `Qual a diferença entre CDB e LCI?` em Investimentos.
**O que acontece:** HIT no cache semântico, resposta instantânea, **zero token de LLM**.
**Olhar no painel:** `cached` sobe e `saved_cache` cresce (~271 tokens economizados).
**Fala:** "Em escala, a fração de perguntas repetidas servidas do cache vira economia direta."

### Beat 4: Estoura o balde (rate limit por área)
**Ação:** dispara várias perguntas novas seguidas na mesma área até `remaining` chegar a zero.
**O que acontece:** o token bucket recusa (throttle) até recarregar. Cada área tem o seu
orçamento, isoladas entre si: Cartões estourar não afeta Investimentos.
**Olhar no painel:** `throttled` sobe, o gauge da área zera e recarrega no ritmo do refill.
**Bônus:** troque a estratégia pra `sliding_window` no painel e mostre o teto por janela.

---

## Fechamento
"Um único Redis no caminho de cada request de IA: roteador semântico que corta o que nem
devia chegar no modelo, cache semântico que serve o repetido de graça, e token bucket que
dá orçamento por time em tempo real. Menos custo de inferência, controle por área, e
visibilidade do que foi gasto, bloqueado, cacheado e economizado. É o Redis como plano de
controle de tokens de LLM."

## Mapa rápido (cola)
| Beat | Área | Prompt | Resultado | Contador |
|---|---|---|---|---|
| 1 | Cartões | Me conta uma piada | bloqueado no roteador | blocked, saved_router |
| 2 | Investimentos | Qual a diferença entre CDB e LCI? | LLM responde | answered, spent |
| 3 | Investimentos | (repete o de cima) | cache HIT | cached, saved_cache |
| 4 | qualquer | rajada de perguntas novas | throttle do balde | throttled |

## Notas de produção
- Subir: `bash scripts/start_token_gateway.sh` (preflight + uvicorn :8050 + health).
- Reset entre demos: `POST http://localhost:8050/api/gateway/reset` (zera só as keys `tcp:*`,
  não encosta em domínio nenhum). O painel tem botão de reset.
- Tuning ao vivo: `POST /api/gateway/config` muda estratégia (token_bucket/sliding_window),
  capacidade e refill por área, sem reiniciar.
- Modelo: gpt-5.4-mini, `MAX_OUTPUT_TOKENS=200` pra resposta concisa e custo previsível.
- Guardrail do gateway agora cobre off-topic + conhecimento + nocivo + prompt injection,
  igual aos 4 demos bancários (consistência de roteador no repo inteiro).
