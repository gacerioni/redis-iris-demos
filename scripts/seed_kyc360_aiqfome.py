"""Seed the aiqfome KYC "perfil de fome 360" + semantic slice index.

Same architecture as the Itaú/BS2 customer-360: one rich JSON document
(macrocategoria -> colecao -> categoria/valor/justificativa/confianca)
describing the FOMINHA, stored as:

  - one RedisJSON doc:   aiqfome:kyc360:CUST_DEMO_001
  - one hash per slice:  aiqfome:kyc360_chunk:<customer>:<categoria>
  - one vector index:    aiqfome_kyc360_idx

The agent tool `get_customer_profile_slice` embeds the topic and returns ONLY
the matching slices; token economy lands in the FinOps panel.

Usage:
    DEMO_DOMAIN=aiqfome uv run python -m scripts.seed_kyc360_aiqfome
"""

from __future__ import annotations

import json
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings

CUSTOMER_ID = "CUST_DEMO_001"
DOC_KEY = f"aiqfome:kyc360:{CUSTOMER_ID}"
CHUNK_PREFIX = "aiqfome:kyc360_chunk:"
INDEX_NAME = "aiqfome_kyc360_idx"

KYC360_DOC: dict = {
    "identificadorPessoa": CUSTOMER_ID,
    "resumo": (
        "Gabriel Cerioni, fominha de Maringá-PR desde abril de 2019: 214 pedidos, LTV de "
        "R$ 4.980 em 12 meses, ticket médio de R$ 67,40, assinante do clube aiqfome. "
        "Apaixonado por comida japonesa (temaki de salmão é o xodó), tradição de pizza "
        "às sextas com a filha Sofia, ALÉRGICO A CAMARÃO. Histórico impecável: 0,9% de "
        "reembolso e score de fraude baixíssimo."
    ),
    "estrategia": (
        "Cliente de altíssimo valor e confiança: aprovação instantânea em reembolsos, "
        "recomendações ancoradas em japonesa + pizza de sexta, nunca ofertar itens com "
        "camarão sem alerta, e usar o voucher ativo como gatilho de recompra."
    ),
    "colecoes": [
        {
            "macrocategoria": "perfil_gastronomico",
            "colecao": [
                {
                    "categoria": "cozinha_favorita",
                    "valor": "Comida japonesa é a cozinha favorita declarada e comprovada por comportamento.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "9 dos 23 pedidos dos últimos 90 dias foram de japonesa, com destaque pro "
                        "Temaki do Tio. O temaki de salmão com cream cheese é o item mais repetido "
                        "do histórico (o xodó declarado do Gabriel)."
                    ),
                    "origem": "comportamento;memoria_relacionamento",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "doces_e_bebidas",
                    "valor": "Sobremesa favorita: açaí com adicionais. Bebida recorrente: guaraná lata.",
                    "indiceConfianca": 0.85,
                    "justificativa": (
                        "Pedidos recorrentes no Açaí do Ponto e guaraná presente em quase todo combo "
                        "de lanche. Em dia de jogo do Palmeiras o padrão é lanche + refri gelado."
                    ),
                    "origem": "comportamento",
                    "data": "2026-07-10T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "restricoes_alimentares",
            "colecao": [
                {
                    "categoria": "alergia_camarao",
                    "valor": "ALERGIA A CAMARÃO declarada. Nunca sugerir nem adicionar itens com camarão sem alerta.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Registrada pelo próprio fominha no relacionamento. Regra de segurança: "
                        "qualquer prato com alérgeno 'camarao' exige alerta explícito e sugestão de "
                        "alternativa; adição silenciosa ao carrinho é proibida."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-01T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "outras_restricoes",
                    "valor": "Sem outras restrições: come glúten, lactose e carne normalmente.",
                    "indiceConfianca": 0.9,
                    "justificativa": "Histórico variado inclui massas, pizzas, burgers e churrasco sem ressalvas.",
                    "origem": "comportamento",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "tradicoes_e_momentos",
            "colecao": [
                {
                    "categoria": "tradicao_sexta_pizza",
                    "valor": "Sexta à noite é dia de pizza com a filha Sofia (tradição da família).",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "3 pedidos recentes na Pizzaria Forno da Vila, todos em sextas entre 19h e "
                        "21h. Declarado pelo Gabriel como programa fixo com a Sofia."
                    ),
                    "origem": "comportamento;memoria_relacionamento",
                    "data": "2026-07-10T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "dia_de_jogo",
                    "valor": "Palmeirense: em dia de jogo o padrão é combo de lanche + refri gelado.",
                    "indiceConfianca": 0.85,
                    "justificativa": (
                        "Pedidos no Burger do Zé coincidem com datas de jogos do Palmeiras; preferência "
                        "declarada no relacionamento."
                    ),
                    "origem": "comportamento;memoria_relacionamento",
                    "data": "2026-07-08T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "almoco_util",
                    "valor": "Em dia útil, marmita caseira ocasional no almoço (Marmitaria da Vó Cida).",
                    "indiceConfianca": 0.8,
                    "justificativa": "Pedidos de marmita concentrados entre 11h30 e 13h em dias de semana.",
                    "origem": "comportamento",
                    "data": "2026-07-09T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "comportamento_de_pedidos",
            "colecao": [
                {
                    "categoria": "frequencia_e_ticket",
                    "valor": "23 pedidos nos últimos 90 dias com ticket médio de R$ 67,40.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Dados sistêmicos do painel do fominha: frequência ~2 pedidos/semana, pico "
                        "às sextas à noite, pagamento preferencial via Pix."
                    ),
                    "origem": "adquirencia_dados",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "endereco_padrao",
                    "valor": "Entrega padrão na Rua Néo Alves Martins, 2810 - Zona 01, Maringá-PR.",
                    "indiceConfianca": 1.0,
                    "justificativa": "Endereço usado em 96% dos pedidos dos últimos 12 meses.",
                    "origem": "cadastro",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "fidelidade_e_valor",
            "colecao": [
                {
                    "categoria": "valor_do_cliente",
                    "valor": "Fominha desde 2019-04: 214 pedidos e LTV de R$ 4.980 em 12 meses.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Assinante do clube aiqfome (frete grátis nos parceiros). Um dos perfis de "
                        "maior valor da praça de Maringá."
                    ),
                    "origem": "adquirencia_dados",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "confianca_e_risco",
                    "valor": "Histórico impecável: refund rate de 0,9% e score de fraude 0,03.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "1 único reembolso em 14 meses (item errado, 2025-05, aprovado). Perfil de "
                        "confiança máxima: reembolsos com aprovação instantânea, sem verificação."
                    ),
                    "origem": "modelo_risco",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "elegibilidade_e_ofertas",
            "colecao": [
                {
                    "categoria": "voucher_ativo",
                    "valor": "Voucher de R$ 15,00 ativo (fidelidade clube aiqfome), validade 31/07/2026.",
                    "indiceConfianca": 1.0,
                    "justificativa": "Crédito de fidelidade emitido pelo clube aiqfome; aplicável em qualquer parceiro.",
                    "origem": "campanhas",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "propensao_campanhas",
                    "valor": "Alta propensão a campanhas de japonesa (qualquer dia) e pizza (sextas).",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Modelo de recomendação: cozinha_favorita=japonesa e dia_pico=sexta com "
                        "tradição familiar tornam esses os gatilhos de maior conversão."
                    ),
                    "origem": "modelo_nbo",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "interacoes_de_atendimento",
            "colecao": [
                {
                    "categoria": "resumo_cliente",
                    "valor": (
                        "Fominha premium de Maringá: 7 anos de casa, 214 pedidos, japonesa no topo, "
                        "pizza de sexta com a Sofia, alérgico a camarão, clube aiqfome ativo, "
                        "voucher de R$ 15 na carteira e confiança máxima no modelo de risco."
                    ),
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Consolidação de comportamento, cadastro, campanhas, modelo de risco e "
                        "memórias de relacionamento de 2019-2026."
                    ),
                    "origem": "comportamento;cadastro;campanhas;modelo_risco;memoria_relacionamento",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
    ],
}


def _chunk_text(macro: str, item: dict) -> str:
    return f"[{macro}/{item['categoria']}] {item['valor']} Evidência: {item['justificativa']}"


def main() -> None:
    settings = get_settings()
    if settings.demo_domain != "aiqfome":
        print(f"DEMO_DOMAIN={settings.demo_domain}; this seeder targets aiqfome only. Aborting.")
        return

    client = create_redis_client(settings)
    openai_client = OpenAI(
        api_key=settings.openai_api_key,
        **({"base_url": settings.openai_base_url} if settings.openai_base_url else {}),
    )

    client.execute_command("JSON.SET", DOC_KEY, "$", json.dumps(KYC360_DOC, ensure_ascii=False))
    doc_bytes = int(client.execute_command("MEMORY", "USAGE", DOC_KEY) or 0)
    print(f"[1/3] {DOC_KEY} written ({doc_bytes} bytes in Redis)")

    chunks: list[tuple[str, str, str]] = []
    for grupo in KYC360_DOC["colecoes"]:
        macro = grupo["macrocategoria"]
        for item in grupo["colecao"]:
            chunks.append((macro, item["categoria"], _chunk_text(macro, item)))

    resp = openai_client.embeddings.create(
        input=[text for _, _, text in chunks],
        model=settings.openai_embedding_model,
    )
    dim = len(resp.data[0].embedding)

    total_chunk_bytes = 0
    for (macro, categoria, text), emb in zip(chunks, resp.data):
        key = f"{CHUNK_PREFIX}{CUSTOMER_ID}:{categoria}"
        client.hset(
            key,
            mapping={
                "customer_id": CUSTOMER_ID,
                "macrocategoria": macro,
                "categoria": categoria,
                "text": text,
            },
        )
        client.execute_command("HSET", key, "embedding", array("f", emb.embedding).tobytes())
        total_chunk_bytes += int(client.execute_command("MEMORY", "USAGE", key) or 0)
    print(f"[2/3] {len(chunks)} slices embedded (dim={dim}) — {total_chunk_bytes} bytes total, "
          f"~{total_chunk_bytes // len(chunks)} bytes/slice")

    try:
        client.execute_command("FT.DROPINDEX", INDEX_NAME)
    except Exception:
        pass
    client.execute_command(
        "FT.CREATE", INDEX_NAME,
        "ON", "HASH",
        "PREFIX", "1", CHUNK_PREFIX,
        "SCHEMA",
        "customer_id", "TAG",
        "macrocategoria", "TAG",
        "categoria", "TAG",
        "text", "TEXT",
        "embedding", "VECTOR", "FLAT", "6",
        "TYPE", "FLOAT32", "DIM", str(dim), "DISTANCE_METRIC", "COSINE",
    )
    print(f"[3/3] Index {INDEX_NAME} created (FLAT, COSINE, dim={dim})")
    print("Done.")


if __name__ == "__main__":
    main()
