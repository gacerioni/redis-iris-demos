"""Seed the leet_bank KYC "perfil 360" + semantic slice index.

Same architecture as the Itaú/BS2 customer-360: one rich JSON document
(macrocategoria -> colecao -> categoria/valor/justificativa/confianca)
describing the CUSTOMER, stored as:

  - one RedisJSON doc:   leet_bank:kyc360:CUST_DEMO_001
  - one hash per slice:  leet_bank:kyc360_chunk:<customer>:<categoria>
  - one vector index:    leet_bank_kyc360_idx

The agent tool `get_customer_profile_slice` embeds the topic and returns ONLY
the matching slices; token economy lands in the FinOps panel.

Usage:
    DEMO_DOMAIN=leet_bank uv run python -m scripts.seed_kyc360_leet_bank
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
DOC_KEY = f"leet_bank:kyc360:{CUSTOMER_ID}"
CHUNK_PREFIX = "leet_bank:kyc360_chunk:"
INDEX_NAME = "leet_bank_kyc360_idx"

KYC360_DOC: dict = {
    "identificadorPessoa": CUSTOMER_ID,
    "resumo": (
        "Gabriel Cerioni, Elite 1337 do Leet Bank desde 2016: engenheiro de plataforma, "
        "saldo de R$ 31.337, CDB de R$ 133.700 a 103,37% do CDI, cartao Leet Black com "
        "12% de utilizacao, 133.700 XP. Perfil de confianca maxima (golpe score 0,02), "
        "pai da Sofia (PUC), torcedor do Raja Casablanca, e vai ao Rock in Rio 2026 no dia 7 de setembro."
    ),
    "estrategia": (
        "Priorizar o Credito Flash com garantia tokenizada (CDB parado como colateral, "
        "1,337% a.m.), ativar o combo Rock in Rio (limite temporario + XP em experiencias "
        "+ alerta de golpe de ingresso) e proteger o padrao Pix do cliente com o modelo "
        "antifraude (ticket medio R$ 317)."
    ),
    "colecoes": [
        {
            "macrocategoria": "perfil_e_estilo",
            "colecao": [
                {
                    "categoria": "perfil_profissional",
                    "valor": "Engenheiro de plataforma, perfil dev, consumo forte em tecnologia e educacao.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Gastos recorrentes em Kabum (monitor ultrawide parcelado 3/10 de R$ 412), "
                        "cursos Alura, assinatura CLOUD DEV PRO (R$ 89,90, reconhecida desde 2024) e "
                        "JETFLIX BR. Multiplicador 2x de XP em tech ativo."
                    ),
                    "origem": "comportamento",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "assinaturas_reconhecidas",
                    "valor": "CLOUD DEV PRO (R$ 89,90, dia 12) e JETFLIX BR (R$ 55,90) sao assinaturas legitimas reconhecidas.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "CLOUD DEV PRO registrada pelo proprio cliente como ferramenta de trabalho desde 2024; "
                        "historico mensal consistente nos dias 12. Contestacoes dessas cobrancas tendem a ser improcedentes."
                    ),
                    "origem": "memoria_relacionamento;comportamento",
                    "data": "2026-07-12T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "momentos_de_vida",
            "colecao": [
                {
                    "categoria": "evento_rock_in_rio",
                    "valor": "Vai ao Rock in Rio 2026 no dia 7 de setembro com a filha Sofia (show do Elton John).",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Declarado no relacionamento; ingressos comprados nos canais oficiais. Gatilhos: limite "
                        "temporario para o fim de semana do evento, resgate de XP em experiencias, alerta de golpe "
                        "de ingresso (so canais oficiais)."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2026-07-10T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "familia_dependentes",
                    "valor": "Mantem a mensalidade da filha Sofia na PUC (R$ 1.500 todo dia 5) e apoia a Tia Eulalia (R$ 800 todo dia 1).",
                    "indiceConfianca": 0.95,
                    "justificativa": "Pix recorrentes estaveis ha mais de 12 meses para os dois compromissos familiares.",
                    "origem": "comportamento",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "time_do_coracao",
                    "valor": "Torcedor declarado do Raja Casablanca (Marrocos).",
                    "indiceConfianca": 1.0,
                    "justificativa": "Preferencia registrada pelo proprio cliente no relacionamento.",
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-20T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "situacao_financeira",
            "colecao": [
                {
                    "categoria": "liquidez_e_investimentos",
                    "valor": "Saldo de R$ 31.337 em conta e CDB de R$ 133.700 rendendo 103,37% do CDI com liquidez diaria.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Dados sistemicos. O CDB inteiro esta livre (sem colateral em uso), o que habilita o "
                        "Credito Flash com garantia tokenizada de ate R$ 100.000 a 1,337% a.m."
                    ),
                    "origem": "conta;investimentos",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "cartao_e_fatura",
                    "valor": "Leet Black final 1337: limite R$ 61.337, fatura aberta R$ 7.331 (venc. 28/07), utilizacao 12%, sem atraso.",
                    "indiceConfianca": 1.0,
                    "justificativa": "Dados sistemicos do cartao; anuidade isenta pela regra de fatura acima de R$ 5 mil/mes.",
                    "origem": "cartao",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "programa_xp",
                    "valor": "133.700 XP no nivel Elite 1337, com 4.200 XP expirando em 30/09/2026.",
                    "indiceConfianca": 1.0,
                    "justificativa": "Multiplicador 2x em tech. XP resgatavel em cashback e experiencias (incluindo eventos parceiros).",
                    "origem": "pontos",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "seguranca_e_confianca",
            "colecao": [
                {
                    "categoria": "padrao_pix",
                    "valor": "Padrao de Pix: ticket medio R$ 317, maior envio em 90 dias R$ 1.500, 4 contatos confiaveis.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Envios recorrentes para Carlos, Tia Eulalia, Sofia e Imobiliaria Horizonte. Transferencias "
                        "para chaves desconhecidas acima do padrao devem ser SEGURADAS pelo modelo antifraude."
                    ),
                    "origem": "modelo_risco;comportamento",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "confianca",
                    "valor": "Golpe score 0,02 (baixissimo). Nunca caiu em golpe, MED nunca acionado.",
                    "indiceConfianca": 1.0,
                    "justificativa": "Historico limpo de disputas por fraude; 1 unica contestacao antiga resolvida em 2025.",
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
                    "categoria": "credito_flash_tokenizado",
                    "valor": "Pre-aprovado: Credito Flash de ate R$ 100.000 a 1,337% a.m. com o CDB como garantia tokenizada.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "CDB de R$ 133.700 livre + propensao a credito 0,91 + utilizacao baixa do cartao. O CDB "
                        "continua rendendo enquanto colateraliza; liberacao do colateral conforme amortizacao."
                    ),
                    "origem": "modelo_nbo",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "combo_evento",
                    "valor": "Elegivel ao combo Rock in Rio: limite temporario no fim de semana do evento + XP em experiencias.",
                    "indiceConfianca": 0.9,
                    "justificativa": "Evento proximo registrado (07/09) + XP expirando em 30/09 tornam o combo a oferta de maior conversao.",
                    "origem": "modelo_nbo",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "opt_out",
                    "valor": "NUNCA ofertar credito consignado (preferencia registrada).",
                    "indiceConfianca": 1.0,
                    "justificativa": "Registrado pelo proprio cliente; vale para todas as jornadas de oferta.",
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-20T00:00:00-03:00",
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
                        "Elite 1337 ha 10 anos, dev, financas saudaveis (12% de utilizacao, CDB robusto), "
                        "confianca maxima no modelo de risco, XP alto com expiracao proxima, Rock in Rio no radar "
                        "e Credito Flash tokenizado pre-aprovado como melhor proxima acao."
                    ),
                    "indiceConfianca": 0.95,
                    "justificativa": "Consolidacao de conta, cartao, investimentos, pontos, risco e memorias 2016-2026.",
                    "origem": "conta;cartao;investimentos;pontos;modelo_risco;memoria_relacionamento",
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
    if settings.demo_domain != "leet_bank":
        print(f"DEMO_DOMAIN={settings.demo_domain}; this seeder targets leet_bank only. Aborting.")
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
