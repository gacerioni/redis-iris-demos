# Roteiro de demo: Serasa Experian (Inteligência de Crédito sobre Redis)

> Demo Redis Iris. Diferencial nativo: a Serasa **é** uma empresa de score, então o
> **feature store de crédito no Redis** não é metáfora, é o produto. O clímax é o
> **score cruzando de Bom pra Excelente ao vivo** (recompute-on-write), destravando uma oferta.
> Antes: subir o domínio (`DEMO_DOMAIN=serasa_experian`, `make setup`, backend :8040, front :3040).
> Persona: Gabriel Cerioni, Serasa Premium Plus, score 692 (Bom), a 9 pontos de Excelente.
> Reset entre demos: `bash scripts/reset_serasa_experian_light.sh`.

Validado e2e (jun/2026): 13 tools internas + 106 tools totais (sob o teto de 128 da API),
guardrail/cache/memory ON, todos os beats abaixo rodando ao vivo.

---

## Talking track (single flow) — 🎤 fala · ⌨️ digita

**🎤 Abertura**
"Pessoal, isso aqui é o assistente do Serasa Experian, rodando 100% sobre Redis. E tem uma
sacada: a Serasa é, no fundo, uma empresa de score e risco de crédito. Então o feature store
no Redis aqui não é analogia, é o coração do produto. Eu sou o Gabriel, consumidor, e vou só
viver o meu dia. Olhem o painel: é o Redis trabalhando embaixo de cada resposta."

**🎤 Situação (Context Surfaces, dado operacional vivo)**
**⌨️** `Como tá minha situação no Serasa?`
**🎤** "Repara: ele não chutou. Puxou meu perfil, dívidas, pendências, consultas ao CPF e
alertas, tudo lido do Redis na hora. Score 692, faixa Bom, Premium Plus, Cadastro Positivo ativo.
Esse é o raio-X operacional, contexto de verdade."

**🎤 Explicar o score (Feature Store, o diferencial nativo do bureau)**
**⌨️** `Por que meu score tá em 692 e o que segura ele de chegar em excelente?`
**🎤** "Olha que bonito. Ele leu as minhas features no feature store do Redis em uns 30 a 40 ms
e decompôs os meus 692 pontos pelos 6 pesos oficiais do Serasa Score: Cadastro Positivo 29%,
experiência de mercado 24%, dívidas 21%, e por aí vai. E me disse exatamente o que mais segura
a subida: dívidas e busca de crédito. Isso é explicabilidade nativa, o modelo lendo features
online no Redis na hora da pergunta."

**🎤 eCred (Feature Store + motor de decisão + write-back)**
**⌨️** `Tem alguma oferta de crédito boa pra mim agora?`
**🎤** "Ele releu o feature store e rodou o motor do eCred sobre o catálogo de parceiros.
Reparem em duas coisas: primeiro, ele respeitou a minha preferência, sabe que eu topo cartão
mas não quero empréstimo nem consignado, isso veio da memória. Segundo, o melhor match é o
**PagBank Cartão Sem Anuidade**, com 76% de chance de aprovação e fit 83%, e ele já escreveu esse
match de volta no Redis. E tem o **Nubank Ultravioleta** ali que fica TRAVADO, porque exige faixa
Excelente. Guardem esse cartão travado."

**🎤 O clímax: recompute-on-write + band-change (o WOW)**
**⌨️** `Se eu quitar a dívida negativada da Riachuelo, meu score sobe? Recalcula e me mostra.`
**🎤** "Esse é o momento. Ele recomputou o score AO VIVO, na escrita: quitar a Riachuelo sobe a
feature de dívidas, o modelo recalcula sobre os 6 pesos, e o score vai de 692 pra 738. Eu
**cruzei de Bom pra Excelente** na frente de vocês. Feature store online, recompute na
escrita e mudança de faixa, tudo no mesmo Redis, em tempo real."

**🎤 O payoff: a oferta premium destrava e vira o #1 (peça pra re-rodar o eCred)**
**⌨️** `E agora que subi pra Excelente, qual a melhor oferta pra mim?`
**🎤** "Aqui fecha o ciclo. Ele releu o feature store, já em Excelente, e rodou o eCred de novo.
Lembram do **Nubank Ultravioleta** que estava TRAVADO porque exigia Excelente? Agora ele
**destravou e virou o meu melhor match**, na frente do cartão de antes. O score subiu, e na mesma
hora uma oferta premium que estava bloqueada abriu e foi pro topo da minha lista. É o feature
store fechando o loop: explica o score, recompõe a faixa e libera a oferta certa, ao vivo."

**🎤 Proteção / Antifraude (o beat emocional, Context Surfaces + LTM)**
**⌨️** `Meu CPF apareceu em algum vazamento? Tem alerta de fraude pra mim?`
**🎤** "Aqui pega no emocional. Ele leu os meus alertas no Redis e achou dois: uma consulta
suspeita às 3h27 da madrugada, sem autorização, e o meu CPF numa lista vazada na Dark Web,
com e-mail junto. E como ele sabe, pela memória, que eu sou Premium e ligo pra segurança, ele
já amarra no valor da proteção que eu pago. Isso é o Serasa fazendo o que ele faz de melhor,
proteger o CPF, com o Redis guardando contexto, alerta e memória no mesmo lugar."

