# Roteiro de demo: StrideLane (retail hybrid search, asset global brandless)

> A demo oficial de retail search da Redis. Loja esportiva brandless (sem marca real),
> EN-US, mostrando o Redis brilhando em busca hybrid: BM25 text + vector + geo + rating,
> fundidos ao vivo, com painel de métricas e sliders de peso.
> Subir: `bash scripts/start_stridelane_storefront.sh` e abrir http://localhost:8060.
> Standalone na porta 8060, aditivo e namespaced (`stridelane_*`), não encosta em nenhum
> outro demo nem dá flush no Redis.

---

## A história
Um shopper procura produtos por necessidade (não por palavra-chave exata), vê o ranking
hybrid se formar com o porquê de cada item, brinca com os pesos e vê re-rankear na hora,
filtra por facets, e adiciona ao carrinho. Tudo sobre um Redis: índice de produto com
vector + geo + text + numeric, autocomplete e synonyms.

## Beat 1: busca semântica (o abridor matador)
**Ação:** digite `something to keep me warm on a chilly run`.
**O que acontece:** o #1 é **Boreal Thermal Run Layer**, um produto que NÃO tem as palavras
"warm", "chilly" nem "run" no texto. Subiu por **similaridade vetorial** (embedding da query
no servidor + KNN no Redis). O painel "why it ranked" mostra o vetor dominando o score.
**Fala:** "Busca por significado, não por palavra-chave. O Redis embeda a intenção e acha o
produto certo mesmo sem nenhum match lexical. FTS puro não pegaria isso."

## Beat 2: os pesos do hybrid (o controle que encanta)
**Ação:** arraste **Vector** pra cima (0.90) e **Text** pra baixo (0.05). Depois inverta.
**O que acontece:** os resultados re-rankeiam ao vivo e o breakdown do top vira ~92% vector.
Com text alto, matches de palavra-chave sobem; com vector alto, vizinhos semânticos sobem.
**Fala:** "Um único FT.AGGREGATE no Redis traz os candidatos por vetor + filtro + geo, e a
gente funde os sinais com pesos ajustáveis. O cliente vê o ranking mudar na hora, sem reindex."

## Beat 3: typo e synonyms (recall)
**Ação:** comece a digitar `kinetc` (com erro). O autocomplete FUZZY sugere "Kinetic Nine".
Busque `teal trainer` (ou `tenis`, via grupo de synonyms PT). 
**O que acontece:** `FT.SUGGET FUZZY` tolera o erro de digitação; `FT.SYNUPDATE` faz tenis/
sneaker/calcado caírem no mesmo match.
**Fala:** "Autocomplete tolerante a erro e synonyms de varejo, tudo nativo no Redis. Em PT,
digite 'tenis' e veja resolver, o engine é o mesmo."

## Beat 4: geo (entrega mais perto rankeia melhor)
**Ação:** mantenha "Rank by nearest store" ligado e busque `trail running shoe`.
**O que acontece:** o **Strideworks Trail Grip 2 (flagship exclusive)** ganha boost de geo
(dist 0 km, estocado na flagship Paulista) e sobe. O painel mostra a contribuição "geo".
**Fala:** "O Redis guarda a coordenada da loja que estoca o produto e calcula a distância
(geodistance) no mesmo aggregate. Mais perto, entrega mais rápida, rankeia melhor."

## Beat 5: facets + carrinho
**Ação:** clique numa categoria/cor à esquerda (contagens vêm de FT.AGGREGATE GROUPBY).
Adicione um produto ao carrinho.
**O que acontece:** os facets filtram o conjunto (TAG/NUMERIC), e o carrinho (RedisJSON)
recomputa total no servidor.
**Fala:** "Facets, sessão e carrinho, tudo no Redis. O total é computado no servidor, não no
cliente. É a base de uma jornada de compra inteira sobre uma única engine."

---

## Mapa rápido (cola)
| Beat | Ação | Pilar | Olhar |
|---|---|---|---|
| 1 | "something to keep me warm on a chilly run" | Vector search | #1 sem keyword, breakdown vector |
| 2 | arrastar Vector/Text | Hybrid weights | re-rank ao vivo + breakdown |
| 3 | "kinetc" / "teal trainer" / "tenis" | Autocomplete FUZZY + synonyms | dropdown + recall |
| 4 | "trail running shoe" (geo on) | Geo ranking | flagship exclusive sobe, dist 0 km |
| 5 | facet + add to cart | Facets + cart RedisJSON | contagens + total server-side |

## Notas de produção
- Engine compartilhado: `backend/app/hybrid_search.py`. A vitrine e (no roadmap) o concierge
  chamam a MESMA função, então catálogo navegável e resposta do agente nunca divergem.
- Índice backend-owned `stridelane_product_idx` (ON JSON): vector HNSW 1536 cosine + GEO +
  TEXT + TAG + NUMERIC. A SDK do Context Surfaces não indexa GEO, por isso o índice é nosso.
- Reset/regen: `bash scripts/start_stridelane_storefront.sh --regen` regenera o catálogo
  (embeddings + datas frescas) e recarrega. Sem flush do DB, só chaves `stridelane_*`.
- Métricas reais no painel: latência no Redis, candidatos varridos, re-rank, embedding ms.
- Próximo (roadmap, fora do primeiro corte): superfície de concierge (chat IRIS retail) com
  handoff "talk to an agent" carregando a sessão, e CRUD de carrinho via LLM (já implementado
  em `domain.py` + `cart_service.py`, falta o setup da Context Surface + a integração no React).
