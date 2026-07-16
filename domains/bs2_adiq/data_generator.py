"""BS2 Pay (ADA): synthetic merchant/acquiring seed in PT-BR.

Built for an executive demo: the flagship use case is the smart chargeback
defense. Buyer MARCOS VINICIUS P. buys the same product monthly on the
e-commerce with confirmed deliveries; when the latest charge lands in dispute,
the agent assembles the recurrence + delivery evidence (winnable dispute). A
second dispute (carrier lost the package) is the one to refund fast. Secondary
paths: receivables anticipation quote (1.49% p.m. pro-rata over the agenda) and
working capital on top of the BS2 PJ account.

Demo merchant is Cerioni Sports (Gabriel Cerioni, managing partner), an
Adiq Pro sports goods retailer in São Paulo, BS2 Empresas client. All values
are fictitious but plausible. Internal Redis demo, no official affiliation
with Banco BS2 S.A. or Adiq.
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

OUTPUT_DIR = ROOT / "output" / "bs2_adiq"

# Fixed demo anchor: the storyline is pinned to July 2026 (canonical dates such
# as 2026-07-05 and the 2026-07-21 dispute deadline are part of the demo script),
# so the generator uses a fixed "today" instead of datetime.now() and stays fully
# deterministic across runs.
now = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)


def ts(dt: datetime) -> str:
    return dt.isoformat()


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


# Adiq Pro MDR table (%). Single source for transaction and receivable math so
# every valor_liquido in the dataset is consistent with the published rates.
MDR_BY_MODALIDADE = {
    "credito_avista": 2.39,
    "credito_parcelado": 2.99,
    "debito": 1.09,
    "pix": 0.99,
}


# ═══════════════════════════════════════════════════════════════════════════
#  MERCHANTS (3) — demo merchant + 2 fillers for realism
# ═══════════════════════════════════════════════════════════════════════════

DEMO_MERCHANT_ID = "MERCH_DEMO_001"

MERCHANTS = [
    {
        "merchant_id": DEMO_MERCHANT_ID,
        "razao_social": "CERIONI SPORTS COMERCIO DE ARTIGOS ESPORTIVOS LTDA",
        "nome_fantasia": "Cerioni Sports",
        "cnpj_masked": "12.***.***/0001-07",
        "segmento": "artigos_esportivos",
        "plano_adiq": "adiq_pro",
        "cliente_desde": "2020-03",
        "relacionamento_bs2": "bs2_empresas",
        "cidade": "São Paulo",
        "status": "ativo",
        "socio_responsavel": "Gabriel Cerioni",
        "contato_email": "gabriel.cerioni@example.com.br",
    },
    {
        "merchant_id": "MERCH_002",
        "razao_social": "EMPORIO VILA NATURAL ALIMENTOS LTDA",
        "nome_fantasia": "Empório Vila Natural",
        "cnpj_masked": "34.***.***/0001-52",
        "segmento": "alimentacao",
        "plano_adiq": "adiq_flex",
        "cliente_desde": "2022-08",
        "relacionamento_bs2": "bs2_empresas",
        "cidade": "São Paulo",
        "status": "ativo",
        "socio_responsavel": "Helena Duarte Sales",
        "contato_email": "helena.sales@example.com.br",
    },
    {
        "merchant_id": "MERCH_003",
        "razao_social": "OFICINA DUAS RODAS PECAS E SERVICOS LTDA",
        "nome_fantasia": "Oficina Duas Rodas",
        "cnpj_masked": "56.***.***/0001-19",
        "segmento": "autopecas",
        "plano_adiq": "adiq_flex",
        "cliente_desde": "2021-11",
        "relacionamento_bs2": "bs2_empresas",
        "cidade": "Campinas",
        "status": "ativo",
        "socio_responsavel": "Nelson Prado Filho",
        "contato_email": "nelson.prado@example.com.br",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PJ ACCOUNTS — one BS2 settlement/PJ account per merchant
# ═══════════════════════════════════════════════════════════════════════════

PJ_ACCOUNTS = [
    # Cerioni Sports: canonical balances anchoring the working-capital path
    {
        "account_id": "PJACC_001", "merchant_id": DEMO_MERCHANT_ID,
        "banco": "BS2", "agencia": "0001", "conta_masked": "***.***-4",
        "saldo_disponivel": 84300.00, "limite_capital_giro": 200000.00,
        "status": "ativa",
    },
    {
        "account_id": "PJACC_002", "merchant_id": "MERCH_002",
        "banco": "BS2", "agencia": "0001", "conta_masked": "***.***-9",
        "saldo_disponivel": 12750.00, "limite_capital_giro": 40000.00,
        "status": "ativa",
    },
    {
        "account_id": "PJACC_003", "merchant_id": "MERCH_003",
        "banco": "BS2", "agencia": "0001", "conta_masked": "***.***-2",
        "saldo_disponivel": 31200.00, "limite_capital_giro": 75000.00,
        "status": "ativa",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  SALES TRANSACTIONS — core of the demo. 45 sample sales for Cerioni Sports
#  (the full month has 1,086 transactions; the monthly aggregates live in the
#  feature store). Includes the CRITICAL MARCOS VINICIUS P. recurrence: R$ 890
#  monthly on the e-commerce (2026-05-12, 2026-06-10, 2026-07-05), all with
#  confirmed delivery; the July one is in dispute — the winnable chargeback.
# ═══════════════════════════════════════════════════════════════════════════

def _sale(
    i: int,
    data: str,
    valor_bruto: float,
    modalidade: str,
    bandeira: str,
    canal: str,
    cliente_final: str,
    descricao: str,
    *,
    parcelas: int = 1,
    terminal_id: str | None = None,
    status: str = "aprovada",
    entrega: str = "n/a",
) -> dict:
    """Build a sales row; valor_liquido always derives from the MDR table."""
    mdr_pct = MDR_BY_MODALIDADE[modalidade]
    valor_liquido = round(valor_bruto * (1 - mdr_pct / 100), 2)
    return {
        "transaction_id": f"TXN_{i:03d}",
        "merchant_id": DEMO_MERCHANT_ID,
        "data": data,
        "valor_bruto": round(valor_bruto, 2),
        "modalidade": modalidade,
        "parcelas": parcelas,
        "bandeira": bandeira,
        "canal": canal,
        "terminal_id": terminal_id,
        "status": status,
        "nsu": str(731000 + i * 13),
        "cliente_final": cliente_final,
        "descricao": descricao,
        "mdr_pct": mdr_pct,
        "valor_liquido": valor_liquido,
        "entrega": entrega,
    }


SALES_TRANSACTIONS = [
    # --- Prior months (Marcos recurrence starts here) ---
    _sale(1, "2026-05-12", 890.00, "credito_avista", "visa", "ecommerce",
          "MARCOS VINICIUS P.", "Chuteira de campo profissional",
          entrega="confirmada:BR845201337SP"),
    _sale(2, "2026-05-28", 1240.00, "credito_parcelado", "mastercard", "pos",
          "LUIZ H. BARROS", "Esteira dobrável compacta",
          parcelas=3, terminal_id="TERM_001"),
    _sale(3, "2026-06-10", 890.00, "credito_avista", "visa", "ecommerce",
          "MARCOS VINICIUS P.", "Chuteira de campo profissional",
          entrega="confirmada:BR861774209SP"),
    _sale(4, "2026-06-18", 456.70, "debito", "elo", "pos",
          "PAULA R. MENDES", "Kit raquetes de beach tennis",
          terminal_id="TERM_002"),
    _sale(5, "2026-06-25", 320.00, "pix", "pix", "ecommerce",
          "THIAGO A. NUNES", "Camisa oficial + meião",
          entrega="confirmada:BR867310992SP"),

    # --- July 2026 (current cycle) ---
    _sale(6, "2026-07-01", 429.90, "credito_avista", "visa", "ecommerce",
          "CAMILA S. ROCHA", "Tênis de corrida amortecido",
          entrega="confirmada:BR870114523SP"),
    _sale(7, "2026-07-01", 189.90, "debito", "mastercard", "pos",
          "RAFAEL T. GOMES", "Bola de futebol de campo",
          terminal_id="TERM_001"),
    _sale(8, "2026-07-01", 356.00, "pix", "pix", "ecommerce",
          "BRUNO C. FARIA", "Agasalho esportivo masculino",
          entrega="confirmada:BR870114987SP"),
    # Dispute 2 storyline: carrier lost the package (refund-fast case)
    _sale(9, "2026-07-02", 156.90, "credito_avista", "mastercard", "ecommerce",
          "JULIANA F. COSTA", "Mochila esportiva 30L",
          status="em_disputa", entrega="extraviada:BR870332415SP"),
    _sale(10, "2026-07-02", 745.50, "credito_parcelado", "visa", "pos",
          "MARCELO A. DUARTE", "Conjunto de halteres 40kg",
          parcelas=6, terminal_id="TERM_002"),
    _sale(11, "2026-07-02", 289.90, "debito", "elo", "pos",
          "FERNANDA L. PRADO", "Tênis casual feminino",
          terminal_id="TERM_003"),
    _sale(12, "2026-07-03", 1189.00, "credito_parcelado", "mastercard", "ecommerce",
          "ANDRE V. CASTRO", "Bicicleta aro 29 com 21 marchas",
          parcelas=10, entrega="confirmada:BR870551208SP"),
    _sale(13, "2026-07-03", 269.90, "credito_avista", "elo", "pos",
          "PATRICIA M. SILVA", "Legging + top fitness",
          terminal_id="TERM_001"),
    _sale(14, "2026-07-03", 412.30, "pix", "pix", "ecommerce",
          "GUSTAVO H. LEMOS", "Kit suplementos e coqueteleira",
          entrega="confirmada:BR870552764SP"),
    _sale(15, "2026-07-04", 359.80, "credito_avista", "visa", "ecommerce",
          "LARISSA O. PINTO", "Par de luvas de goleiro",
          entrega="confirmada:BR870761190SP"),
    _sale(16, "2026-07-04", 219.90, "debito", "visa", "pos",
          "RODRIGO S. TELES", "Bermuda e camiseta dry-fit",
          terminal_id="TERM_002"),
    _sale(17, "2026-07-04", 899.00, "credito_parcelado", "visa", "ecommerce",
          "EDUARDO N. RAMOS", "Barraca de camping 6 pessoas",
          parcelas=4, entrega="confirmada:BR870763321SP"),
    # Dispute 1 storyline: 3rd monthly purchase, delivered, then contested
    _sale(18, "2026-07-05", 890.00, "credito_avista", "visa", "ecommerce",
          "MARCOS VINICIUS P.", "Chuteira de campo profissional",
          status="em_disputa", entrega="confirmada:BR880412655SP"),
    _sale(19, "2026-07-05", 175.50, "debito", "mastercard", "pos",
          "BEATRIZ K. MOURA", "Corda de pular profissional + acessórios",
          terminal_id="TERM_001"),
    _sale(20, "2026-07-05", 528.40, "credito_avista", "mastercard", "pos",
          "VITOR L. ANDRADE", "Tênis de trilha impermeável",
          terminal_id="TERM_002"),
    _sale(21, "2026-07-06", 349.90, "pix", "pix", "ecommerce",
          "AMANDA J. REIS", "Patins inline ajustável",
          entrega="confirmada:BR871002456SP"),
    _sale(22, "2026-07-06", 1450.00, "credito_parcelado", "visa", "ecommerce",
          "CLAUDIO B. MOTTA", "Estação de musculação compacta",
          parcelas=12, entrega="confirmada:BR871003318SP"),
    _sale(23, "2026-07-06", 98.50, "debito", "elo", "pos",
          "SERGIO D. CAMPOS", "Squeeze térmico + munhequeira",
          terminal_id="TERM_003"),
    _sale(24, "2026-07-07", 465.00, "credito_avista", "elo", "ecommerce",
          "TATIANA R. FROTA", "Wetsuit 3mm feminino",
          entrega="confirmada:BR871220874SP"),
    _sale(25, "2026-07-07", 312.90, "credito_avista", "visa", "pos",
          "HENRIQUE P. SALES", "Chuteira society juvenil",
          terminal_id="TERM_001"),
    _sale(26, "2026-07-07", 239.80, "credito_parcelado", "mastercard", "pos",
          "MONICA T. BRAGA", "Tênis de caminhada",
          parcelas=2, terminal_id="TERM_002"),
    _sale(27, "2026-07-08", 689.70, "credito_parcelado", "mastercard", "ecommerce",
          "FELIPE G. ARRUDA", "Kit boxe: luvas, bandagem e saco",
          parcelas=3, entrega="confirmada:BR871448001SP"),
    _sale(28, "2026-07-08", 154.90, "debito", "visa", "pos",
          "CRISTINA U. NEVES", "Bola de vôlei oficial",
          terminal_id="TERM_001"),
    _sale(29, "2026-07-08", 379.90, "credito_avista", "visa", "ecommerce",
          "DANIEL M. QUEIROZ", "Jaqueta corta-vento de corrida",
          entrega="confirmada:BR871449553SP"),
    # Refunded duplicate charge at the POS (density/realism)
    _sale(30, "2026-07-09", 429.90, "credito_avista", "visa", "pos",
          "PEDRO IVO L. SANTANA", "Tênis de corrida amortecido (cobrança duplicada)",
          terminal_id="TERM_002", status="estornada"),
    _sale(31, "2026-07-09", 265.00, "pix", "pix", "ecommerce",
          "ISABELA C. FONTES", "Kit yoga: tapete + blocos",
          entrega="confirmada:BR871667231SP"),
    _sale(32, "2026-07-09", 549.90, "credito_parcelado", "elo", "ecommerce",
          "MAURICIO F. ABREU", "Patinete dobrável adulto",
          parcelas=5, entrega="confirmada:BR871668914SP"),
    _sale(33, "2026-07-10", 199.90, "debito", "mastercard", "pos",
          "SANDRA E. VILELA", "Camisa de time nacional",
          terminal_id="TERM_002"),
    _sale(34, "2026-07-10", 815.60, "credito_avista", "mastercard", "ecommerce",
          "RICARDO O. MACHADO", "Kit ciclismo: capacete + sapatilha",
          entrega="confirmada:BR871881120SP"),
    _sale(35, "2026-07-10", 385.00, "credito_avista", "visa", "pos",
          "ALINE B. SARAIVA", "Tênis de academia feminino",
          terminal_id="TERM_001"),
    _sale(36, "2026-07-11", 122.40, "debito", "elo", "pos",
          "JORGE W. PASSOS", "Meião + caneleira",
          terminal_id="TERM_003"),
    _sale(37, "2026-07-11", 640.00, "credito_parcelado", "visa", "ecommerce",
          "NATALIA H. CORREA", "Smartwatch esportivo com GPS",
          parcelas=2, entrega="confirmada:BR872093467SP"),
    _sale(38, "2026-07-11", 298.70, "pix", "pix", "ecommerce",
          "OTAVIO J. MELLO", "Kit natação: óculos, touca e nadadeiras",
          entrega="confirmada:BR872094105SP"),
    _sale(39, "2026-07-12", 519.90, "credito_avista", "mastercard", "ecommerce",
          "VANESSA D. AGUIAR", "Tênis de basquete",
          entrega="confirmada:BR872311782SP"),
    _sale(40, "2026-07-12", 233.50, "debito", "visa", "pos",
          "MARCIO S. VALENTE", "Bola de basquete + bomba de ar",
          terminal_id="TERM_001"),
    _sale(41, "2026-07-12", 999.00, "credito_parcelado", "mastercard", "pos",
          "GUILHERME T. PIRES", "Remo indoor magnético",
          parcelas=8, terminal_id="TERM_002"),
    _sale(42, "2026-07-13", 359.90, "credito_avista", "visa", "ecommerce",
          "PRISCILA N. XAVIER", "Tênis de corrida feminino",
          entrega="confirmada:BR872530649SP"),
    _sale(43, "2026-07-13", 149.90, "pix", "pix", "pos",
          "LEONARDO A. BASTOS", "Garrafa térmica + toalha esportiva",
          terminal_id="TERM_001"),
    _sale(44, "2026-07-13", 279.90, "credito_avista", "elo", "ecommerce",
          "SIMONE R. GALVAO", "Conjunto fitness feminino",
          entrega="confirmada:BR872531821SP"),
    _sale(45, "2026-07-13", 189.90, "debito", "mastercard", "pos",
          "WAGNER C. DUTRA", "Chuteira de futsal",
          terminal_id="TERM_002"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  RECEIVABLES — settlement agenda. Each row is a settlement batch anchored to
#  a representative sale (origem_transaction_id). Pending NET amounts sum to
#  EXACTLY R$ 287,450.00 in the next 30 days (data_prevista 2026-07-15 to
#  2026-08-13) and R$ 96,200.00 in 31-60 days (2026-08-14 to 2026-09-12).
# ═══════════════════════════════════════════════════════════════════════════

def _receivable(
    i: int,
    data_prevista: str,
    valor_liquido: float,
    modalidade: str,
    bandeira: str,
    origem_transaction_id: str,
    *,
    status: str = "pendente",
) -> dict:
    """Build a receivable; gross/MDR derive from net so sums stay exact."""
    rate = MDR_BY_MODALIDADE[modalidade] / 100
    valor_bruto = round(valor_liquido / (1 - rate), 2)
    mdr_valor = round(valor_bruto - valor_liquido, 2)
    return {
        "receivable_id": f"REC_{i:03d}",
        "merchant_id": DEMO_MERCHANT_ID,
        "data_prevista": data_prevista,
        "valor_bruto": valor_bruto,
        "mdr_valor": mdr_valor,
        "valor_liquido": round(valor_liquido, 2),
        "bandeira": bandeira,
        "modalidade": modalidade,
        "status": status,
        "origem_transaction_id": origem_transaction_id,
    }


RECEIVABLES = [
    # --- Already settled (debit/Pix D+1 from early July) ---
    _receivable(1, "2026-07-02", 1870.00, "pix", "pix", "TXN_008", status="liquidado"),
    _receivable(2, "2026-07-03", 2980.00, "debito", "elo", "TXN_011", status="liquidado"),

    # --- Pending, next 30 days (sums to R$ 287,450.00 net) ---
    _receivable(3, "2026-07-15", 3120.00, "debito", "mastercard", "TXN_045"),
    _receivable(4, "2026-07-15", 2140.00, "pix", "pix", "TXN_043"),
    _receivable(5, "2026-07-16", 21300.00, "credito_avista", "visa", "TXN_006"),
    _receivable(6, "2026-07-18", 19850.00, "credito_avista", "elo", "TXN_013"),
    _receivable(7, "2026-07-20", 19870.00, "credito_parcelado", "visa", "TXN_010"),
    _receivable(8, "2026-07-21", 22400.00, "credito_avista", "visa", "TXN_015"),
    _receivable(9, "2026-07-23", 18760.00, "credito_avista", "mastercard", "TXN_020"),
    _receivable(10, "2026-07-26", 20150.00, "credito_avista", "elo", "TXN_024"),
    _receivable(11, "2026-07-27", 20340.00, "credito_parcelado", "mastercard", "TXN_012"),
    _receivable(12, "2026-07-28", 19480.00, "credito_avista", "visa", "TXN_025"),
    _receivable(13, "2026-07-30", 21940.00, "credito_avista", "visa", "TXN_029"),
    _receivable(14, "2026-08-03", 18230.00, "credito_avista", "mastercard", "TXN_034"),
    _receivable(15, "2026-08-04", 18910.00, "credito_parcelado", "visa", "TXN_017"),
    _receivable(16, "2026-08-06", 20690.00, "credito_avista", "visa", "TXN_035"),
    _receivable(17, "2026-08-10", 19320.00, "credito_avista", "mastercard", "TXN_039"),
    _receivable(18, "2026-08-12", 20950.00, "credito_parcelado", "visa", "TXN_022"),

    # --- Pending, 31-60 days (sums to R$ 96,200.00 net) ---
    _receivable(19, "2026-08-16", 17850.00, "credito_parcelado", "mastercard", "TXN_002"),
    _receivable(20, "2026-08-21", 16200.00, "credito_parcelado", "mastercard", "TXN_026"),
    _receivable(21, "2026-08-27", 15400.00, "credito_parcelado", "mastercard", "TXN_027"),
    _receivable(22, "2026-09-01", 16900.00, "credito_parcelado", "elo", "TXN_032"),
    _receivable(23, "2026-09-05", 14750.00, "credito_parcelado", "visa", "TXN_037"),
    _receivable(24, "2026-09-10", 15100.00, "credito_parcelado", "mastercard", "TXN_041"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  TERMINALS (3) — 2 stores + 1 kiosk. The kiosk POS is "instavel" (4G chip
#  flapping), powering the support/terminal-swap path.
# ═══════════════════════════════════════════════════════════════════════════

TERMINALS = [
    {
        "terminal_id": "TERM_001", "merchant_id": DEMO_MERCHANT_ID,
        "serial": "BS2-SMT-104512", "modelo": "pos_smart",
        "loja": "Loja Itaim", "status": "ativo",
        "ultima_transacao_em": "2026-07-13T17:41:00+00:00",
    },
    {
        "terminal_id": "TERM_002", "merchant_id": DEMO_MERCHANT_ID,
        "serial": "BS2-SMT-104739", "modelo": "pos_smart",
        "loja": "Loja Morumbi", "status": "ativo",
        "ultima_transacao_em": "2026-07-13T19:12:00+00:00",
    },
    {
        "terminal_id": "TERM_003", "merchant_id": DEMO_MERCHANT_ID,
        "serial": "BS2-MNI-208804", "modelo": "pos_mini",
        "loja": "Quiosque Shopping Vila Lobos", "status": "instavel",
        "ultima_transacao_em": "2026-07-11T15:27:00+00:00",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  DISPUTES (2) — the winnable one (Marcos: recurrence + confirmed deliveries)
#  and the refund-fast one (Juliana: carrier lost the package).
# ═══════════════════════════════════════════════════════════════════════════

DISPUTES = [
    {
        "dispute_id": "DSP_001", "merchant_id": DEMO_MERCHANT_ID,
        "transaction_id": "TXN_018",
        "valor": 890.00,
        "motivo": "nao_reconhecida",
        "cliente_final": "MARCOS VINICIUS P.",
        "status": "aguardando_lojista",
        "prazo_resposta": "2026-07-21",
        "bandeira": "visa",
    },
    {
        "dispute_id": "DSP_002", "merchant_id": DEMO_MERCHANT_ID,
        "transaction_id": "TXN_009",
        "valor": 156.90,
        "motivo": "produto_nao_recebido",
        "cliente_final": "JULIANA F. COSTA",
        "status": "aguardando_lojista",
        "prazo_resposta": "2026-07-21",
        "bandeira": "mastercard",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS — kiosk 4G chip swap (open) + a closed paper-roll order
# ═══════════════════════════════════════════════════════════════════════════

SUPPORT_TICKETS = [
    {
        "ticket_id": "TKT_001", "merchant_id": DEMO_MERCHANT_ID,
        "categoria": "terminal", "status": "em_andamento",
        "data_abertura": "2026-07-10T14:05:00+00:00",
        "data_resolucao": None,
        "resumo": (
            "Quiosque Shopping Vila Lobos: POS mini (TERM_003) com chip 4G oscilando, "
            "transações caindo nos horários de pico do fim de semana. Solicitada troca do chip."
        ),
        "resolucao": None,
    },
    {
        "ticket_id": "TKT_002", "merchant_id": DEMO_MERCHANT_ID,
        "categoria": "suprimentos", "status": "resolvido",
        "data_abertura": "2026-06-03T10:20:00+00:00",
        "data_resolucao": "2026-06-04T16:00:00+00:00",
        "resumo": "Pedido de bobinas de papel para os POS das lojas Itaim e Morumbi.",
        "resolucao": "Enviadas 24 bobinas, entrega confirmada na Loja Itaim em 1 dia útil.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  PIX CONTACTS — frequent payees of the Cerioni Sports PJ account
# ═══════════════════════════════════════════════════════════════════════════

PIX_CONTACTS = [
    {
        "contact_id": "PIX_001", "merchant_id": DEMO_MERCHANT_ID,
        "recipient_name": "Almeida Esportes Distribuidora LTDA",
        "chave_pix": "43.***.***/0001-88",
        "chave_tipo": "cnpj",
        "banco_destino": "Itaú Unibanco",
        "tipo_relacao": "fornecedor",
        "valor_recorrente": 32000.00,
        "recorrencia": "mensal (todo dia 15)",
        "frequencia_uso": 28,
        "ultimo_uso": "2026-06-15T13:02:00+00:00",
    },
    {
        "contact_id": "PIX_002", "merchant_id": DEMO_MERCHANT_ID,
        "recipient_name": "Renata Lima",
        "chave_pix": "renata.lima@example.com.br",
        "chave_tipo": "email",
        "banco_destino": "BS2",
        "tipo_relacao": "pro_labore",
        "valor_recorrente": 18000.00,
        "recorrencia": "mensal (dia 5)",
        "frequencia_uso": 19,
        "ultimo_uso": "2026-07-05T09:14:00+00:00",
    },
    {
        "contact_id": "PIX_003", "merchant_id": DEMO_MERCHANT_ID,
        "recipient_name": "RapidLog Transportes",
        "chave_pix": "+55 11 97030-4412",
        "chave_tipo": "celular",
        "banco_destino": "Bradesco",
        "tipo_relacao": "frete",
        "valor_recorrente": 4100.00,
        "recorrencia": "semanal (sextas)",
        "frequencia_uso": 42,
        "ultimo_uso": "2026-07-10T11:33:00+00:00",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) — BS2 Pay / Adiq policies in PT-BR
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "MDR e taxas do plano Adiq Pro", "category": "taxas",
        "content": (
            "No plano Adiq Pro, o MDR aplicado sobre cada venda é: crédito à vista 2,39%, "
            "crédito parcelado 2,99%, débito 1,09% e Pix 0,99%. O MDR é descontado "
            "automaticamente do valor bruto e o valor líquido entra na agenda de recebíveis. "
            "A taxa de antecipação de recebíveis é de 1,49% ao mês, cobrada pro-rata pelos "
            "dias efetivamente antecipados. Não há taxa de adesão nem mensalidade no Adiq Pro; "
            "o aluguel de maquininha segue regra própria de isenção por volume."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Prazos de repasse por modalidade", "category": "repasse",
        "content": (
            "Débito e Pix são liquidados em D+1 (dia útil seguinte à venda). Crédito à vista "
            "é liquidado em D+30. Crédito parcelado é liquidado a cada 30 dias por parcela: "
            "a primeira parcela em D+30, a segunda em D+60 e assim por diante. O valor líquido "
            "(bruto menos MDR) cai direto na conta de liquidação cadastrada. Lojistas com conta "
            "PJ BS2 recebem o repasse sem TED e sem custo adicional."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Como funciona uma disputa de chargeback", "category": "chargeback",
        "content": (
            "Quando o portador do cartão contesta uma venda, a adquirente notifica o lojista e "
            "a transação fica com status em disputa. O lojista tem prazo de 15 dias corridos "
            "para enviar as evidências: comprovante de entrega com código de rastreio, histórico "
            "de compras do cliente, aceite dos termos de compra e troca de mensagens, se houver. "
            "Recorrência favorece o lojista: compras anteriores do mesmo comprador com entregas "
            "confirmadas são evidência forte de que a transação é legítima. Se o lojista não "
            "responder no prazo, o valor é debitado automaticamente da agenda. Em casos de "
            "produto não recebido, recomenda-se avaliar o reembolso direto ao comprador antes "
            "de disputar, preservando a taxa de chargeback do estabelecimento."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Antecipação de recebíveis", "category": "antecipacao",
        "content": (
            "O lojista pode antecipar a agenda de recebíveis de crédito (à vista e parcelado) "
            "a qualquer momento. A taxa é de 1,49% ao mês, calculada pro-rata pelos dias entre "
            "a antecipação e a data prevista de cada recebível. O valor cai na conta PJ BS2 em "
            "minutos após a confirmação. A antecipação pode ser spot (o lojista escolhe quanto "
            "e quando) ou automática (toda a agenda elegível é antecipada diariamente). "
            "Recebíveis vinculados a disputa de chargeback não são elegíveis para antecipação."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Troca e suporte de POS", "category": "terminal",
        "content": (
            "Terminais com defeito, instabilidade de conexão ou dano físico são trocados em até "
            "2 dias úteis nas capitais e regiões metropolitanas (até 5 dias úteis nas demais "
            "localidades). A troca não tem custo quando o problema é técnico. Problemas de chip "
            "4G podem ser resolvidos com envio de novo chip sem troca do terminal. O suporte é "
            "acionado pelo portal do lojista ou pela central BS2 Pay, com protocolo de "
            "acompanhamento."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Bandeiras e métodos de pagamento aceitos", "category": "credenciamento",
        "content": (
            "O credenciamento BS2 Pay (Adiq) aceita as bandeiras Visa, Mastercard e Elo nas "
            "modalidades crédito à vista, crédito parcelado (até 12 parcelas) e débito, além de "
            "Pix via QR Code no POS e no e-commerce. No e-commerce, a integração cobre checkout "
            "próprio via API, link de pagamento e as principais plataformas de loja virtual. "
            "Carteiras digitais e pagamento por aproximação (NFC) são aceitos nos terminais "
            "pos_smart e pos_mini."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Aluguel de maquininha", "category": "taxas",
        "content": (
            "No plano Adiq Pro, o aluguel da maquininha é isento para estabelecimentos com "
            "faturamento mensal acima de R$ 20.000,00 no cartão. Abaixo desse volume, é cobrado "
            "aluguel por terminal ativo no mês. Terminais adicionais para novas lojas ou "
            "quiosques seguem a mesma regra de isenção por volume, avaliada por CNPJ."
        ),
    },
    {
        "policy_id": "POL_008", "title": "Pix no e-commerce", "category": "pix",
        "content": (
            "O Pix no e-commerce tem taxa de 0,99% por transação e liquidação em D+1 na agenda. "
            "O QR Code é gerado no checkout com expiração configurável e a confirmação do "
            "pagamento é instantânea, liberando o pedido na hora. Pix não tem chargeback de "
            "bandeira; contestações seguem o Mecanismo Especial de Devolução (MED) do Banco "
            "Central, com prazos próprios de resposta."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Capital de giro BS2", "category": "credito",
        "content": (
            "Clientes BS2 Empresas credenciados na BS2 Pay contam com limite de capital de giro "
            "pré-aprovado, calculado a partir do histórico de vendas e da agenda de recebíveis. "
            "A garantia é a própria agenda: as parcelas do empréstimo são descontadas dos "
            "repasses futuros, sem boleto. A contratação é digital, o dinheiro cai na conta PJ "
            "em minutos e não há tarifa de contratação. As taxas variam conforme o prazo e o "
            "perfil do estabelecimento."
        ),
    },
    {
        "policy_id": "POL_010", "title": "Conta PJ BS2 para credenciados", "category": "conta",
        "content": (
            "Estabelecimentos credenciados na BS2 Pay têm conta PJ BS2 sem tarifa de manutenção. "
            "A conta recebe os repasses da agenda no mesmo dia da liquidação, concentra Pix, TED "
            "e pagamento de fornecedores, e dá acesso ao capital de giro pré-aprovado. O extrato "
            "unifica vendas, repasses e antecipações, facilitando a conciliação do lojista."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — generate embeddings + write JSONLs
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


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE (1) — Cerioni Sports online features, read in real time by ADA
#  for merchant recommendations. Calibrated for the flagship paths: a healthy
#  agenda (anticipation quote at 1.49% p.m. pro-rata), low chargeback rate
#  (0.4%, strengthens the dispute defense) and the planned Campinas branch on
#  top of the pre-approved working capital.
# ═══════════════════════════════════════════════════════════════════════════

FEATURE_STORE = [
    {
        "merchant_id": DEMO_MERCHANT_ID,
        "agenda_liquida_30d": 287450.00,
        "agenda_liquida_31_60d": 96200.00,
        "vendas_mes": 412800.00,
        "qtd_transacoes_mes": 1086,
        "ticket_medio": 380.00,
        "mdr_medio_pct": 2.21,
        "chargeback_rate_pct": 0.4,
        "crescimento_mm_pct": 8.0,
        "plano": "adiq_pro",
        "taxa_antecipacao_am": 1.49,
        "sazonalidade_pico": "black_friday",
        "saldo_pj": 84300.00,
        "capital_giro_pre_aprovado": 200000.00,
        "filial_planejada": "campinas",
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]


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
    write_jsonl(resolved_output_dir, "merchants.jsonl", MERCHANTS)
    write_jsonl(resolved_output_dir, "pj_accounts.jsonl", PJ_ACCOUNTS)
    write_jsonl(resolved_output_dir, "sales_transactions.jsonl", SALES_TRANSACTIONS)
    write_jsonl(resolved_output_dir, "receivables.jsonl", RECEIVABLES)
    write_jsonl(resolved_output_dir, "terminals.jsonl", TERMINALS)
    write_jsonl(resolved_output_dir, "disputes.jsonl", DISPUTES)
    write_jsonl(resolved_output_dir, "support_tickets.jsonl", SUPPORT_TICKETS)
    write_jsonl(resolved_output_dir, "pix_contacts.jsonl", PIX_CONTACTS)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = MERCHANTS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["merchant_id"])
        update_env("DEMO_USER_NAME", demo["socio_responsavel"])
        update_env("DEMO_USER_EMAIL", demo["contato_email"])
    print(f"\nLojista demo: {demo['nome_fantasia']} / {demo['socio_responsavel']} ({demo['merchant_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["merchant_id"],
            "DEMO_USER_NAME": demo["socio_responsavel"],
            "DEMO_USER_EMAIL": demo["contato_email"],
        },
        summary={
            "merchants": len(MERCHANTS),
            "pj_accounts": len(PJ_ACCOUNTS),
            "sales_transactions": len(SALES_TRANSACTIONS),
            "receivables": len(RECEIVABLES),
            "terminals": len(TERMINALS),
            "disputes": len(DISPUTES),
            "support_tickets": len(SUPPORT_TICKETS),
            "pix_contacts": len(PIX_CONTACTS),
            "feature_store": len(FEATURE_STORE),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
