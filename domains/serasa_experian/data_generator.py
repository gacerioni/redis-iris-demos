"""Serasa Experian — seed sintético em PT-BR.

Persona principal: Gabriel Cerioni, Serasa Score 692 (faixa Bom na escala
oficial), Premium Plus há 6 anos. Narrativa: subir de "bom" para "excelente"
(faltam ~9 pontos pra cruzar 701), e quitar a dívida negativada cruza a faixa ao
vivo (recompute-on-write leva o score pra ~738, faixa Excelente). Tem 3 pendências
"esquecidas" que aparecem só na descoberta real-time, e um feature store online
que alimenta o Serasa Score e o motor de decisão do eCred.

Escala oficial Serasa Score: 0-300 baixo, 301-500 regular, 501-700 bom,
701-1000 excelente.

Stack: 14 entidades. Tools determinísticas escrevem runtime via UnifiedClient.import_data.
Datas SEMPRE relativas (now - timedelta), zero datas absolutas hardcoded.
"""

from __future__ import annotations

import json
import os
import sys
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "serasa_experian"


def ts(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input=texts, model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in resp.data]


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


DEMO_USER_ID = "CUST_DEMO_001"


# ═══════════════════════════════════════════════════════════════════════════
#  Pesos OFICIAIS do Serasa Score (somam 1.0) — fonte da verdade do recompute
# ═══════════════════════════════════════════════════════════════════════════
SCORE_WEIGHTS: dict[str, float] = {
    "cadastro_positivo": 0.29,
    "experiencia_mercado": 0.24,
    "dividas": 0.21,
    "busca_credito": 0.12,
    "dados_cadastrais": 0.08,
    "contratos": 0.06,
}


def faixa_oficial(score: int) -> str:
    """Escala oficial Serasa Score."""
    if score >= 701:
        return "excelente"
    if score >= 501:
        return "bom"
    if score >= 301:
        return "regular"
    return "baixo"


# ═══════════════════════════════════════════════════════════════════════════
#  CONSUMERS (5) — Gabriel + 4 outros pra densidade
# ═══════════════════════════════════════════════════════════════════════════

