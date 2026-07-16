"""PicPay Assist — seed sintético em PT-BR.

Persona: Gabriel Cerioni (@gabscerioni), usuário ativo, vida social de pagamentos.
Mora em república (racha aluguel/contas), tem a galera do churrasco (racha rolê),
acumula cashback (vai pro Cofrinho da Viagem Chile) e tem 1 contato golpista na
agenda (gancho anti-golpe do Pix).

As 3 tools determinísticas escrevem runtime via UnifiedClient.import_data:
  • simulate_split_bill        — racha a conta social (cria N transações P2P)
  • move_cashback_to_cofrinho  — joga cashback disponível no Cofrinho
  • flag_suspicious_pix         — sinaliza/bloqueia contato ou chave suspeita
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

OUTPUT_DIR = ROOT / "output" / "picpay_assist"

now = datetime.now(timezone.utc)


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


DEMO_USER_ID = "USER_DEMO_001"

# ═══════════════════════════════════════════════════════════════════════════
#  USER (Gabriel) — dono da carteira
# ═══════════════════════════════════════════════════════════════════════════
USERS = [
    {
        "user_id": DEMO_USER_ID,
        "nome": "Gabriel Cerioni",
        "handle": "@gabscerioni",
        "cpf_masked": "***.456.789-**",
        "email": "gabriel.cerioni@example.com.br",
        "cidade": "São Paulo",
        "saldo_carteira": 1250.75,
        "cashback_disponivel": 87.40,
        "membro_desde": "2018",
        "nivel": "ouro",
        "pix_key_principal": "***.456.789-** (CPF)",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  CONTACTS — grafo social (república + galera do churrasco + família + golpista)
# ═══════════════════════════════════════════════════════════════════════════
CONTACTS = [
    {"contact_id": "CONT_JOAO", "user_id": DEMO_USER_ID, "nome": "João Pedro", "handle": "@joaopedro",
     "relacao": "republica", "is_frequente": "sim", "trust_level": "confiavel",
     "vezes_transacionado": 48, "ultima_interacao": ts(now - timedelta(days=2))},
    {"contact_id": "CONT_MARINA", "user_id": DEMO_USER_ID, "nome": "Marina Alves", "handle": "@marinaalves",
     "relacao": "republica", "is_frequente": "sim", "trust_level": "confiavel",
     "vezes_transacionado": 44, "ultima_interacao": ts(now - timedelta(days=3))},
    {"contact_id": "CONT_BRUNO", "user_id": DEMO_USER_ID, "nome": "Bruno Tanaka", "handle": "@brunotanaka",
     "relacao": "amigo", "is_frequente": "sim", "trust_level": "confiavel",
     "vezes_transacionado": 31, "ultima_interacao": ts(now - timedelta(days=6))},
    {"contact_id": "CONT_LARI", "user_id": DEMO_USER_ID, "nome": "Larissa Gomes", "handle": "@larigomes",
     "relacao": "amigo", "is_frequente": "sim", "trust_level": "confiavel",
     "vezes_transacionado": 22, "ultima_interacao": ts(now - timedelta(days=9))},
    {"contact_id": "CONT_TEO", "user_id": DEMO_USER_ID, "nome": "Téo Martins", "handle": "@teomartins",
     "relacao": "amigo", "is_frequente": "nao", "trust_level": "confiavel",
     "vezes_transacionado": 12, "ultima_interacao": ts(now - timedelta(days=20))},
    {"contact_id": "CONT_MAE", "user_id": DEMO_USER_ID, "nome": "Dona Sônia", "handle": "@donasonia",
     "relacao": "familia", "is_frequente": "sim", "trust_level": "confiavel",
     "vezes_transacionado": 60, "ultima_interacao": ts(now - timedelta(days=1))},
    # O golpista — chave recém-criada, fora do grafo, nunca transacionou
    {"contact_id": "CONT_GOLPE", "user_id": DEMO_USER_ID, "nome": "Prêmios Caixa 2026", "handle": "@premios-caixa-2026",
     "relacao": "desconhecido", "is_frequente": "nao", "trust_level": "suspeito",
     "vezes_transacionado": 0, "ultima_interacao": ts(now - timedelta(hours=3))},
]

# galera do churrasco = quem entra no racha por padrão
CHURRASCO_CREW = ["CONT_JOAO", "CONT_MARINA", "CONT_BRUNO", "CONT_LARI", "CONT_TEO"]

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS — feed social
# ═══════════════════════════════════════════════════════════════════════════
def _txn(i, cp_id, cp_nome, tipo, valor, tag, emoji, days_ago, status="concluida"):
    return {
        "txn_id": f"TXN_{i:03d}", "user_id": DEMO_USER_ID,
        "counterparty_id": cp_id, "counterparty_nome": cp_nome,
        "tipo": tipo, "valor": valor, "tag": tag, "emoji": emoji,
        "status": status, "data": ts(now - timedelta(days=days_ago)),
        "is_split": "nao", "split_group_id": None,
    }

TRANSACTIONS = [
    _txn(1, "CONT_JOAO", "João Pedro", "p2p_enviado", 400.00, "aluguel", "🏠", 5),
    _txn(2, "CONT_MARINA", "Marina Alves", "p2p_recebido", 142.00, "conta de luz", "💡", 4),
    _txn(3, "CONT_BRUNO", "Bruno Tanaka", "p2p_enviado", 35.00, "rolê", "🍻", 6),
    _txn(4, "CONT_MAE", "Dona Sônia", "p2p_recebido", 200.00, "presente", "🎁", 1),
    _txn(5, None, "iFood", "compra", 58.90, "jantar", "🍔", 2),
    _txn(6, None, "Uber", "compra", 24.50, "corrida", "🚗", 2),
    _txn(7, "CONT_LARI", "Larissa Gomes", "p2p_enviado", 50.00, "vaquinha aniversário", "🎂", 8),
    _txn(8, None, "Mercado Livre", "compra", 189.90, "fone novo", "🎧", 10),
    _txn(9, "CONT_JOAO", "João Pedro", "p2p_recebido", 80.00, "churrasco passado", "🔥", 14),
    _txn(10, None, "Posto Shell", "compra", 150.00, "gasolina", "⛽", 7),
    _txn(11, None, "PicPay", "cashback", 12.40, "cashback iFood", "💚", 2),
    _txn(12, None, "Cofrinho Viagem Chile", "cofrinho", 300.00, "depósito meta", "✈️", 15),
    # pedido suspeito do golpista (pendente) — gancho do anti-golpe
    {
        "txn_id": "TXN_GOLPE", "user_id": DEMO_USER_ID,
        "counterparty_id": "CONT_GOLPE", "counterparty_nome": "Prêmios Caixa 2026",
        "tipo": "p2p_recebido", "valor": 800.00, "tag": "resgate de prêmio", "emoji": "🎁",
        "status": "solicitada", "data": ts(now - timedelta(hours=3)),
        "is_split": "nao", "split_group_id": None,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  CASHBACK — disponível pra resgatar/jogar no Cofrinho
# ═══════════════════════════════════════════════════════════════════════════
CASHBACK_EVENTS = [
    {"cashback_id": "CB_001", "user_id": DEMO_USER_ID, "origem": "compra", "descricao": "Cashback iFood 5%",
     "valor": 12.40, "data": ts(now - timedelta(days=2)), "destino": "disponivel", "status": "creditado"},
    {"cashback_id": "CB_002", "user_id": DEMO_USER_ID, "origem": "compra", "descricao": "Cashback Mercado Livre 3%",
     "valor": 5.70, "data": ts(now - timedelta(days=10)), "destino": "disponivel", "status": "creditado"},
    {"cashback_id": "CB_003", "user_id": DEMO_USER_ID, "origem": "promo", "descricao": "Promo Black Friday PicPay",
     "valor": 50.00, "data": ts(now - timedelta(days=20)), "destino": "disponivel", "status": "creditado"},
    {"cashback_id": "CB_004", "user_id": DEMO_USER_ID, "origem": "indicacao", "descricao": "Indicação do Bruno",
     "valor": 10.00, "data": ts(now - timedelta(days=30)), "destino": "disponivel", "status": "creditado"},
    {"cashback_id": "CB_005", "user_id": DEMO_USER_ID, "origem": "parceiro", "descricao": "Cashback Posto Shell 2%",
     "valor": 9.30, "data": ts(now - timedelta(days=7)), "destino": "disponivel", "status": "creditado"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  COFRINHOS — metas de poupança
# ═══════════════════════════════════════════════════════════════════════════
COFRINHOS = [
    {"cofrinho_id": "COF_CHILE", "user_id": DEMO_USER_ID, "nome": "Viagem Chile", "emoji": "✈️",
     "meta_valor": 8000.00, "saldo_atual": 3200.00, "rende_cdi_pct": 100,
     "data_meta": ts(now + timedelta(days=210)), "status": "ativo"},
    {"cofrinho_id": "COF_RESERVA", "user_id": DEMO_USER_ID, "nome": "Reserva de Emergência", "emoji": "🛡️",
     "meta_valor": 5000.00, "saldo_atual": 4100.00, "rende_cdi_pct": 100,
     "data_meta": ts(now + timedelta(days=120)), "status": "ativo"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  CARDS
# ═══════════════════════════════════════════════════════════════════════════
CARDS = [
    {"card_id": "CARD_CRED", "user_id": DEMO_USER_ID, "tipo": "credito", "final": "4423",
     "limite": 6000.00, "fatura_atual": 1840.30, "vencimento": ts(now + timedelta(days=12)), "status": "ativo"},
    {"card_id": "CARD_DEB", "user_id": DEMO_USER_ID, "tipo": "debito", "final": "1102",
     "limite": 0.00, "fatura_atual": 0.00, "vencimento": ts(now + timedelta(days=30)), "status": "ativo"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  BOLETOS
# ═══════════════════════════════════════════════════════════════════════════
BOLETOS = [
    {"boleto_id": "BOL_LUZ", "user_id": DEMO_USER_ID, "descricao": "Conta de luz Enel", "beneficiario": "Enel SP",
     "valor": 142.00, "vencimento": ts(now + timedelta(days=5)), "status": "a_pagar"},
    {"boleto_id": "BOL_NET", "user_id": DEMO_USER_ID, "descricao": "Internet Vivo Fibra", "beneficiario": "Vivo",
     "valor": 119.90, "vencimento": ts(now + timedelta(days=9)), "status": "a_pagar"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  SUSPICIOUS FLAGS — começa vazio; o anti-golpe cria runtime.
#  (1 histórico resolvido pra dar densidade ao "já me protegeram antes")
# ═══════════════════════════════════════════════════════════════════════════
SUSPICIOUS_FLAGS = [
    {"flag_id": "FLAG_HIST_001", "user_id": DEMO_USER_ID, "target_type": "chave_pix", "target_id": None,
     "target_label": "@sorteio-pix-oficial", "motivo": "Chave de sorteio falso reportada por outros usuários",
     "padrao_detectado": "premio_falso", "severidade": "alta",
     "data": ts(now - timedelta(days=45)), "status": "bloqueado"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE — features comportamentais online do Gabriel (o diferencial)
#  O modelo de fraude lê esta row em sub-ms e funde com os dados vivos do contato.
#  Calibrado: ticket médio P2P baixo + máximo histórico R$400 => pedido de R$800
#  do golpista (contato novo, fora do grafo) acende como risco crítico.
# ═══════════════════════════════════════════════════════════════════════════
FEATURE_STORE = [
    {
        "user_id": DEMO_USER_ID,
        "velocity_pix_24h": 4,
        "valor_medio_p2p": 151.20,
        "valor_max_historico": 400.00,
        "num_contatos_confiaveis": 6,
        "prior_golpe_count": 1,        # caiu num golpe de sorteio falso em 2024 (casa com a LTM)
        "device_trust_score": 0.93,
        "horario_tipico_inicio": 8,
        "horario_tipico_fim": 22,
        "perfil_risco": "baixo",
        "ultima_atualizacao": ts(now - timedelta(minutes=5)),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (8) — ajuda/segurança PicPay, embedding em runtime
# ═══════════════════════════════════════════════════════════════════════════
POLICIES_TEXT = [
    {"policy_id": "POL_PIX_LIMITES", "title": "Limites de Pix e P2P por horário (dia e noite)", "category": "limites",
     "content": "Limites do Pix por horário no PicPay. Durante o dia, das 6h às 20h, o limite diurno é de "
                "R$ 5.000 por transação. À noite e de madrugada, das 20h às 6h, o limite noturno cai para "
                "R$ 1.000 por transação, por segurança. Esses limites de Pix valem por transação e podem ser "
                "ajustados no app a qualquer momento. Pix e transferências entre amigos não têm taxa."},
    {"policy_id": "POL_RACHA", "title": "Como funciona o Racha a Conta", "category": "pagamentos",
     "content": "O Racha a Conta divide um valor entre os contatos selecionados e envia um pedido de "
                "pagamento P2P pra cada um, com tag e emoji opcionais. O criador do racha vê quem já pagou. "
                "Você pode rachar igualmente ou por valores customizados."},
    {"policy_id": "POL_CASHBACK", "title": "Cashback PicPay", "category": "cashback",
     "content": "O cashback é creditado como saldo disponível e pode ser usado em pagamentos, transferido "
                "pra carteira ou jogado num Cofrinho pra render. Cashback de promoção pode ter prazo de "
                "validade; cashback de compra normalmente não expira."},
    {"policy_id": "POL_COFRINHO", "title": "Cofrinho: metas que rendem", "category": "cofrinho",
     "content": "O Cofrinho guarda dinheiro separado da carteira pra uma meta (viagem, reserva). Rende um "
                "percentual do CDI com liquidez diária. Você define o valor-alvo e a data; dá pra depositar "
                "manualmente, agendar ou jogar o cashback direto no Cofrinho."},
    {"policy_id": "POL_GOLPE", "title": "Segurança: golpe do Pix", "category": "seguranca",
     "content": "Desconfie de chaves Pix recém-criadas, pedidos urgentes, prêmios e cobranças de contatos "
                "fora do seu histórico. O PicPay sinaliza transações com padrão atípico. Nunca pague por "
                "pressão. Em caso de suspeita, bloqueie o contato e registre a denúncia, a equipe analisa."},
    {"policy_id": "POL_SEG_CONTATO", "title": "Bloquear e denunciar contatos", "category": "seguranca",
     "content": "Você pode bloquear qualquer contato ou chave Pix suspeita. Ao bloquear, novos pedidos "
                "daquele contato são barrados e a sinalização entra em análise antifraude. Contatos confiáveis "
                "do seu histórico (família, república, amigos frequentes) não são bloqueados por engano."},
    {"policy_id": "POL_CARTAO", "title": "Cartão PicPay", "category": "cartao",
     "content": "O cartão de crédito PicPay tem fatura mensal e limite ajustável. O cartão de débito puxa do "
                "saldo da carteira. Você acompanha a fatura, antecipa parcelas e bloqueia o cartão pelo app."},
    {"policy_id": "POL_LGPD", "title": "Privacidade e LGPD", "category": "lgpd",
     "content": "Seus dados de pagamento e grafo social são protegidos pela LGPD. O PicPay não compartilha "
                "histórico de transações com terceiros sem consentimento. Você pode exportar ou excluir seus "
                "dados pelo app."},
]


def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {filename}: {len(rows)} registros")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    safe_value = value
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
    write_jsonl(resolved_output_dir, "users.jsonl", USERS)
    write_jsonl(resolved_output_dir, "contacts.jsonl", CONTACTS)
    write_jsonl(resolved_output_dir, "transactions.jsonl", TRANSACTIONS)
    write_jsonl(resolved_output_dir, "cashback_events.jsonl", CASHBACK_EVENTS)
    write_jsonl(resolved_output_dir, "cofrinhos.jsonl", COFRINHOS)
    write_jsonl(resolved_output_dir, "cards.jsonl", CARDS)
    write_jsonl(resolved_output_dir, "boletos.jsonl", BOLETOS)
    write_jsonl(resolved_output_dir, "suspicious_flags.jsonl", SUSPICIOUS_FLAGS)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = USERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["user_id"])
        update_env("DEMO_USER_NAME", demo["nome"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nUsuário demo: {demo['nome']} ({demo['user_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["user_id"],
            "DEMO_USER_NAME": demo["nome"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "users": len(USERS),
            "contacts": len(CONTACTS),
            "transactions": len(TRANSACTIONS),
            "cashback_events": len(CASHBACK_EVENTS),
            "cofrinhos": len(COFRINHOS),
            "cards": len(CARDS),
            "boletos": len(BOLETOS),
            "suspicious_flags": len(SUSPICIOUS_FLAGS),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
