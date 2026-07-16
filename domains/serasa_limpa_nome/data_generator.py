"""Limpa Nome IA — seed sintético em PT-BR.

Persona principal: Gabriel Cerioni, score 950 (Excelente), Premium há 6 anos.
Sem dívidas negativadas, mas com 3 pendências "esquecidas" que aparecem só na
descoberta real-time (gancho do demo).

Stack: 11 entidades, ~30 registros estáticos + tools determinísticas escrevem
runtime via UnifiedClient.import_data.
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

OUTPUT_DIR = ROOT / "output" / "serasa_limpa_nome"


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
        "score": 950,
        "score_faixa": "excelente",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium_plus",
        "premium_since_years": 6,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
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
        "score_faixa": "muito_baixo",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium",
        "premium_since_years": 1,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
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
        "score_faixa": "bom",
        "monitoramento_ativo": "sim",
        "premium_tier": "premium",
        "premium_since_years": 2,
        "cadastro_positivo_ativo": "sim",
        "antifraude_ativo": "sim",
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
#  DEBTS — dívidas negativadas (Gabriel não tem, outros têm)
# ═══════════════════════════════════════════════════════════════════════════

DEBTS = [
    # Camila (CUST_002) — 3 negativações
    {"debt_id": "DBT_001", "consumer_id": "CUST_002", "creditor_id": "CRED_RIACHUELO",
     "descricao": "Cartão Riachuelo: parcelado em atraso desde fev/2026",
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
#
# Esses 3 itens são a magia da demo: Gabriel score 950, "limpo", mas tem 3
# pequenas pendências escondidas que NUNCA viraram negativação ainda. Real-time
# discovery encontra. Cliente resolve em 2 cliques.

PENDING_DEBTS = [
    {
        "pending_id": "PEND_GABS_001", "consumer_id": DEMO_USER_ID, "creditor_id": "CRED_TIM",
        "descricao": "Fatura final TIM Pós: plano cancelado em jul/2024, última fatura não migrou pra cobrança",
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
        "descricao": "Claro NET Combo Família: cancelamento mal processado, equipamento devolvido mas última mensalidade em aberto",
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
        "descricao": "Devolução Magalu não processada: produto retornado mas estorno parcial pendente",
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
    # Gabriel — 1 proposta por pending
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
#  SCORE HISTORY — 6 meses do Gabriel (estável na faixa excelente)
# ═══════════════════════════════════════════════════════════════════════════

def _month_label(months_back: int) -> str:
    base = now.replace(day=15)
    for _ in range(months_back):
        base = (base.replace(day=1) - timedelta(days=1)).replace(day=15)
    return base.strftime("%Y-%m")


SCORE_HISTORY = [
    {"history_id": "SH_GABS_M0", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(0),
     "score": 950, "faixa": "excelente", "variacao": +1,
     "fator_principal": "Histórico de pagamento em dia + Cadastro Positivo ativo"},
    {"history_id": "SH_GABS_M1", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(1),
     "score": 949, "faixa": "excelente", "variacao": -2,
     "fator_principal": "Aumento de consultas ao CPF no mês"},
    {"history_id": "SH_GABS_M2", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(2),
     "score": 951, "faixa": "excelente", "variacao": +3,
     "fator_principal": "Tempo de relacionamento financeiro longo"},
    {"history_id": "SH_GABS_M3", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(3),
     "score": 948, "faixa": "excelente", "variacao": +13,
     "fator_principal": "Quitação de financiamento (auto) atualizada no histórico"},
    {"history_id": "SH_GABS_M4", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(4),
     "score": 935, "faixa": "excelente", "variacao": +15,
     "fator_principal": "Inclusão de novo cartão Black com limite alto"},
    {"history_id": "SH_GABS_M5", "consumer_id": DEMO_USER_ID, "mes_referencia": _month_label(5),
     "score": 920, "faixa": "excelente", "variacao": 0,
     "fator_principal": "Padrão estável de utilização de crédito"},
    # Camila — declínio
    {"history_id": "SH_CAMI_M0", "consumer_id": "CUST_002", "mes_referencia": _month_label(0),
     "score": 458, "faixa": "regular", "variacao": -54,
     "fator_principal": "3 negativações ativas: Riachuelo, Claro, Americanas"},
    {"history_id": "SH_CAMI_M1", "consumer_id": "CUST_002", "mes_referencia": _month_label(1),
     "score": 512, "faixa": "regular", "variacao": -38,
     "fator_principal": "Atraso > 90 dias em conta Americanas"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  SCORE FACTORS — o que afeta o score do Gabriel AGORA (todos positivos)
# ═══════════════════════════════════════════════════════════════════════════

SCORE_FACTORS = [
    {"factor_id": "SF_GABS_001", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Histórico de pagamento 100% em dia nos últimos 36 meses",
     "peso_estimado": 180, "categoria": "pagamento"},
    {"factor_id": "SF_GABS_002", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Diversidade alta de produtos financeiros (cartões, conta corrente, investimentos)",
     "peso_estimado": 95, "categoria": "diversidade"},
    {"factor_id": "SF_GABS_003", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Relacionamento financeiro estabelecido há mais de 15 anos",
     "peso_estimado": 110, "categoria": "tempo"},
    {"factor_id": "SF_GABS_004", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Comprovação de renda alta e estável (perfil Personnalité Itaú Nível 5)",
     "peso_estimado": 75, "categoria": "renda"},
    {"factor_id": "SF_GABS_005", "consumer_id": DEMO_USER_ID, "tipo": "positivo",
     "descricao": "Cadastro Positivo ativo com 6 anos de histórico",
     "peso_estimado": 60, "categoria": "cadastro_positivo"},
    {"factor_id": "SF_GABS_006", "consumer_id": DEMO_USER_ID, "tipo": "negativo",
     "descricao": "Volume médio-alto de consultas ao CPF nos últimos 90 dias",
     "peso_estimado": -10, "categoria": "consultas"},
    # Camila — fatores
    {"factor_id": "SF_CAMI_001", "consumer_id": "CUST_002", "tipo": "negativo",
     "descricao": "3 negativações ativas em diferentes setores",
     "peso_estimado": -135, "categoria": "pagamento"},
    {"factor_id": "SF_CAMI_002", "consumer_id": "CUST_002", "tipo": "positivo",
     "descricao": "Cadastro Positivo ativo recentemente",
     "peso_estimado": 25, "categoria": "cadastro_positivo"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  INQUIRIES — quem consultou o CPF do Gabriel
# ═══════════════════════════════════════════════════════════════════════════

INQUIRIES = [
    {"inquiry_id": "INQ_GABS_001", "consumer_id": DEMO_USER_ID,
     "consultor": "Itaú Unibanco (Personnalité)",
     "consultor_setor": "financeiro",
     "motivo": "monitoramento",
     "data_consulta": ts(now - timedelta(days=2, hours=4)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_002", "consumer_id": DEMO_USER_ID,
     "consultor": "Banco Inter (Crédito Imobiliário)",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=8, hours=10)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_003", "consumer_id": DEMO_USER_ID,
     "consultor": "C6 Bank (Portabilidade de Salário)",
     "consultor_setor": "financeiro",
     "motivo": "contratacao",
     "data_consulta": ts(now - timedelta(days=15, hours=14)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 0},
    {"inquiry_id": "INQ_GABS_004", "consumer_id": DEMO_USER_ID,
     "consultor": "Magazine Luiza (Análise pré-aprovação)",
     "consultor_setor": "varejo",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=22, hours=18)),
     "autorizada": "sim", "status": "registrada", "severidade_anomalia": 1},
    {"inquiry_id": "INQ_GABS_005", "consumer_id": DEMO_USER_ID,
     "consultor": "Financeira Crédito Rápido FastCash",
     "consultor_setor": "financeiro",
     "motivo": "aprovacao_credito",
     "data_consulta": ts(now - timedelta(days=4, hours=3, minutes=27)),  # 3h da manhã, suspeito
     "autorizada": "nao", "status": "registrada", "severidade_anomalia": 8},
]


# ═══════════════════════════════════════════════════════════════════════════
#  FRAUD ALERTS — 1 alerta ativo do Gabriel (da consulta suspeita)
# ═══════════════════════════════════════════════════════════════════════════

FRAUD_ALERTS = [
    {
        "alert_id": "ALERT_GABS_001",
        "consumer_id": DEMO_USER_ID,
        "inquiry_id": "INQ_GABS_005",
        "tipo": "consulta_suspeita",
        "severidade": "alta",
        "data_alerta": ts(now - timedelta(days=4, hours=2)),
        "status": "aberto",
        "descricao": (
            "Consulta ao CPF realizada às 03:27 da madrugada por financeira não-bancária "
            "(FastCash), padrão fora do habitual do cliente. Sem autorização registrada."
        ),
        "acao_sugerida": "Contestar a consulta via dispute_inquiry e ativar alerta de fraude.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  NEGOTIATION HISTORY — vazio pro Gabriel (nunca negociou) + 1 da Tatiane
# ═══════════════════════════════════════════════════════════════════════════

NEGOTIATION_HISTORY = [
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
        "protocolo": "LN-20260520-T4T1AN",
        "status_pagamento": "em_dia",
        "score_impact_real": 18,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — embedding gerado em runtime
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "Limpa Nome Real-Time: Como funciona", "category": "limpa_nome",
        "content": (
            "O Limpa Nome Real-Time consulta de forma concorrente todos os credores parceiros do "
            "Serasa (full e realtime_only) e descobre pendências em aberto antes que virem "
            "negativações. Tipicamente encontra faturas finais pós-cancelamento, devoluções não "
            "processadas e estornos pendurados. As pendências descobertas vêm com proposta de "
            "quitação já calculada baseada na política de desconto do credor. Aceitar a proposta "
            "via 'simulate_proposal_accept' fecha o ciclo em segundos e não permite que o item "
            "vire negativação. Disponível pra todos os clientes Premium e Premium Plus."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Limpa Nome tradicional (dívidas negativadas)", "category": "limpa_nome",
        "content": (
            "Pra dívidas que já viraram negativação, o Limpa Nome agrega ofertas de credores "
            "parceiros e exibe pra o consumidor escolher. O desconto típico varia por setor: "
            "varejo até 80%, telecom até 70%, financeiro até 60%, saúde até 25%, energia até 30%. "
            "Cliente pode aceitar à vista ou parcelado (até 12x dependendo do credor). A "
            "remoção da negativação ocorre em até 5 dias úteis após confirmação do pagamento."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Score Serasa: fatores que influenciam", "category": "score",
        "content": (
            "O Score Serasa é calculado entre 0 e 1000 com base em 5 dimensões principais: "
            "histórico de pagamento (40%), diversidade e idade dos produtos financeiros (20%), "
            "tempo de relacionamento (15%), comprovação de renda (15%), e Cadastro Positivo / "
            "consultas recentes (10%). Faixas: 0-300 muito baixo, 301-500 baixo, 501-700 regular, "
            "701-900 bom, 901-1000 excelente. Score acima de 950 sinaliza histórico exemplar. "
            "Quitar uma dívida em aberto via Limpa Nome aumenta o score em proporção ao impacto "
            "estimado da dívida (campo score_impact_estimate)."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Monitoramento de CPF: alertas em tempo real", "category": "monitoramento",
        "content": (
            "Clientes com monitoramento ativo recebem alerta via push e e-mail sempre que: "
            "(1) o CPF é consultado por alguma empresa; (2) uma nova dívida é registrada; "
            "(3) há tentativa de abertura de crédito. Premium Plus inclui também monitoramento "
            "noturno (24x7), alerta de uso suspeito do CPF em padrão anômalo, e proteção contra "
            "fraude com cobertura financeira. Configurável no app."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Antifraude: contestação de consultas e proteção", "category": "antifraude",
        "content": (
            "Cliente pode contestar qualquer consulta ao CPF que não tenha autorizado via "
            "dispute_inquiry. A contestação abre um chamado interno e a consulta fica marcada "
            "como em_disputa enquanto investigada. Se confirmada como fraude, o registro é "
            "removido do histórico e um FraudAlert é elevado pra severidade crítica. Premium Plus "
            "inclui seguro fraude com cobertura de até R$ 50.000."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Cadastro Positivo: opt-in e benefícios", "category": "score",
        "content": (
            "O Cadastro Positivo é um registro voluntário do histórico de pagamento em dia "
            "(contas de luz, água, telefone, financiamentos, faturas pagas dentro do prazo). "
            "Mantê-lo ativo costuma adicionar 20 a 80 pontos ao score, dependendo do histórico. "
            "Pode ser desativado a qualquer momento. Clientes Premium têm desbloqueio automático "
            "de fontes adicionais (streaming, varejo digital)."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Score Turbo: produto premium", "category": "premium",
        "content": (
            "Score Turbo é um produto Premium que conecta serviços recorrentes (Netflix, "
            "Spotify, energia, internet) ao Cadastro Positivo automaticamente, dando boost "
            "imediato no score baseado no comportamento de pagamento dessas contas. Cliente "
            "Premium ativa 1x e o Serasa monitora continuamente. Boost típico: 30 a 70 pontos "
            "no primeiro mês após ativação. Recomendado pra quem já tem score >700."
        ),
    },
    {
        "policy_id": "POL_008", "title": "LGPD e direitos do titular", "category": "lgpd",
        "content": (
            "O Serasa atua como controlador de dados sob a LGPD. O titular pode a qualquer "
            "momento solicitar: acesso aos dados, retificação, anonimização, portabilidade pra "
            "outro órgão de proteção ao crédito (Boa Vista, Quod, etc), revogação de "
            "consentimentos específicos, e eliminação de dados (sujeito a obrigações legais "
            "de retenção). Solicitações são atendidas em até 15 dias."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Premium e Premium Plus: diferenças", "category": "premium",
        "content": (
            "Premium (R$ 19,90/mês): Limpa Nome Real-Time, monitoramento básico, sem limite "
            "de consultas ao próprio score, Score Turbo elegível. Premium Plus (R$ 39,90/mês): "
            "tudo do Premium + monitoramento noturno 24x7, seguro fraude até R$ 50K, contestação "
            "prioritária de consultas, atendimento humano dedicado em até 1h útil, e relatório "
            "mensal personalizado de evolução do score com recomendações de ações pra subir de "
            "faixa."
        ),
    },
    {
        "policy_id": "POL_010", "title": "Negociação: modalidades e limites por setor", "category": "limpa_nome",
        "content": (
            "Modalidades aceitas: à vista (desconto máximo), parcelado em 2x, 3x, 6x ou 12x "
            "(desconto reduzido proporcionalmente). Desconto máximo por setor: varejo até 80%, "
            "telecom até 70%, financeiro até 60%, energia até 30%, saúde até 25%. Validade "
            "típica das ofertas: 7 a 30 dias. Cliente pode renegociar uma proposta uma vez, "
            "solicitando modalidade diferente, desconto pode ser ajustado pelo credor."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — escreve JSONLs
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w") as fh:
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
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CONSUMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["consumer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['name']} ({demo['consumer_id']})")
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
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