**🎤 RAG com Vector Search**
**⌨️** `Como funciona o monitoramento de CPF do Serasa?`
**🎤** "Resposta aterrada na política, via busca vetorial no Redis. A pergunta vira embedding e
acha o documento por significado, não por palavra-chave. Sem alucinação."

**🎤 Semantic Cache**
**⌨️** `Como funciona o Serasa Score?`
**🎤** "Reparem na velocidade. Essa é uma pergunta que todo mundo faz, então veio do cache
semântico, sem chamar o modelo. Pergunta recorrente, custo zero de LLM. Em escala, isso é dinheiro."

**🎤 Guardrail / Semantic Routing**
**⌨️** `Me conta uma piada.`
**🎤** "Barrado. O roteador semântico no Redis decide o que vale a pena antes de gastar um token.
Off-topic, troll, até prompt injection morrem aqui na porta. E o que é legítimo passa."

**🎤 Fechamento**
"Um único Redis sustentando tudo: contexto operacional, memória de curto e longo prazo, cache
semântico, RAG vetorial, guardrail e o feature store de crédito que explica o score, ranqueia
oferta e recompõe a faixa ao vivo. Pra uma empresa que é feita de score e risco, isso não é
infra de apoio, é o produto. O Iris orquestra, o Redis é a fundação."

---

## Sequência de prompts (cola rápida)
1. `Como tá minha situação no Serasa?`
2. `Por que meu score tá em 692 e o que segura ele de chegar em excelente?`
3. `Tem alguma oferta de crédito boa pra mim agora?`
4. `Se eu quitar a dívida negativada da Riachuelo, meu score sobe? Recalcula e me mostra.`
5. `E agora que subi pra Excelente, qual a melhor oferta pra mim?`
6. `Meu CPF apareceu em algum vazamento? Tem alerta de fraude pra mim?`
7. `Como funciona o monitoramento de CPF do Serasa?`
8. `Como funciona o Serasa Score?`
9. `Me conta uma piada.`

Dica de ritmo: os beats 2 a 5 são o coração (feature store). Os beats 4 e 5 são o clímax em par,
desacelere: o beat 4 cruza a faixa (`simulate_score_recompute` 692 -> 738, aponte a faixa virando
e o `feature_fetch_ms`), e o beat 5 é o payoff (re-rodar o eCred mostra o **Nubank Ultravioleta**
destravando e indo pro topo da lista). Depois do recompute o demo fica "sujo" (score 738),
então rode `reset_serasa_experian_light.sh` pra
voltar pro 692 antes da próxima apresentação.

## Mapa rápido (cola)
| # | Prompt | Pilar | Tool no painel |
|---|---|---|---|
| 1 | Como tá minha situação no Serasa? | Context Surfaces | filter_* + get_consumer_by_id |
| 2 | Por que meu score tá em 692? | Feature Store (explica score) | explain_credit_score + feature_fetch_ms |
| 3 | Tem oferta de crédito boa pra mim? | Feature Store (decisão eCred + write-back) | rank_ecred_offers |
| 4 | Se eu quitar a Riachuelo, meu score sobe? | Feature Store (recompute + band-change) | simulate_score_recompute (692 -> 738) |
| 5 | E agora, qual a melhor oferta pra mim? | Feature Store (payoff: oferta premium destrava e vira #1) | rank_ecred_offers (Nubank Ultravioleta desbloqueia) |
| 6 | Meu CPF apareceu em algum vazamento? | Proteção / Antifraude (Context + LTM) | filter_fraudalert + search_customer_memory |
| 7 | Como funciona o monitoramento de CPF? | RAG Vector Search | search_policies_semantic |
| 8 | Como funciona o Serasa Score? | LangCache | semantic_cache_search (HIT) |
| 9 | Me conta uma piada. | Guardrail | guardrail_check (Blocked) |

## Notas de produção
- **Feature store:** `serasa_experian_features:{consumer_id}` (JSON, lido por _read_json em ~30-70 ms
  via Redis Cloud). Os 6 f_* mapeiam os 6 pesos oficiais do Serasa Score (29/24/21/12/8/6).
- **eCred:** catálogo `CreditOffer` (8 ofertas) varrido pelo `rank_ecred_offers`; respeita opt-outs
  da LTM; escreve o `OfferMatch` de volta no Surface. Catálogo de 12 ofertas de marcas reais
  (Nubank, PagBank, C6, Will Bank, Mercado Pago, Caixa...); o Nubank Ultravioleta é gated em Excelente.
  Seed rico: 12 consultas ao CPF de marcas reais (anomalia FastCash 03:27), Cadastro Positivo
  (Enel/Vivo/Netflix/financiamento em dia), score history de 13 meses, vazamento Dark Web de 12,8M
  amarrado na consulta da FastCash.
- **Recompute:** `simulate_score_recompute` muda f_dividas (quitar a Riachuelo, R$ 847,50) e
  re-deriva o score on-write: 692 (Bom) -> 738 (Excelente), band_change. É o clímax.
- **Datas sempre frescas (anti-staleness):** seed usa datas relativas; reset_light regenera pro dia.
- **Coexistência:** domínio isolado (prefixo serasa_experian_, router serasa-experian-guardrails,
  memory serasa-experian-demo). Convive com serasa_limpa_nome e os outros sem colidir.
- **Logo:** placeholder magenta no ar; pro logo oficial, operador roda `scripts/fetch_serasa_experian_brand.sh`.