CONSUMERS = [
    {
        "consumer_id": DEMO_USER_ID,
        "name": "Gabriel Cerioni",
        "cpf_masked": "***.456.789-**",
        "email": "gabriel.cerioni@example.com.br",
        "phone": "+55 11 98765-4321",
        "city": "São Paulo",
        "state": "SP",
        "score": 692,
        "score_faixa": "bom",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium_plus",
        "premium_since_years": 6,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
        "renda_mensal_estimada": 3800.00,
        "meta_faixa": "excelente",
    },
    {
        "consumer_id": "CUST_002",
        "name": "Camila Ribeiro Sousa",
        "cpf_masked": "***.234.567-**",
        "email": "camila.r.sousa@example.com.br",
        "phone": "+55 11 98123-4500",
        "city": "Osasco",
        "state": "SP",
        "score": 458,
        "score_faixa": "regular",
        "monitoramento_ativo": "sim",
        "premium_tier": "free",
        "premium_since_years": 0,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "nao",
        "renda_mensal_estimada": 2600.00,
        "meta_faixa": "bom",
    },
    {
        "consumer_id": "CUST_003",
        "name": "Robson Magrão Oliveira",
        "cpf_masked": "***.890.123-**",
        "email": "robson.magrao@example.com.br",
        "phone": "+55 11 97333-4444",
        "city": "Pompeia",
        "state": "SP",
        "score": 612,
        "score_faixa": "bom",
        "monitoramento_ativo": "nao",
        "premium_tier": "free",
        "premium_since_years": 0,
        "cadastro_positivo_ativo": "nao",
        "antifraude_ativo": "nao",
        "renda_mensal_estimada": 3100.00,
        "meta_faixa": "excelente",
    },
    {
        "consumer_id": "CUST_004",
        "name": "Tatiane Aparecida Souza",
        "cpf_masked": "***.345.678-**",
        "email": "tatiane.aps@example.com.br",
        "phone": "+55 11 96222-3333",
        "city": "Tatuapé",
        "state": "SP",
        "score": 287,
        "score_faixa": "baixo",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium",
        "premium_since_years": 1,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
        "renda_mensal_estimada": 1900.00,
        "meta_faixa": "regular",
    },
    {
        "consumer_id": "CUST_005",
        "name": "Miller Moreno",
        "cpf_masked": "***.567.890-**",
        "email": "miller.moreno@example.com.br",
        "phone": "+55 11 95111-2222",
        "city": "Itaim Bibi",
        "state": "SP",
        "score": 845,
        "score_faixa": "excelente",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium",
        "premium_since_years": 2,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
        "renda_mensal_estimada": 7400.00,
        "meta_faixa": "excelente_900",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  CREDITORS (10) — mix de setores brasileiros
# ═══════════════════════════════════════════════════════════════════════════

CREDITORS = [
    {"creditor_id": "CRED_TIM", "name": "TIM Brasil", "setor": "telecom", "partner_level": "full",
     "max_discount_pct": 70, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_CLARO", "name": "Claro NET", "setor": "telecom", "partner_level": "full",
     "max_discount_pct": 65, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_VIVO", "name": "Vivo Telefônica", "setor": "telecom", "partner_level": "full",
     "max_discount_pct": 60, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_MAGALU", "name": "Magazine Luiza", "setor": "varejo", "partner_level": "full",
     "max_discount_pct": 50, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_RIACHUELO", "name": "Lojas Riachuelo", "setor": "varejo", "partner_level": "full",
     "max_discount_pct": 55, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_AMERICANAS", "name": "Americanas", "setor": "varejo", "partner_level": "legacy",
     "max_discount_pct": 80, "supports_realtime_query": "nao"},
    {"creditor_id": "CRED_ENEL", "name": "Enel Distribuição SP", "setor": "energia", "partner_level": "full",
     "max_discount_pct": 30, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_SKY", "name": "Sky TV", "setor": "telecom", "partner_level": "realtime_only",
     "max_discount_pct": 70, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_AMAZON", "name": "Amazon Brasil", "setor": "streaming", "partner_level": "realtime_only",
     "max_discount_pct": 40, "supports_realtime_query": "sim"},
    {"creditor_id": "CRED_BRADESCO_SAUDE", "name": "Bradesco Saúde", "setor": "saude", "partner_level": "full",
     "max_discount_pct": 25, "supports_realtime_query": "sim"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  DEBTS — dívidas negativadas. Gabriel tem 1 (a que segura o score em "bom");
#  quitá-la sobe f_dividas e cruza a faixa pra "excelente" no recompute.
# ═══════════════════════════════════════════════════════════════════════════

DEBTS = [
    # Gabriel (CUST_DEMO_001) — 1 negativação que segura o score na faixa Bom
    {"debt_id": "DBT_GABS_001", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_RIACHUELO",
     "descricao": "Cartão Riachuelo: fatura parcelada negativada após cancelamento",
     "valor_original": 612.00, "valor_atualizado": 847.50,
     "data_origem": ts(now - timedelta(days=150)),
     "dias_em_atraso": 150, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 46},
    # Camila (CUST_002) — 3 negativações
    {"debt_id": "DBT_001", "consumer_id": "CUST_002", "creditor_id": "CRED_RIACHUELO",
     "descricao": "Cartão Riachuelo: parcelado em atraso",
     "valor_original": 845.00, "valor_atualizado": 1247.30,
     "data_origem": ts(now - timedelta(days=180)),
     "dias_em_atraso": 180, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 42},
    {"debt_id": "DBT_002", "consumer_id": "CUST_002", "creditor_id": "CRED_CLARO",
     "descricao": "Plano pós-pago Claro com 4 faturas em aberto",
     "valor_original": 360.00, "valor_atualizado": 587.20,
     "data_origem": ts(now - timedelta(days=120)),
     "dias_em_atraso": 120, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 28},
    {"debt_id": "DBT_003", "consumer_id": "CUST_002", "creditor_id": "CRED_AMERICANAS",
     "descricao": "Compra parcelada Americanas: 8 parcelas em aberto",
     "valor_original": 1200.00, "valor_atualizado": 2340.50,
     "data_origem": ts(now - timedelta(days=240)),
     "dias_em_atraso": 240, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 65},
    # Tatiane (CUST_004) — situação crítica
    {"debt_id": "DBT_004", "consumer_id": "CUST_004", "creditor_id": "CRED_ENEL",
     "descricao": "Conta de luz em atraso há 8 meses",
     "valor_original": 1450.00, "valor_atualizado": 2180.00,
     "data_origem": ts(now - timedelta(days=240)),
     "dias_em_atraso": 240, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 55},
    {"debt_id": "DBT_005", "consumer_id": "CUST_004", "creditor_id": "CRED_BRADESCO_SAUDE",
     "descricao": "Mensalidade do plano de saúde em atraso",
     "valor_original": 890.00, "valor_atualizado": 1120.00,
     "data_origem": ts(now - timedelta(days=90)),
     "dias_em_atraso": 90, "is_negativada": "sim", "status": "em_negociacao",
     "score_impact_estimate": 30},
    # Robson (CUST_003) — 1 dívida moderada
    {"debt_id": "DBT_006", "consumer_id": "CUST_003", "creditor_id": "CRED_VIVO",
     "descricao": "Vivo Fibra: fatura única em atraso pós-cancelamento",
     "valor_original": 247.00, "valor_atualizado": 312.40,
     "data_origem": ts(now - timedelta(days=60)),
     "dias_em_atraso": 60, "is_negativada": "sim", "status": "ativa",
     "score_impact_estimate": 18},
]


# ═══════════════════════════════════════════════════════════════════════════
#  PENDING DEBTS — "esquecidos" do Gabriel (descobertos via real-time)
# ═══════════════════════════════════════════════════════════════════════════

PENDING_DEBTS = [
    {
        "pending_id": "PEND_GABS_001", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_TIM",
        "descricao": (
            "Fatura residual TIM Pos no valor de R$ 287,40: linha portada pra outra operadora, "
            "a ultima fatura ficou orfã e nao migrou pra cobranca ativa (sem boleto, sem cobranca "
            "registrada). Canal de origem: portabilidade. Sem registro de ultima cobranca."
        ),
        "valor": 287.40,
        "data_origem": ts(now - timedelta(days=320)),
        "descoberto_em": ts(now),
        "dias_silencioso": 320,
        "status": "aberta",
        "source": "realtime_discovery",
        "would_negativate_in_days": 40,
    },
    {
        "pending_id": "PEND_GABS_002", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_CLARO",
        "descricao": (
            "Claro NET Combo Familia: cancelamento mal processado pela central, ultima mensalidade "
            "ficou em aberto. Canal de origem: central de retencao. Ultima cobranca emitida ha ~150 dias "
            "e nunca reapresentada."
        ),
        "valor": 134.90,
        "data_origem": ts(now - timedelta(days=185)),
        "descoberto_em": ts(now),
        "dias_silencioso": 185,
        "status": "aberta",
        "source": "realtime_discovery",
        "would_negativate_in_days": 175,
    },
    {
        "pending_id": "PEND_GABS_003", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_MAGALU",
        "descricao": (
            "Devolucao Magalu nao processada no pedido 2024-7841933-MG: produto retornado e recebido "
            "no CD, mas o estorno parcial ficou pendente. Canal de origem: marketplace (devolucao). "
            "Numero do pedido 2024-7841933-MG."
        ),
        "valor": 56.80,
        "data_origem": ts(now - timedelta(days=95)),
        "descoberto_em": ts(now),
        "dias_silencioso": 95,
        "status": "aberta",
        "source": "realtime_discovery",
        "would_negativate_in_days": 265,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PROPOSALS — ofertas pré-existentes (geradas pelo Limpa Nome pra cada pending)
# ═══════════════════════════════════════════════════════════════════════════

PROPOSALS = [
    # Gabriel — oferta pra quitar a negativação Riachuelo (quitar cruza a faixa)
    {"proposal_id": "PROP_GABS_DBT_001", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_RIACHUELO",
     "debt_id": "DBT_GABS_001", "pending_id": None,
     "valor_original": 847.50, "valor_com_desconto": 508.50,
     "desconto_percentual": 40, "modalidade": "à_vista",
     "valor_parcela": 508.50,
     "validade": ts(now + timedelta(days=10)),
     "status": "ativa"},
    {"proposal_id": "PROP_GABS_001", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_TIM",
     "debt_id": None, "pending_id": "PEND_GABS_001",
     "valor_original": 287.40, "valor_com_desconto": 186.81,
     "desconto_percentual": 35, "modalidade": "à_vista",
     "valor_parcela": 186.81,
     "validade": ts(now + timedelta(days=14)),
     "status": "ativa"},
    {"proposal_id": "PROP_GABS_002", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_CLARO",
     "debt_id": None, "pending_id": "PEND_GABS_002",
     "valor_original": 134.90, "valor_com_desconto": 67.45,
     "desconto_percentual": 50, "modalidade": "parcelado_3x",
     "valor_parcela": 22.48,
     "validade": ts(now + timedelta(days=10)),
     "status": "ativa"},
    {"proposal_id": "PROP_GABS_003", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_MAGALU",
     "debt_id": None, "pending_id": "PEND_GABS_003",
     "valor_original": 56.80, "valor_com_desconto": 28.40,
     "desconto_percentual": 50, "modalidade": "à_vista",
     "valor_parcela": 28.40,
     "validade": ts(now + timedelta(days=30)),
     "status": "ativa"},
    # Camila — ofertas pras dívidas negativadas
    {"proposal_id": "PROP_CAMI_001", "consumer_id": "CUST_002", "creditor_id": "CRED_RIACHUELO",
     "debt_id": "DBT_001", "pending_id": None,
     "valor_original": 1247.30, "valor_com_desconto": 561.28,
     "desconto_percentual": 55, "modalidade": "parcelado_6x",
     "valor_parcela": 93.55,
     "validade": ts(now + timedelta(days=7)),
     "status": "ativa"},
    {"proposal_id": "PROP_CAMI_002", "consumer_id": "CUST_002", "creditor_id": "CRED_CLARO",
     "debt_id": "DBT_002", "pending_id": None,
     "valor_original": 587.20, "valor_com_desconto": 205.52,
     "desconto_percentual": 65, "modalidade": "à_vista",
     "valor_parcela": 205.52,
     "validade": ts(now + timedelta(days=7)),
     "status": "ativa"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  SCORE HISTORY — 6 meses do Gabriel (subindo dentro da faixa Bom rumo a Excelente)
# ═══════════════════════════════════════════════════════════════════════════

def _month_label(months_back: int) -> str:
    base = now.replace(day=15)
    for _ in range(months_back):
        base = (base.replace(day=1) - timedelta(days=1)).replace(day=15)
    return base.strftime("%Y-%m")


SCORE_HISTORY = [
    # ── Gabriel (CUST_DEMO_001) — arco não-linear: baseline -> dip Riachuelo ->
    #    vale -> recuperação via Cadastro Positivo -> dip por busca de crédito -> 692 hoje
    {"history_id": "SH_GABS_M0", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(0),
     "score": 692, "faixa": faixa_oficial(692), "variacao": +11,
     "fator_principal": "Volume de consultas ao CPF normalizou e o Cadastro Positivo seguiu somando contas pagas em dia (faltam ~9 pts pra Excelente)"},
    {"history_id": "SH_GABS_M1", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(1),
     "score": 681, "faixa": faixa_oficial(681), "variacao": +23,
     "fator_principal": "Recuperação forte: parou a corrida por crédito e o peso de busca de crédito voltou a relaxar"},
    {"history_id": "SH_GABS_M2", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(2),
     "score": 658, "faixa": faixa_oficial(658), "variacao": -13,
     "fator_principal": "Pico de busca de crédito: várias consultas ao CPF em pouco tempo (Magalu, Inter, C6) derrubaram o peso de busca de crédito"},
    {"history_id": "SH_GABS_M3", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(3),
     "score": 671, "faixa": faixa_oficial(671), "variacao": +11,
     "fator_principal": "Experiência de mercado consolidando e dados cadastrais atualizados (comprovante de renda)"},
    {"history_id": "SH_GABS_M4", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(4),
     "score": 660, "faixa": faixa_oficial(660), "variacao": +19,
     "fator_principal": "Cadastro Positivo absorvendo novas contas recorrentes pagas em dia (maior peso do score, 29%)"},
    {"history_id": "SH_GABS_M5", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(5),
     "score": 641, "faixa": faixa_oficial(641), "variacao": +14,
     "fator_principal": "Cadastro Positivo passou a puxar o score pra cima: histórico de pagamento em dia começou a compensar a negativação"},
    {"history_id": "SH_GABS_M6", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(6),
     "score": 627, "faixa": faixa_oficial(627), "variacao": +5,
     "fator_principal": "Fundo do vale: score estabilizou com a negativação da Riachuelo ainda em aberto segurando o peso de dívidas"},
    {"history_id": "SH_GABS_M7", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(7),
     "score": 622, "faixa": faixa_oficial(622), "variacao": -18,
     "fator_principal": "Impacto cheio da negativação da Riachuelo (cartão parcelado pós-cancelamento) no peso de dívidas"},
    {"history_id": "SH_GABS_M8", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(8),
     "score": 640, "faixa": faixa_oficial(640), "variacao": -24,
     "fator_principal": "Negativação da Riachuelo registrada: fatura parcelada virou negativação ativa e derrubou o peso de dívidas"},
    {"history_id": "SH_GABS_M9", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(9),
     "score": 664, "faixa": faixa_oficial(664), "variacao": +6,
     "fator_principal": "Padrão estável de utilização de crédito, sem negativações ativas"},
    {"history_id": "SH_GABS_M10", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(10),
     "score": 658, "faixa": faixa_oficial(658), "variacao": +4,
     "fator_principal": "Baseline saudável na faixa Bom: experiência de mercado consolidada e contas em dia"},
    # ── Camila — declínio (preservado) ──────────────────────────────────────
    {"history_id": "SH_CAMI_M0", "consumer_id": "CUST_002", "mes_referencia": _month_label(0),
     "score": 458, "faixa": "regular", "variacao": -54,
     "fator_principal": "3 negativações ativas: Riachuelo, Claro, Americanas"},
    {"history_id": "SH_CAMI_M1", "consumer_id": "CUST_002", "mes_referencia": _month_label(1),
     "score": 512, "faixa": "bom", "variacao": -38,
     "fator_principal": "Atraso > 90 dias em conta Americanas"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  SCORE FACTORS — categorias = 6 PESOS OFICIAIS do Serasa Score
# ═══════════════════════════════════════════════════════════════════════════

SCORE_FACTORS = [
    {"factor_id": "SF_GABS_001", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Cadastro Positivo ativo há 6 anos, contas recorrentes pagas em dia",
     "peso_estimado": 165, "categoria": "cadastro_positivo"},
    {"factor_id": "SF_GABS_002", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Experiência de mercado consolidada (relacionamento financeiro longo)",
     "peso_estimado": 120, "categoria": "experiencia_mercado"},
    {"factor_id": "SF_GABS_003", "consumer_id": DEMO_USER_ID, "tipo": "negativo",
     "descricao": "Dívida negativada da Riachuelo em aberto: é o que mais segura o score (quitar cruza pra Excelente)",
     "peso_estimado": -46, "categoria": "dividas"},
    {"factor_id": "SF_GABS_004", "consumer_id": DEMO_USER_ID, "tipo": "negativo",
     "descricao": "Volume médio-alto de consultas ao CPF nos últimos 90 dias (2o fator que mais segura)",
     "peso_estimado": -30, "categoria": "busca_credito"},
    {"factor_id": "SF_GABS_005", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Dados cadastrais completos e atualizados (renda comprovada)",
     "peso_estimado": 55, "categoria": "dados_cadastrais"},
    {"factor_id": "SF_GABS_006", "consumer_id": DEMO_USER_ID, "tipo": "negativo",
     "descricao": "Histórico de contratos firmados ainda enxuto (poucos contratos longos)",
     "peso_estimado": -22, "categoria": "contratos"},
    # Camila — fatores
    {"factor_id": "SF_CAMI_001", "consumer_id": "CUST_002", "tipo": "negativo",
     "descricao": "3 negativações ativas em diferentes setores",
     "peso_estimado": -135, "categoria": "dividas"},
    {"factor_id": "SF_CAMI_002", "consumer_id": "CUST_002", "tipo": "positivo",
     "descricao": "Cadastro Positivo ativado recentemente",
     "peso_estimado": 25, "categoria": "cadastro_positivo"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  INQUIRIES — quem consultou o CPF do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

INQUIRIES = [
    {"inquiry_id": "INQ_GABS_001", "consumer_id": DEMO_USER_ID,
     "consultor": "Nubank (Análise de aumento de limite)",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=3, hours=9)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_002", "consumer_id": DEMO_USER_ID,
     "consultor": "PagBank (Conta e cartão PagSeguro)",
     "consultor_setor": "financeiro",
     "motivo": "contratacao",
     "data_consulta": ts(now - timedelta(days=6, hours=15)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_003", "consumer_id": DEMO_USER_ID,
     "consultor": "Localiza (Locação de veículo: análise cadastral)",
     "consultor_setor": "varejo",
     "motivo": "contratacao",
     "data_consulta": ts(now - timedelta(days=9, hours=11)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_004", "consumer_id": DEMO_USER_ID,
     "consultor": "Porto Seguro (Cotação seguro auto)",
     "consultor_setor": "financeiro",
     "motivo": "cadastro",
     "data_consulta": ts(now - timedelta(days=12, hours=16)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_005", "consumer_id": DEMO_USER_ID,
     "consultor": "Banco Inter (Crédito imobiliário: simulação)",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=14, hours=10)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_006", "consumer_id": DEMO_USER_ID,
     "consultor": "Mercado Pago (Limite pré-aprovado)",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=18, hours=13)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 1},
    {"inquiry_id": "INQ_GABS_007", "consumer_id": DEMO_USER_ID,
     "consultor": "Magazine Luiza (Análise pré-aprovação Magalu)",
     "consultor_setor": "varejo",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=21, hours=18)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 1},
    {"inquiry_id": "INQ_GABS_008", "consumer_id": DEMO_USER_ID,
     "consultor": "Caixa Econômica Federal (Crédito consignado)",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=25, hours=10)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_009", "consumer_id": DEMO_USER_ID,
     "consultor": "TIM Brasil (Plano pós-pago Black)",
     "consultor_setor": "telecom",
     "motivo": "contratacao",
     "data_consulta": ts(now - timedelta(days=27, hours=14)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_010", "consumer_id": DEMO_USER_ID,
     "consultor": "C6 Bank (Portabilidade de salário)",
     "consultor_setor": "financeiro",
     "motivo": "contratacao",
     "data_consulta": ts(now - timedelta(days=29, hours=12)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_011", "consumer_id": DEMO_USER_ID,
     "consultor": "Itaú Unibanco (Monitoramento Personnalité)",
     "consultor_setor": "financeiro",
     "motivo": "monitoramento",
     "data_consulta": ts(now - timedelta(days=30, hours=8)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    # ANOMALIA — id FIXO, cross-referenciada por starter + guardrail + FraudAlert.
    # Consulta às 03:27 da madrugada, financeira não-bancária, sem autorização.
    {"inquiry_id": "INQ_GABS_FASTCASH", "consumer_id": DEMO_USER_ID,
     "consultor": "Financeira FastCash",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts((now - timedelta(days=4)).replace(hour=3, minute=27, second=0, microsecond=0)),  # 03:27 da madrugada (UTC), suspeito
     "autorizada": "nao", "status": "registrada", "severidade_anomalia": 8},
]


# ═══════════════════════════════════════════════════════════════════════════
#  FRAUD ALERTS — alertas ativos do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

FRAUD_ALERTS = [
    {
        "alert_id": "ALERT_GABS_001",
        "consumer_id": DEMO_USER_ID,
        "inquiry_id": "INQ_GABS_FASTCASH",
        "tipo": "consulta_suspeita",
        "severidade": "alta",
        "data_alerta": ts((now - timedelta(days=4)).replace(hour=3, minute=29, second=0, microsecond=0)),
        "status": "aberto",
        "descricao": (
            "Consulta ao CPF do cliente às 03:27 da madrugada pela Financeira FastCash "
            "(financeira não-bancária), com motivo declarado de aprovação de crédito e "
            "SEM autorização registrada. Horário, perfil do consultor e ausência de relacionamento "
            "prévio fogem totalmente do padrão do cliente (consultas habituais são diurnas, de "
            "bancos com vínculo). Severidade de anomalia 8 de 10. Indício clássico de tentativa de "
            "abertura de crédito por terceiro usando o CPF do titular."
        ),
        "acao_sugerida": (
            "Contestar a consulta da FastCash via dispute_inquiry, elevar o alerta antifraude e "
            "considerar bloqueio cautelar de novas aberturas de crédito até a investigação fechar."
        ),
    },
    {
        "alert_id": "ALERT_GABS_002",
        "consumer_id": DEMO_USER_ID,
        "inquiry_id": "INQ_GABS_FASTCASH",
        "tipo": "cpf_em_lista_vazada",
        "severidade": "alta",
        "data_alerta": ts(now - timedelta(days=11)),
        "status": "em_analise",
        "descricao": (
            "Monitoramento de Dark Web encontrou os dados do cliente em um pacote vazado de um "
            "e-commerce de varejo, com cerca de 12,8 milhões de registros, posto à venda em fórum "
            "de credenciais há 11 dias. O registro do titular expõe a combinação completa: CPF, "
            "e-mail cadastrado, telefone celular, data de nascimento e hash de senha. NÃO há número "
            "de cartão de crédito no vazamento (nenhum dado de cartão exposto), o que afasta o risco "
            "de compra fraudulenta direta, mas concentra o risco na engenharia social e na tentativa "
            "de abertura de crédito em nome do titular. Este vazamento está CORRELACIONADO com a "
            "consulta anômala da FastCash às 03:27 da madrugada (alerta ALERT_GABS_001 / consulta "
            "INQ_GABS_FASTCASH): o conjunto de dados exposto é exatamente o suficiente pra um fraudador "
            "se passar pelo titular e disparar uma solicitação de crédito não autorizada. Padrão "
            "típico de vazamento seguido de tentativa de uso indevido em poucos dias."
        ),
        "acao_sugerida": (
            "Trocar imediatamente a senha reutilizada, reforçar o antifraude e o monitoramento "
            "noturno, contestar a consulta da FastCash e avaliar bloqueio cautelar de novas "
            "aberturas de crédito. Como Premium Plus, o cliente já tem seguro fraude com cobertura "
            "de até R$ 50.000: vale acionar a cobertura preventivamente e manter o monitoramento de "
            "Dark Web ativo pra novos vazamentos do mesmo pacote."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  NEGOTIATION HISTORY — precedente do proprio Gabriel (acordo antigo ja quitado)
#  + 1 da Tatiane. O acordo do Gabriel (now - 400d, quitado/em_dia) da lastro pro
#  "voce ja fez isso e deu certo" quando ele aceitar uma proposta nova.
#  protocolo derivado da data relativa (anti-staleness, formato SX-AAAAMMDD-XXXXXX).
# ═══════════════════════════════════════════════════════════════════════════

_GABS_NEG_DATE = now - timedelta(days=400)

NEGOTIATION_HISTORY = [
    {
        "negotiation_id": "NEG_GABS_001",
        "consumer_id": DEMO_USER_ID,
        "creditor_id": "CRED_VIVO",
        "proposal_id": None,
        "debt_id": None,
        "pending_id": None,
        "data_acordo": ts(_GABS_NEG_DATE),
        "valor_acordado": 198.70,
        "modalidade": "à_vista",
        "protocolo": f"SX-{_GABS_NEG_DATE.strftime('%Y%m%d')}-GABS01",
        "status_pagamento": "quitado",
        "score_impact_real": 21,
    },
    {
        "negotiation_id": "NEG_TATI_001",
        "consumer_id": "CUST_004",
        "creditor_id": "CRED_BRADESCO_SAUDE",
        "proposal_id": None,
        "debt_id": "DBT_005",
        "pending_id": None,
        "data_acordo": ts(now - timedelta(days=20)),
        "valor_acordado": 670.00,
        "modalidade": "parcelado_3x",
        "protocolo": "SX-20260520-T4T1AN",
        "status_pagamento": "em_dia",
        "score_impact_real": 18,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE (CreditFeatures) — features online do Gabriel
#  Os 6 f_* alimentam o Serasa Score e o motor de decisão do eCred.
#  score_calculado = round(1000 * sum(f_x * peso_x)) sobre os 6 pesos oficiais.
#  Calibrado pra dar 692 (faixa Bom, faltam ~9 pts pra Excelente em 701):
#  f_dividas 0.40 e f_busca_credito 0.42 são os 2 que mais seguram o score.
#  Quitar a dívida negativada sobe f_dividas (0.40 -> ~0.62) e derruba a
#  inadimplencia_setor_atual: no recompute o score cruza 701 (bom -> excelente).
# ═══════════════════════════════════════════════════════════════════════════

def _compute_score(feats: dict[str, float]) -> int:
    total = (
        feats["f_cadastro_positivo"] * SCORE_WEIGHTS["cadastro_positivo"]
        + feats["f_experiencia_mercado"] * SCORE_WEIGHTS["experiencia_mercado"]
        + feats["f_dividas"] * SCORE_WEIGHTS["dividas"]
        + feats["f_busca_credito"] * SCORE_WEIGHTS["busca_credito"]
        + feats["f_dados_cadastrais"] * SCORE_WEIGHTS["dados_cadastrais"]
        + feats["f_contratos"] * SCORE_WEIGHTS["contratos"]
    )
    return int(round(1000 * total))


_GABS_FEATURES = {
    "f_cadastro_positivo": 0.90,
    "f_experiencia_mercado": 0.78,
    "f_dividas": 0.40,  # a dívida negativada segura aqui; quitar sobe pra ~0.62
    "f_busca_credito": 0.42,
    "f_dados_cadastrais": 0.92,
    "f_contratos": 0.60,
}  # score_calculado = 692 (faixa Bom). Top-2 que seguram: dívidas + busca de crédito.

FEATURE_STORE = [
    {
        "consumer_id": DEMO_USER_ID,
        **_GABS_FEATURES,
        "score_calculado": _compute_score(_GABS_FEATURES),
        "faixa": faixa_oficial(_compute_score(_GABS_FEATURES)),
        "propensao_cartao": 0.74,
        "propensao_emprestimo": 0.28,
        "propensao_consignado": 0.10,
        "renda_estimada": 3800.00,
        "inadimplencia_setor_atual": 0.45,  # alta por causa da negativada; quitar derruba pra ~0.10
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  CADASTRO POSITIVO — carne do peso de maior impacto do Serasa Score (29%).
#  11 registros do Gabriel: contas recorrentes pagas em dia + um financiamento
#  quitado. Justifica f_cadastro_positivo=0.90 (Premium Plus há 6 anos, contas em
#  dia). Lido pelas tools custom via FT.SEARCH por consumer_id/categoria. Datas
#  RELATIVAS only.
# ═══════════════════════════════════════════════════════════════════════════

CADASTRO_POSITIVO = [
    {"record_id": "CP_GABS_ENEL", "consumer_id": DEMO_USER_ID, "categoria": "utilities",
     "credor": "Enel Distribuição SP", "valor": 218.40, "status": "em_dia", "meses_em_dia": 36,
     "ultima_atualizacao": ts(now - timedelta(days=3))},
    {"record_id": "CP_GABS_SABESP", "consumer_id": DEMO_USER_ID, "categoria": "utilities",
     "credor": "Sabesp (água e esgoto)", "valor": 96.70, "status": "em_dia", "meses_em_dia": 34,
     "ultima_atualizacao": ts(now - timedelta(days=5))},
    {"record_id": "CP_GABS_COMGAS", "consumer_id": DEMO_USER_ID, "categoria": "utilities",
     "credor": "Comgás (gás encanado)", "valor": 74.20, "status": "em_dia", "meses_em_dia": 30,
     "ultima_atualizacao": ts(now - timedelta(days=6))},
    {"record_id": "CP_GABS_VIVO_FIBRA", "consumer_id": DEMO_USER_ID, "categoria": "telecom",
     "credor": "Vivo Fibra", "valor": 129.90, "status": "em_dia", "meses_em_dia": 28,
     "ultima_atualizacao": ts(now - timedelta(days=4))},
    {"record_id": "CP_GABS_VIVO_MOVEL", "consumer_id": DEMO_USER_ID, "categoria": "telecom",
     "credor": "Vivo Controle (celular)", "valor": 59.90, "status": "em_dia", "meses_em_dia": 41,
     "ultima_atualizacao": ts(now - timedelta(days=7))},
    {"record_id": "CP_GABS_NETFLIX", "consumer_id": DEMO_USER_ID, "categoria": "streaming",
     "credor": "Netflix", "valor": 44.90, "status": "em_dia", "meses_em_dia": 26,
     "ultima_atualizacao": ts(now - timedelta(days=2))},
    {"record_id": "CP_GABS_SPOTIFY", "consumer_id": DEMO_USER_ID, "categoria": "streaming",
     "credor": "Spotify Premium", "valor": 21.90, "status": "em_dia", "meses_em_dia": 33,
     "ultima_atualizacao": ts(now - timedelta(days=2))},
    {"record_id": "CP_GABS_FACULDADE", "consumer_id": DEMO_USER_ID, "categoria": "educacao",
     "credor": "Mensalidade pós-graduação FIAP", "valor": 690.00, "status": "em_dia", "meses_em_dia": 18,
     "ultima_atualizacao": ts(now - timedelta(days=9))},
    {"record_id": "CP_GABS_CARTAO", "consumer_id": DEMO_USER_ID, "categoria": "cartao",
     "credor": "Cartão Sem Anuidade Serasa eCred", "valor": 1240.00, "status": "em_dia", "meses_em_dia": 22,
     "ultima_atualizacao": ts(now - timedelta(days=1))},
    {"record_id": "CP_GABS_SEGURO_AUTO", "consumer_id": DEMO_USER_ID, "categoria": "seguro",
     "credor": "Porto Seguro Auto", "valor": 187.50, "status": "em_dia", "meses_em_dia": 24,
     "ultima_atualizacao": ts(now - timedelta(days=12))},
    {"record_id": "CP_GABS_FINANC_CARRO", "consumer_id": DEMO_USER_ID, "categoria": "financiamento",
     "credor": "Financiamento de veículo Santander", "valor": 0.00, "status": "quitado", "meses_em_dia": 48,
     "ultima_atualizacao": ts(now - timedelta(days=110))},
]


# ═══════════════════════════════════════════════════════════════════════════
#  CREDIT OFFERS (eCred catalog) — o motor de decisão filtra/rankeia sobre isso.
#  Marcas brasileiras reais com diferenciais concretos. A LÓGICA de gating é
#  preservada: rank_ecred_offers filtra por faixa_minima/renda_minima/publico_alvo,
#  respeita opt_outs e rankeia por fit (propensão + público-alvo casando com a faixa).
#
#  Calibrado pro Gabriel (Score 692 Bom, renda 3800, propensao_cartao 0.74,
#  opt-out emprestimo_pessoal + consignado):
#   • HOJE vence o "PagBank Cartão Sem Anuidade" (cartao, publico_alvo bom,
#     renda_minima 1500): único cartão de público 'bom' ELEGÍVEL pro Gabriel,
#     logo fit_score máximo (publico_match 1.0 + propensao_cartao 0.74).
#   • Os demais cartões 'bom' (Mercado Pago, Santander SX) têm renda_minima > 3800,
#     ficam INELEGÍVEIS hoje e não disputam o topo (sort determinístico).
#   • "Nubank Ultravioleta" (cartao premium, gated em EXCELENTE, renda_minima 3500)
#     fica TRAVADO na faixa Bom e SÓ desbloqueia depois que o recompute cruza pra
#     Excelente (renda 3800 já cobre os 3500). "C6 Carbon" idem, gated em excelente.
#   • Empréstimo (Crefisa, taxa alta) e consignado/FGTS (Caixa) existem no catálogo
#     mas são opt-out do Gabriel (LTM), então o motor os pula.
# ═══════════════════════════════════════════════════════════════════════════

CREDIT_OFFERS = [
    # ── Cartões de público 'bom' ──────────────────────────────────────────
    # VENCEDOR HOJE pro Gabriel: único cartão 'bom' elegível (renda_minima <= 3800).
    {"offer_id": "OFFER_PAGBANK_SEM_ANUIDADE", "partner_name": "PagBank Cartão Sem Anuidade",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "bom", "renda_minima": 1500.00,
     "publico_alvo": "bom", "valor_max": 8000.00, "status": "ativa"},
    # Demais cartões 'bom' ficam INELEGÍVEIS pro Gabriel hoje (renda_minima > 3800),
    # então não disputam o topo: o PagBank segue vencedor único.
    {"offer_id": "OFFER_MERCADOPAGO_MEU_LIMITE", "partner_name": "Mercado Pago Cartão Meu Limite",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "bom", "renda_minima": 4200.00,
     "publico_alvo": "bom", "valor_max": 12000.00, "status": "ativa"},
    {"offer_id": "OFFER_SANTANDER_SX", "partner_name": "Santander SX",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "bom", "renda_minima": 4500.00,
     "publico_alvo": "bom", "valor_max": 15000.00, "status": "ativa"},
    {"offer_id": "OFFER_ITAU_CLICK", "partner_name": "Itaú Click Cartão Digital",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "bom", "renda_minima": 5000.00,
     "publico_alvo": "bom", "valor_max": 16000.00, "status": "ativa"},

    # ── Cartões premium gated em EXCELENTE (travados na faixa Bom do Gabriel) ──
    # Nubank Ultravioleta: o "premium sem anuidade vitalícia" da narrativa.
    # renda_minima 3500 <= 3800, então SÓ a faixa segura: desbloqueia no recompute.
    {"offer_id": "OFFER_NUBANK_ULTRAVIOLETA", "partner_name": "Nubank Ultravioleta (premium sem anuidade vitalícia, cashback 1%)",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "excelente", "renda_minima": 3500.00,
     "publico_alvo": "excelente", "valor_max": 18000.00, "status": "ativa"},
    {"offer_id": "OFFER_C6_CARBON", "partner_name": "C6 Carbon (cartão premium, salas VIP e pontos Átomos)",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "excelente", "renda_minima": 6000.00,
     "publico_alvo": "excelente", "valor_max": 30000.00, "status": "ativa"},
    {"offer_id": "OFFER_INTER_BLACK", "partner_name": "Banco Inter Black (cartão premium, cashback e cancelamento sem custo)",
     "produto": "cartao", "taxa_min_aa": 0.0, "faixa_minima": "excelente", "renda_minima": 8000.00,
     "publico_alvo": "excelente", "valor_max": 40000.00, "status": "ativa"},

    # ── Conta digital (público bom, sem renda mínima) ─────────────────────────
    {"offer_id": "OFFER_WILL_BANK_CONTA", "partner_name": "Will Bank Conta Digital Sem Tarifa",
     "produto": "conta_digital", "taxa_min_aa": 0.0, "faixa_minima": "baixo", "renda_minima": 0.00,
     "publico_alvo": "bom", "valor_max": 0.00, "status": "ativa"},

    # ── Empréstimo / consignado / FGTS (opt-out do Gabriel: o motor pula) ─────
    {"offer_id": "OFFER_CREFISA_PESSOAL", "partner_name": "Crefisa Empréstimo Pessoal (liberação na hora, taxa alta)",
     "produto": "emprestimo_pessoal", "taxa_min_aa": 215.0, "faixa_minima": "regular", "renda_minima": 1200.00,
     "publico_alvo": "bom", "valor_max": 25000.00, "status": "ativa"},
    {"offer_id": "OFFER_CAIXA_CONSIGNADO", "partner_name": "Caixa Crédito Consignado (desconto em folha, menor taxa)",
     "produto": "consignado", "taxa_min_aa": 19.9, "faixa_minima": "regular", "renda_minima": 1800.00,
     "publico_alvo": "bom", "valor_max": 50000.00, "status": "ativa"},
    {"offer_id": "OFFER_CAIXA_FGTS", "partner_name": "Caixa Antecipação Saque-Aniversário FGTS",
     "produto": "fgts", "taxa_min_aa": 18.0, "faixa_minima": "regular", "renda_minima": 1000.00,
     "publico_alvo": "bom", "valor_max": 12000.00, "status": "ativa"},

    # ── Cartão pra negativado (recomeço) ──────────────────────────────────────
    {"offer_id": "OFFER_MERCADOPAGO_GARANTIDO", "partner_name": "Mercado Pago Cartão Garantido (limite pelo saldo, pra quem está negativado)",
     "produto": "cartao_negativado", "taxa_min_aa": 0.0, "faixa_minima": "baixo", "renda_minima": 0.00,
     "publico_alvo": "negativado", "valor_max": 1500.00, "status": "ativa"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  OFFER MATCH — vazio no seed; preenchido em runtime pelo rank_ecred_offers
# ═══════════════════════════════════════════════════════════════════════════

OFFER_MATCH: list[dict] = []


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES — embedding gerado em runtime
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_SCORE", "title": "Serasa Score: os 6 pesos do cálculo", "category": "score",
        "content": (
            "O Serasa Score vai de 0 a 1000 e é calculado a partir de 6 dimensões com pesos "
            "oficiais: Cadastro Positivo (29%), experiência de mercado (24%), dívidas (21%), "
            "busca de crédito (12%), dados cadastrais (8%) e contratos (6%). Faixas oficiais: "
            "0-300 baixo, 301-500 regular, 501-700 bom, 701-1000 excelente. Manter o Cadastro "
            "Positivo ativo e contas pagas em dia é o que mais ajuda. Reduzir dívidas em aberto "
            "e evitar muitas consultas de crédito em pouco tempo também sobem o score."
        ),
    },
    {
        "policy_id": "POL_ECRED", "title": "Serasa eCred: marketplace de crédito personalizado", "category": "ecred",
        "content": (
            "O Serasa eCred é o marketplace de crédito do Serasa: cruza o seu perfil (score, faixa, "
            "renda estimada e propensões) com o catálogo de ofertas dos parceiros e mostra só o que "
            "tem chance real de aprovação pra você, com a probabilidade estimada. Produtos comuns: "
            "cartão de crédito (inclusive sem anuidade), empréstimo pessoal, consignado, antecipação "
            "do saque-aniversário do FGTS, conta digital e cartão pra quem está negativado. O eCred "
            "respeita suas preferências: se você não quer um tipo de produto, ele não aparece."
        ),
    },
    {
        "policy_id": "POL_LIMPA_RT", "title": "Limpa Nome Real-Time: como funciona", "category": "limpa_nome",
        "content": (
            "O Limpa Nome Real-Time consulta de forma concorrente todos os credores parceiros do "
            "Serasa (full e realtime_only) e descobre pendências em aberto antes que virem "
            "negativações. Tipicamente encontra faturas finais pós-cancelamento, devoluções não "
            "processadas e estornos pendurados. As pendências descobertas vêm com proposta de "
            "quitação já calculada baseada na política de desconto do credor. Aceitar a proposta "
            "fecha o ciclo em segundos e não permite que o item vire negativação. Disponível pra "
            "clientes Premium e Premium Plus."
        ),
    },
    {
        "policy_id": "POL_LIMPA_TRAD", "title": "Limpa Nome tradicional (dívidas negativadas)", "category": "limpa_nome",
        "content": (
            "Pra dívidas que já viraram negativação, o Limpa Nome agrega ofertas de credores "
            "parceiros. O desconto típico varia por setor: varejo até 80%, telecom até 70%, "
            "financeiro até 60%, saúde até 25%, energia até 30%. Cliente pode aceitar à vista ou "
            "parcelado (até 12x dependendo do credor). A remoção da negativação ocorre em até 5 "
            "dias úteis após confirmação do pagamento."
        ),
    },
    {
        "policy_id": "POL_MONITORAMENTO", "title": "Monitoramento de CPF: alertas em tempo real", "category": "monitoramento",
        "content": (
            "Clientes com monitoramento ativo recebem alerta sempre que: (1) o CPF é consultado por "
            "alguma empresa; (2) uma nova dívida é registrada; (3) há tentativa de abertura de crédito. "
            "Premium Plus inclui monitoramento noturno (24x7), alerta de uso suspeito do CPF em padrão "
            "anômalo, monitoramento de vazamento na Dark Web e proteção contra fraude com cobertura "
            "financeira."
        ),
    },
    {
        "policy_id": "POL_ANTIFRAUDE", "title": "Antifraude: contestação de consultas e Dark Web", "category": "antifraude",
        "content": (
            "Cliente pode contestar qualquer consulta ao CPF que não tenha autorizado. A contestação "
            "abre um chamado e a consulta fica marcada como em_disputa enquanto investigada. Se "
            "confirmada como fraude, o registro é removido e um alerta é elevado pra severidade "
            "crítica. O monitoramento de Dark Web avisa quando o CPF aparece em listas vazadas. "
            "Premium Plus inclui seguro fraude com cobertura de até R$ 50.000."
        ),
    },
    {
        "policy_id": "POL_CADASTRO_POSITIVO", "title": "Cadastro Positivo: opt-in e benefícios", "category": "score",
        "content": (
            "O Cadastro Positivo é um registro do histórico de pagamento em dia (contas de luz, água, "
            "telefone, financiamentos, faturas pagas no prazo). É o peso de maior impacto no Serasa "
            "Score (29%). Mantê-lo ativo costuma adicionar pontos relevantes ao score. Pode ser "
            "desativado a qualquer momento."
        ),
    },
    {
        "policy_id": "POL_LGPD", "title": "LGPD e direitos do titular", "category": "lgpd",
        "content": (
            "O Serasa atua como controlador de dados sob a LGPD. O titular pode a qualquer momento "
            "solicitar: acesso aos dados, retificação, anonimização, portabilidade pra outro órgão de "
            "proteção ao crédito, revogação de consentimentos específicos e eliminação de dados "
            "(sujeito a obrigações legais de retenção). Solicitações são atendidas em até 15 dias."
        ),
    },
    {
        "policy_id": "POL_PREMIUM", "title": "Premium e Premium Plus: diferenças", "category": "premium",
        "content": (
            "Premium: Limpa Nome Real-Time, monitoramento básico, consultas ilimitadas ao próprio "
            "score. Premium Plus: tudo do Premium + monitoramento noturno 24x7, monitoramento de "
            "Dark Web, seguro fraude até R$ 50K, contestação prioritária de consultas, atendimento "
            "humano dedicado e relatório mensal de evolução do score com recomendações pra subir."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — escreve JSONLs
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} registros")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={safe_value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    print("Gerando embeddings das políticas...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Escrevendo arquivos JSONL:")
    write_jsonl(resolved_output_dir, "consumers.jsonl", CONSUMERS)
    write_jsonl(resolved_output_dir, "creditors.jsonl", CREDITORS)
    write_jsonl(resolved_output_dir, "debts.jsonl", DEBTS)
    write_jsonl(resolved_output_dir, "pending_debts.jsonl", PENDING_DEBTS)
    write_jsonl(resolved_output_dir, "proposals.jsonl", PROPOSALS)
    write_jsonl(resolved_output_dir, "score_history.jsonl", SCORE_HISTORY)
    write_jsonl(resolved_output_dir, "score_factors.jsonl", SCORE_FACTORS)
    write_jsonl(resolved_output_dir, "inquiries.jsonl", INQUIRIES)
    write_jsonl(resolved_output_dir, "fraud_alerts.jsonl", FRAUD_ALERTS)
    write_jsonl(resolved_output_dir, "negotiation_history.jsonl", NEGOTIATION_HISTORY)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "cadastro_positivo.jsonl", CADASTRO_POSITIVO)
    write_jsonl(resolved_output_dir, "offers.jsonl", CREDIT_OFFERS)
    write_jsonl(resolved_output_dir, "offer_match.jsonl", OFFER_MATCH)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CONSUMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["consumer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['name']} ({demo['consumer_id']}), Score {demo['score']} ({demo['score_faixa']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["consumer_id"],
            "DEMO_USER_NAME": demo["name"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "consumers": len(CONSUMERS),
            "creditors": len(CREDITORS),
            "debts": len(DEBTS),
            "pending_debts": len(PENDING_DEBTS),
            "proposals": len(PROPOSALS),
            "score_history": len(SCORE_HISTORY),
            "score_factors": len(SCORE_FACTORS),
            "inquiries": len(INQUIRIES),
            "fraud_alerts": len(FRAUD_ALERTS),
            "negotiation_history": len(NEGOTIATION_HISTORY),
            "feature_store": len(FEATURE_STORE),
            "cadastro_positivo": len(CADASTRO_POSITIVO),
            "offers": len(CREDIT_OFFERS),
            "offer_match": len(OFFER_MATCH),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
