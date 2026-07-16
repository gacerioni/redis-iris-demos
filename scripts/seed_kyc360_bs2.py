"""Seed the BS2 Pay KYC business-360 ("momento do negócio") + semantic slice index.

Same architecture as the Itaú customer-360 (scripts/seed_kyc360.py), adapted to
the merchant/acquiring world: a DynamoDB-style document (macrocategoria ->
colecao -> categoria/valor/justificativa/confianca) describing the MERCHANT,
stored as:

  - one RedisJSON doc:   bs2_adiq:kyc360:MERCH_DEMO_001   (the full 360)
  - one hash per slice:  bs2_adiq:kyc360_chunk:<merchant>:<categoria>
  - one vector index:    bs2_adiq_kyc360_idx (KNN over the slices)

The agent tool `get_customer_profile_slice` embeds the topic and returns ONLY
the matching slices; token economy lands in the FinOps panel.

Usage:
    DEMO_DOMAIN=bs2_adiq uv run python -m scripts.seed_kyc360_bs2
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

MERCHANT_ID = "MERCH_DEMO_001"
DOC_KEY = f"bs2_adiq:kyc360:{MERCHANT_ID}"
CHUNK_PREFIX = "bs2_adiq:kyc360_chunk:"
INDEX_NAME = "bs2_adiq_kyc360_idx"

# Persona-consistent with the bs2_adiq seed: Cerioni Sports, plano Adiq Pro,
# conta PJ BS2, agenda de recebíveis, Black Friday storyline.
KYC360_DOC: dict = {
    "identificadorPessoa": MERCHANT_ID,
    "resumo": (
        "Cerioni Sports, comércio de artigos esportivos (e-commerce + 2 lojas + quiosque, "
        "São Paulo), credenciado Adiq desde 2020 no plano Adiq Pro e cliente BS2 Empresas. "
        "Vendas de R$ 412.800/mês em crescimento de 8% m/m, agenda líquida de R$ 287.450 "
        "em 30 dias, chargeback baixíssimo (0,4%) e sazonalidade forte na Black Friday. "
        "Planeja filial em Campinas."
    ),
    "estrategia": (
        "Priorizar antecipação de recebíveis pré-Black Friday (evitar repetir a falta de "
        "estoque de 2025), estruturar a filial de Campinas (POS extra + conta da filial) e "
        "posicionar capital de giro BS2 como colchão pós-pico."
    ),
    "colecoes": [
        {
            "macrocategoria": "perfil_e_operacao",
            "colecao": [
                {
                    "categoria": "operacao_canais",
                    "valor": "Operação multicanal: e-commerce dominante com lojas físicas complementares.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Mix de vendas do ciclo: e-commerce ~55% (gateway Adiq) e POS ~45% "
                        "(Loja Itaim, Loja Morumbi e Quiosque Shopping Vila Lobos). 1.086 transações "
                        "no mês, ticket médio de R$ 380,00."
                    ),
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "operacao_mix_pagamento",
                    "valor": "Mix de recebimento concentrado em crédito, com Pix crescendo.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Crédito 62% (à vista 40%, parcelado 22%), débito 23% e Pix 15% das vendas "
                        "de R$ 412.800,00 do ciclo atual. Parcelado relevante puxa a agenda pra "
                        "frente (D+30 por parcela)."
                    ),
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "operacao_terminais",
                    "valor": "3 terminais ativos, 1 com instabilidade de conectividade em acompanhamento.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "POS Smart nas lojas Itaim e Morumbi (estáveis) e POS Mini no Quiosque "
                        "Shopping Vila Lobos com chip 4G oscilando; chamado de troca de chip em "
                        "andamento com previsão de 2 dias úteis."
                    ),
                    "origem": "suporte",
                    "data": "2026-07-10T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "comportamento_de_vendas",
            "colecao": [
                {
                    "categoria": "vendas_tendencia",
                    "valor": "Crescimento consistente de 8% mês a mês, sem sinal de desaceleração.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Faturamento do ciclo em R$ 412.800,00 contra ~R$ 382.000,00 do anterior. "
                        "Categoria top: chuteiras society. Ticket médio estável em R$ 380,00."
                    ),
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "clientes_recorrentes",
                    "valor": "Base fiel no e-commerce, com compradores mensais identificados.",
                    "indiceConfianca": 0.92,
                    "justificativa": (
                        "Exemplo canônico: MARCOS VINICIUS P. compra chuteiras de ~R$ 890,00 todo "
                        "mês desde 2024 (12/05, 10/06 e 05/07 em 2026), todas com entrega confirmada "
                        "por rastreio. Recorrência é evidência forte em disputas de chargeback."
                    ),
                    "origem": "adquirencia;memoria_relacionamento",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "sazonalidade",
                    "valor": "Sazonalidade extrema na Black Friday: ~2,8x o volume de um mês normal.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Histórico Adiq mostra pico anual em novembro. Em 2025 faltou estoque de "
                        "chuteiras society e o lojista declarou ter perdido vendas no auge do evento."
                    ),
                    "origem": "adquirencia;memoria_relacionamento",
                    "data": "2025-11-28T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "risco_chargeback",
                    "valor": "Chargeback rate de 0,4%, muito abaixo do teto das bandeiras.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "2 disputas abertas no ciclo: uma de comprador recorrente (alta chance de "
                        "reversão com evidência de entrega) e uma de extravio de transportadora "
                        "(reembolso recomendado). Operação saudável."
                    ),
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "life_events_do_negocio",
            "colecao": [
                {
                    "categoria": "expansao_filial",
                    "valor": "Planeja abrir filial em Campinas no segundo semestre de 2026.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Declarado pelo sócio no relacionamento. Demanda prevista: POS adicional, "
                        "conta da filial e possivelmente capital de giro pra montagem da loja."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-15T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "contratacoes",
                    "valor": "Contratou 2 vendedores em maio/2026, folha crescendo com a operação.",
                    "indiceConfianca": 0.85,
                    "justificativa": (
                        "Pagamentos recorrentes de pró-labore e salários via conta PJ BS2, incluindo "
                        "a favorecida Renata Lima (pró-labore de sócio)."
                    ),
                    "origem": "conta_pj",
                    "data": "2026-05-30T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "evento_critico_passado",
                    "valor": "Falta de estoque na Black Friday 2025 gerou perda de vendas no pico.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Registrado no relacionamento: em novembro/2025 o estoque de chuteiras "
                        "society esgotou no segundo dia do evento. Motivador direto da estratégia "
                        "de antecipação de recebíveis pré-BF 2026."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2025-11-28T00:00:00-03:00",
                    "analiseTemporal": "passado",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "situacao_financeira",
            "colecao": [
                {
                    "categoria": "agenda_recebiveis",
                    "valor": "Agenda líquida de R$ 287.450 nos próximos 30 dias e R$ 96.200 em 31-60 dias.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Dados sistêmicos da adquirência: recebíveis pendentes majoritariamente de "
                        "crédito (D+30 e parcelas futuras), MDR médio de 2,21% no ciclo."
                    ),
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "fluxo_de_caixa",
                    "valor": "Saldo PJ de R$ 84.300 com compromisso mensal relevante de fornecedor.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Conta BS2 Empresas com saldo disponível de R$ 84.300,00. Pagamento "
                        "recorrente de ~R$ 32.000,00 todo dia 15 para Almeida Esportes "
                        "Distribuidora (fornecedor principal, Pix chave CNPJ) e frete semanal de "
                        "~R$ 4.100,00 (RapidLog)."
                    ),
                    "origem": "conta_pj",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "credito_disponivel",
                    "valor": "Capital de giro BS2 pré-aprovado de R$ 200.000 sem uso.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Limite pré-aprovado com garantia na agenda de recebíveis; nunca utilizado. "
                        "Candidato natural a colchão de liquidez pós-Black Friday."
                    ),
                    "origem": "conta_pj",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "produtos_e_servicos",
            "colecao": [
                {
                    "categoria": "detalhamento_plano",
                    "valor": (
                        "{\"plano\": \"Adiq Pro\", \"mdr_credito_avista\": 2.39, \"mdr_credito_parcelado\": 2.99, "
                        "\"mdr_debito\": 1.09, \"mdr_pix\": 0.99, \"taxa_antecipacao_am\": 1.49, "
                        "\"aluguel_pos\": \"isento (faturamento > R$ 20 mil/mês)\"}"
                    ),
                    "indiceConfianca": 1.0,
                    "justificativa": "Dados sistêmicos do credenciamento Adiq Pro vigente desde 2020-03.",
                    "origem": "adquirencia",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "detalhamento_conta_pj",
                    "valor": "Conta BS2 Empresas sem tarifa de manutenção (benefício de credenciado).",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Conta corrente PJ ativa desde 2020, liquidação da agenda Adiq cai direto "
                        "nela (repasse automático). Pix PJ habilitado."
                    ),
                    "origem": "conta_pj",
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
                    "categoria": "elegibilidade_antecipacao",
                    "valor": "Elegível a antecipação spot e automática a 1,49% a.m. pro-rata.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Agenda líquida de R$ 287.450 em 30 dias, histórico sem inadimplência e "
                        "chargeback de 0,4% tornam a antecipação a oferta de maior propensão, "
                        "especialmente pré-Black Friday (estoque)."
                    ),
                    "origem": "modelo_nbo",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "elegibilidade_expansao",
                    "valor": "Elegível a POS adicional e conta da filial para a expansão de Campinas.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Plano Adiq Pro comporta novos terminais sem aluguel; filial declarada no "
                        "relacionamento habilita bundle POS + conta PJ da filial + câmbio BS2 para "
                        "importação de estoque."
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
                        "Lojista saudável e em crescimento (8% m/m), multicanal, chargeback mínimo, "
                        "agenda robusta de R$ 287 mil/30d, plano Adiq Pro, conta BS2 sem tarifa, "
                        "sazonalidade Black Friday crítica (falta de estoque em 2025) e expansão "
                        "pra Campinas no radar."
                    ),
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Consolidação de adquirência, conta PJ, suporte e memórias de relacionamento "
                        "do período 2024-2026."
                    ),
                    "origem": "adquirencia;conta_pj;suporte;memoria_relacionamento",
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
    if settings.demo_domain != "bs2_adiq":
        print(f"DEMO_DOMAIN={settings.demo_domain}; this seeder targets bs2_adiq only. Aborting.")
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
        key = f"{CHUNK_PREFIX}{MERCHANT_ID}:{categoria}"
        client.hset(
            key,
            mapping={
                "customer_id": MERCHANT_ID,
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
