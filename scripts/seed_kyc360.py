"""Seed the KYC customer-360 ("momento de vida") document + semantic slice index.

Mirrors the customer's real-world shape: a DynamoDB-style "momento de vida"
document (macrocategoria -> colecao -> categoria/valor/justificativa/confianca)
that today lives in DynamoDB + pgvector. Here it becomes:

  - one RedisJSON doc:   itau_assist:kyc360:CUST_DEMO_001   (the full 360)
  - one hash per slice:  itau_assist:kyc360_chunk:<cust>:<categoria>
                         (text + metadata + FLOAT32 embedding)
  - one vector index:    itau_assist_kyc360_idx (KNN over the slices)

The agent tool `get_customer_profile_slice` embeds the topic and returns ONLY
the matching slices, so the LLM never eats the full 360 payload. Token economy
is reported per call and accumulated in the FinOps panel.

Usage:
    DEMO_DOMAIN=itau_assist uv run python -m scripts.seed_kyc360
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
DOC_KEY = f"itau_assist:kyc360:{CUSTOMER_ID}"
CHUNK_PREFIX = "itau_assist:kyc360_chunk:"
INDEX_NAME = "itau_assist_kyc360_idx"

# Persona-consistent with the itau_assist seed: same merchants, contacts,
# amounts and storylines the other tools (raio-X, NBA, feature store) surface.
KYC360_DOC: dict = {
    "identificadorPessoa": CUSTOMER_ID,
    "resumo": (
        "Cliente Personnalité há 11 anos, uso intenso e saudável de cartão de crédito "
        "(faturas em dia), gastos discricionários fortes em gastronomia de alto tíquete, "
        "dependente universitária, apoio financeiro familiar recorrente via Pix, "
        "R$ 187.000 aplicados em CDB tributado, portfólio de seguros ativo e afinidade "
        "declarada com o Palmeiras."
    ),
    "estrategia": (
        "Priorizar migração de CDB tributado para LCI isenta (maior ganho líquido), "
        "oferta de afinidade Palmeiras no cartão branco, revisão do portfólio de seguros "
        "(residencial vence 2026-09-25, elegível AUTO/PET/VIAGEM) e acompanhamento do "
        "chamado de aumento de limite ligado a aquisição imobiliária."
    ),
    "colecoes": [
        {
            "macrocategoria": "estilo_de_vida_e_interesses",
            "colecao": [
                {
                    "categoria": "lifestyle_gastronomia",
                    "valor": "Frequenta restaurantes de alto tíquete com regularidade.",
                    "indiceConfianca": 0.92,
                    "justificativa": (
                        "Gastos relevantes em alimentação fora de casa: 'RESTAURANTE FASANO' R$ 624,50, "
                        "'BISTRO CHARLO' R$ 287,40 e 'OUTBACK' R$ 198,50 no ciclo atual, além de padarias "
                        "(R$ 145,30), 'IFOOD' R$ 42,90 e 'STARBUCKS' R$ 28,50, caracterizando alimentação "
                        "como categoria top de gasto."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "lifestyle_conveniencia_digital",
                    "valor": "Mantém assinaturas digitais recorrentes de entretenimento.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Assinaturas recorrentes: 'ON NETFLIX' R$ 55,90, 'EBN SPOTIFY' R$ 32,90, "
                        "'GLOBOPLAY' R$ 49,90 e 'AMAZON PAY LU' R$ 432,00 (Amazon Prime + Music Family, "
                        "reconhecida pelo cliente como legítima desde 2024, cobrada por volta do dia 12)."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-12T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "lifestyle_mobilidade",
                    "valor": "Mobilidade mista: veículo próprio em uso ativo e apps de transporte.",
                    "indiceConfianca": 0.88,
                    "justificativa": (
                        "Abastecimento em 'AUTO POSTO' R$ 312,40 no ciclo atual e corridas 'UBER' R$ 47,30, "
                        "indicando uso de carro próprio complementado por transporte por aplicativo."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-08T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "lifestyle_viagens",
                    "valor": "Viaja com recorrência e declara preferência por primeira classe em voos internacionais.",
                    "indiceConfianca": 0.85,
                    "justificativa": (
                        "Parcelamento ativo de viagem em 'CVC ITAIM VIAGENS' (R$ 1.450,00, parcela 3 de 10) e "
                        "preferência registrada pelo próprio cliente de sempre viajar em primeira classe nas "
                        "rotas internacionais."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-01T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "lifestyle_afinidade_futebol",
                    "valor": "Torcedor declarado do Palmeiras, com interesse em experiências ligadas ao clube.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Preferência declarada e registrada na memória do relacionamento: torce para o "
                        "Palmeiras. Alta aderência a ofertas de afinidade (cartão co-branded, experiências "
                        "no estádio, pontos virando ingresso)."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-20T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "life_events",
            "colecao": [
                {
                    "categoria": "familia_dependencia_financeira",
                    "valor": "Sustenta dependentes com despesas recorrentes de educação e apoio familiar.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Mensalidade recorrente 'PUC' de R$ 1.500,00 todo dia 5 (filha Sofia, universitária) e "
                        "Pix recorrente de R$ 800,00 todo início de mês para 'Tia Eulália', caracterizando "
                        "apoio financeiro familiar estável."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "familia_idade_filhos",
                    "valor": "Possui filha em idade universitária (ensino superior privado).",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Mensalidades recorrentes de R$ 1.500,00 para universidade privada (PUC) em nome de "
                        "Sofia, com pagamento estável há vários ciclos."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "status_aquisicao_imovel",
                    "valor": "Planeja aquisição imobiliária no curto prazo.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Chamado em andamento de aumento de limite do cartão Itaú The One motivado por "
                        "planejamento de aquisição imobiliária, combinado com reserva de R$ 187.000,00 "
                        "aplicada em CDB."
                    ),
                    "origem": "atendimento;momento_de_vida",
                    "data": "2026-06-28T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "preferencias_e_objetivos",
            "colecao": [
                {
                    "categoria": "preferencias_investimentos",
                    "valor": "Perfil conservador com concentração em renda fixa tributada; oportunidade clara em isentos.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Posição de R$ 187.000,00 em CDB tributado sem movimentação de resgate, sensível a "
                        "argumento de ganho líquido: migração parcial para LCI isenta de IR é o next best "
                        "action de maior impacto."
                    ),
                    "origem": "momento_de_vida;investimentos",
                    "data": "2026-07-01T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "objetivo_educacao",
                    "valor": "Direciona parte relevante da renda para educação da dependente.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Mensalidade universitária recorrente de R$ 1.500,00 (PUC), sem atraso, tratada como "
                        "compromisso prioritário do orçamento mensal."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-05T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "preferencias_opt_out",
                    "valor": "Opt-out declarado: não ofertar crédito consignado em hipótese alguma.",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Preferência explícita registrada pelo cliente no canal de atendimento. Deve ser "
                        "respeitada em qualquer jornada de oferta (NBO, campanhas, atendimento humano)."
                    ),
                    "origem": "memoria_relacionamento",
                    "data": "2026-06-20T00:00:00-03:00",
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
                    "categoria": "detalhamento_cartoes",
                    "valor": (
                        "[{\"nomeProduto\": \"ITAU THE ONE PERSONNALITE\", \"final\": \"4242\", "
                        "\"situacao\": \"Conta Ativa e Sem Atraso\", \"faturaAberta\": 12450.00, "
                        "\"vencimento\": \"2026-07-23\"}, {\"nomeProduto\": \"ITAU CLICK\", \"final\": \"8123\", "
                        "\"situacao\": \"Conta Ativa e Sem Atraso\", \"faturaAberta\": 2340.00, "
                        "\"vencimento\": \"2026-07-23\"}]"
                    ),
                    "indiceConfianca": 1.0,
                    "justificativa": "Dados sistêmicos de cartões ativos, incluindo anuidade The One parcelada (4 de 12, R$ 5.040,00).",
                    "origem": "cartao_pf",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "detalhamento_seguros",
                    "valor": (
                        "[{\"nome\": \"CARTAO PROTEGIDO\", \"valor\": 92.64, \"dataHoraContratacao\": \"2025-11-12\", "
                        "\"dataHoraFimVigencia\": \"2026-12-01\"}, {\"nome\": \"RESIDENCIAL\", \"valor\": 660.03, "
                        "\"dataHoraContratacao\": \"2025-09-24\", \"dataHoraFimVigencia\": \"2026-09-25\"}, "
                        "{\"nome\": \"VIDA INDIVIDUAL\", \"valor\": 521.33, \"dataHoraContratacao\": \"2023-10-27\", "
                        "\"dataHoraFimVigencia\": \"2085-10-27\"}]"
                    ),
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Dados sistêmicos de seguros vigentes: CARTAO PROTEGIDO (R$ 92,64/ano, vigência até "
                        "2026-12-01), RESIDENCIAL (R$ 660,03/ano, vigência até 2026-09-25, renovação próxima) "
                        "e VIDA INDIVIDUAL (R$ 521,33/ano, vigência longa até 2085-10-27)."
                    ),
                    "origem": "seguro_pf",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "credito_saude_financeira",
                    "valor": "Uso saudável de crédito: faturas pagas integralmente, sem rotativo nem LIS.",
                    "indiceConfianca": 0.92,
                    "justificativa": (
                        "Faturas abertas somam R$ 14.790,00 com saldo disponível de R$ 28.450,00 em conta; "
                        "histórico sem pagamento mínimo, sem juros de limite da conta e sem multas de atraso. "
                        "Limite disponível folgado no The One (R$ 487.550,00)."
                    ),
                    "origem": "momento_de_vida;cartao",
                    "data": "2026-07-13T00:00:00-03:00",
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
                    "categoria": "gastos_essenciais_distribuicao",
                    "valor": "Compromissos essenciais estáveis: educação, apoio familiar e parcelados de médio prazo.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Educação (PUC R$ 1.500,00 dia 5), apoio familiar (Pix R$ 800,00 Tia Eulália) e "
                        "parcelados ativos: CVC 3/10 de R$ 1.450,00, Apple Store 2/12 de R$ 1.083,25, "
                        "H Stern 1/6 de R$ 720,00, Renner 1/3 de R$ 489,90 e anuidade The One 4/12 de "
                        "R$ 5.040,00, com R$ 65.882,30 a vencer no total."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "gastos_discricionarios_distribuicao",
                    "valor": "Discricionário concentrado em gastronomia de alto tíquete e compras pontuais.",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Alimentação é a categoria top do ciclo (Fasano, Bistrô Charlo, Outback), seguida de "
                        "assinaturas digitais e compras pontuais de maior valor (Apple Store, H Stern)."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
            ],
        },
        {
            "macrocategoria": "comportamento_transacional",
            "colecao": [
                {
                    "categoria": "pagamentos_uso_pix",
                    "valor": "Usa Pix para transferências pessoais recorrentes e pagamentos no dia a dia.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Pix recorrentes: R$ 800,00 para 'Tia Eulália' (dia 1º), R$ 1.500,00 mensalidade da "
                        "Sofia (dia 5) e transferências frequentes para o contato 'Carlos Eduardo Souza' "
                        "(chave celular, Itaú)."
                    ),
                    "origem": "momento_de_vida",
                    "data": "2026-07-08T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "pontos_beneficios",
                    "valor": "Acumulador ativo do Sempre Presente com pontos a vencer no curto prazo.",
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Saldo de 187.420 pontos, com 4.500 pontos vencendo em 24/09/2026. Categoria top: "
                        "alimentação em restaurante, com multiplicador 1,5x no perfil."
                    ),
                    "origem": "pontos_pf",
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
                    "categoria": "elegibilidade_seguros",
                    "valor": "[{\"nome\": \"AUTO\"}, {\"nome\": \"ODONTO\"}, {\"nome\": \"PET\"}, {\"nome\": \"VIAGEM\"}]",
                    "indiceConfianca": 1.0,
                    "justificativa": (
                        "Dados sistêmicos: elegível a AUTO (veículo próprio em uso ativo), ODONTO, PET e "
                        "VIAGEM (padrão recorrente de viagens). Já possui CARTAO PROTEGIDO, RESIDENCIAL e VIDA."
                    ),
                    "origem": "seguro_pf",
                    "data": "2026-07-13T00:00:00-03:00",
                    "analiseTemporal": "presente",
                    "aferido": True,
                    "status": "HABILITADO",
                },
                {
                    "categoria": "elegibilidade_cartao_afinidade",
                    "valor": "Elegível ao cartão Personnalité co-branded Palmeiras (cartão branco).",
                    "indiceConfianca": 0.9,
                    "justificativa": (
                        "Afinidade declarada com o Palmeiras + relacionamento Personnalité de 11 anos + uso "
                        "saudável de crédito tornam a oferta de afinidade de alta propensão."
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
                        "Cliente Personnalité há 11 anos, saudável em crédito, discricionário forte em "
                        "gastronomia, dependente universitária, R$ 187.000 em CDB tributado, seguros ativos "
                        "(cartão, residencial, vida), 187.420 pontos, palmeirense, planejando aquisição "
                        "imobiliária e com opt-out de consignado."
                    ),
                    "indiceConfianca": 0.95,
                    "justificativa": (
                        "Consolidação de momento_de_vida, cartões, seguros, pontos e memórias de "
                        "relacionamento do período 2024-2026."
                    ),
                    "origem": "momento_de_vida;seguro;conta;cartao;memoria_relacionamento",
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
    if settings.demo_domain != "itau_assist":
        print(f"DEMO_DOMAIN={settings.demo_domain}; this seeder targets itau_assist only. Aborting.")
        return

    client = create_redis_client(settings)
    openai_client = OpenAI(
        api_key=settings.openai_api_key,
        **({"base_url": settings.openai_base_url} if settings.openai_base_url else {}),
    )

    # 1) Full 360 document as RedisJSON (the "payloadzão" the agent never eats whole)
    client.execute_command("JSON.SET", DOC_KEY, "$", json.dumps(KYC360_DOC, ensure_ascii=False))
    doc_bytes = int(client.execute_command("MEMORY", "USAGE", DOC_KEY) or 0)
    print(f"[1/3] {DOC_KEY} written ({doc_bytes} bytes in Redis)")

    # 2) One chunk per categoria, embedded for KNN slicing
    chunks: list[tuple[str, str, str]] = []  # (macro, categoria, text)
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
        # Binary field must skip decode_responses: use a raw execute on the same client
        client.execute_command("HSET", key, "embedding", array("f", emb.embedding).tobytes())
        total_chunk_bytes += int(client.execute_command("MEMORY", "USAGE", key) or 0)
    print(f"[2/3] {len(chunks)} slices embedded (dim={dim}) — {total_chunk_bytes} bytes total, "
          f"~{total_chunk_bytes // len(chunks)} bytes/slice")

    # 3) Vector index over the slices (idempotent: drop + recreate, keep docs)
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
