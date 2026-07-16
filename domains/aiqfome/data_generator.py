"""aiqfome (AIQ): synthetic food delivery seed in PT-BR.

Built for an executive demo: the flagship use case is the instant refund on a
missing item. Order AIQ-8807 (yesterday, Burger do Ze) was delivered without
the large fries; Gabriel's online features (214 orders, 0.9% refund rate,
fraud score 0.03) let AIQ approve the refund on the spot per policy. A live
order AIQ-8842 (Temaki do Tio combo) is out for delivery with courier Jonas
right now. Secondary paths: allergy-aware menu search (shrimp dishes carry the
"camarao" allergen tag), the Friday pizza habit at Forno da Vila, and the
active R$ 15.00 loyalty voucher.

The Dish catalog (72 dishes across 12 Maringa merchants) is also the seed for
a future retail search demo, so descriptions are rich PT-BR with soft synonyms
in context and every dish carries a content embedding.

Demo customer is Gabriel Cerioni, a "fominha" since 2019-04 in Maringa-PR and
a clube aiqfome subscriber. All values are fictitious but plausible. Internal
Redis demo, no official affiliation with aiqfome or Magalu.
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

OUTPUT_DIR = ROOT / "output" / "aiqfome"

# Fixed demo anchor: the storyline is pinned to July 2026 (canonical facts such
# as order AIQ-8842 out for delivery "now" and the AIQ-8807 missing-fries case
# from yesterday are part of the demo script), so the generator uses a fixed
# "today" instead of datetime.now() and stays fully deterministic across runs.
now = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


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


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMERS (3) - demo fominha + 2 fillers for realism
# ═══════════════════════════════════════════════════════════════════════════

DEMO_USER_ID = "CUST_DEMO_001"

CUSTOMERS = [
    {
        "customer_id": DEMO_USER_ID,
        "nome": "Gabriel Cerioni",
        "email": "gabriel.cerioni@example.com.br",
        "cidade": "Maringá",
        "bairro": "Zona 01",
        "fominha_desde": "2019-04",
        "clube_aiqfome": "sim",
        "endereco_entrega": "Rua Néo Alves Martins, 2810 - Zona 01",
        "telefone": "+55 44 9****-4321",
    },
    {
        "customer_id": "CUST_002",
        "nome": "Larissa Kobayashi",
        "email": "larissa.kobayashi@example.com.br",
        "cidade": "Maringá",
        "bairro": "Zona 05",
        "fominha_desde": "2021-09",
        "clube_aiqfome": "nao",
        "endereco_entrega": "Av. Mandacaru, 1550, apto 302 - Zona 05",
        "telefone": "+55 44 9****-8812",
    },
    {
        "customer_id": "CUST_003",
        "nome": "Rafael Antunes",
        "email": "rafael.antunes@example.com.br",
        "cidade": "Maringá",
        "bairro": "Jardim Alvorada",
        "fominha_desde": "2023-02",
        "clube_aiqfome": "sim",
        "endereco_entrega": "Av. Morangueira, 980 - Jardim Alvorada",
        "telefone": "+55 44 9****-3307",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MERCHANTS (12) - Maringá-PR, real-ish coordinates per bairro. Clube
#  partners have delivery_fee 0. `geo` is "lon,lat", ready for a GEO index.
# ═══════════════════════════════════════════════════════════════════════════

def _merchant(
    merchant_id: str,
    nome: str,
    cozinha: str,
    rating: float,
    delivery_fee: float,
    eta_min: int,
    bairro: str,
    lat: float,
    lon: float,
    descricao: str,
    *,
    aberto: str = "sim",
    clube_parceiro: str = "nao",
) -> dict:
    """Build a merchant row; `geo` always derives from lon/lat."""
    return {
        "merchant_id": merchant_id,
        "nome": nome,
        "cozinha": cozinha,
        "rating": rating,
        "delivery_fee": delivery_fee,
        "eta_min": eta_min,
        "cidade": "Maringá",
        "bairro": bairro,
        "aberto": aberto,
        "clube_parceiro": clube_parceiro,
        "lat": lat,
        "lon": lon,
        "geo": f"{lon},{lat}",
        "descricao": descricao,
    }


MERCHANTS = [
    _merchant("MERCH_001", "Temaki do Tio", "japonesa", 4.8, 0.00, 35, "Zona 01",
              -23.4211, -51.9339,
              "Temakeria descontraída no centro, famosa pelo temaki de salmão enrolado na hora.",
              clube_parceiro="sim"),
    _merchant("MERCH_002", "Sushi Kenzo", "japonesa", 4.9, 8.90, 50, "Novo Centro",
              -23.4229, -51.9390,
              "Sushi bar premium com peixes frescos do dia e combinados montados pelo chef."),
    _merchant("MERCH_003", "Pizzaria Forno da Vila", "pizza", 4.7, 0.00, 45, "Zona 05",
              -23.4315, -51.9408,
              "Pizzas de forno a lenha com massa de fermentação lenta, tradição das sextas em Maringá.",
              clube_parceiro="sim"),
    _merchant("MERCH_004", "Burger do Zé", "lanches", 4.6, 0.00, 40, "Zona 07",
              -23.4386, -51.9247,
              "Hamburgueria artesanal com blends de 180g e a batata mais crocante da cidade.",
              clube_parceiro="sim"),
    _merchant("MERCH_005", "Açaí do Ponto", "acai_sobremesas", 4.8, 5.90, 30, "Zona 01",
              -23.4198, -51.9322,
              "Açaí batido na hora com adicionais à vontade, do copinho à barca de 1 litro."),
    _merchant("MERCH_006", "Marmitaria da Vó Cida", "caseira", 4.9, 0.00, 35, "Vila Operária",
              -23.4345, -51.9158,
              "Comida caseira de verdade: marmita da vó todo dia e feijoada completa aos sábados.",
              clube_parceiro="sim"),
    _merchant("MERCH_007", "Pastel & Cia Central", "pastelaria", 4.5, 6.90, 30, "Zona 01",
              -23.4219, -51.9350,
              "Pastéis de feira gigantes com massa que estala e caldo de cana moído na hora."),
    _merchant("MERCH_008", "Cantina Nonna Lucia", "massas", 4.7, 9.90, 55, "Zona 02",
              -23.4128, -51.9291,
              "Cantina italiana de família com massas frescas feitas em casa e molhos de panela."),
    _merchant("MERCH_009", "Churras Prime", "churrasco", 4.6, 10.90, 50, "Zona 04",
              -23.4152, -51.9447,
              "Espetos no carvão, costela no bafo e combos de churrasco pra família toda."),
    _merchant("MERCH_010", "Veggie Vida", "vegetariana", 4.8, 7.90, 40, "Zona 02",
              -23.4117, -51.9305,
              "Cozinha vegetariana e vegana com bowls, wraps e doces sem ingredientes de origem animal."),
    _merchant("MERCH_011", "Taco Loko", "mexicana", 4.4, 7.90, 45, "Zona 03",
              -23.4262, -51.9186,
              "Mexicano de verdade: tacos, burritos e nachos com molhos da casa e pimenta na medida.",
              aberto="nao"),
    _merchant("MERCH_012", "Padoca do Bairro", "padaria_cafe", 4.7, 0.00, 25, "Zona 01",
              -23.4189, -51.9315,
              "Padaria de bairro com pão quentinho, pingado na chapa e o famoso bolo de cenoura.",
              clube_parceiro="sim"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  DISHES (72) - 6 per merchant. Strategic asset for the future retail search
#  demo: rich PT-BR descriptions with soft synonyms in context, popularity for
#  reranking, allergen tags (the shrimp storyline) and a content embedding
#  (nome + descrição) generated at seed time.
# ═══════════════════════════════════════════════════════════════════════════

def _dish(
    dish_id: str,
    merchant_id: str,
    nome: str,
    categoria: str,
    preco: float,
    rating: float,
    popularity: int,
    descricao: str,
    *,
    tags: list[str] | None = None,
    alergenos: list[str] | None = None,
    serve_pessoas: int = 1,
) -> dict:
    """Build a dish row; the content embedding is attached at generation time."""
    return {
        "dish_id": dish_id,
        "merchant_id": merchant_id,
        "nome": nome,
        "descricao": descricao,
        "categoria": categoria,
        "preco": preco,
        "rating": rating,
        "popularity": popularity,
        "tags": tags or [],
        "alergenos": alergenos or [],
        "serve_pessoas": serve_pessoas,
    }


DISHES = [
    # --- Temaki do Tio (MERCH_001, japonesa) ---
    _dish("DISH_001", "MERCH_001", "Temaki de Salmão com Cream Cheese", "temaki", 32.90, 4.9, 98,
          "Cone de alga crocante recheado com arroz japonês, salmão fresco em cubos e cream cheese "
          "cremoso. O temaki queridinho da casa, enrolado na hora.",
          tags=["mais_pedido"], alergenos=["lactose"]),
    _dish("DISH_002", "MERCH_001", "Temaki Ebi Empanado", "temaki", 34.90, 4.7, 74,
          "Temaki de camarão (ebi) empanado e crocante com maionese especial levemente apimentada. "
          "Pra quem gosta de fruto do mar no cone.",
          tags=["picante"], alergenos=["camarao", "gluten", "ovo"]),
    _dish("DISH_003", "MERCH_001", "Hot Roll da Casa (8 unidades)", "sushi", 26.90, 4.8, 90,
          "Enrolado de salmão com cream cheese, empanado e frito, 8 peças quentinhas. O clássico "
          "hot roll (hossomaki empanado) que todo mundo pede.",
          tags=["mais_pedido"], alergenos=["gluten", "lactose"]),
    _dish("DISH_004", "MERCH_001", "Combo Xodó: 2 Temakis de Salmão + Hot Roll", "combo", 84.90, 4.9, 95,
          "Dois temakis de salmão com cream cheese e um hot roll de 8 peças. Comprando o combo "
          "você economiza R$ 7,80 em relação aos itens avulsos.",
          tags=["promo", "mais_pedido"], alergenos=["gluten", "lactose"], serve_pessoas=2),
    _dish("DISH_005", "MERCH_001", "Guioza de Porco (6 unidades)", "entrada", 24.90, 4.6, 62,
          "Guioza (gyoza) de porco, 6 unidades douradas na chapa, servidas com molho oriental da casa.",
          alergenos=["gluten"]),
    _dish("DISH_006", "MERCH_001", "Guaraná Lata 350ml", "bebida", 7.90, 4.5, 55,
          "Refrigerante de guaraná lata 350ml, o refri gelado pra acompanhar o japa."),

    # --- Sushi Kenzo (MERCH_002, japonesa) ---
    _dish("DISH_007", "MERCH_002", "Combinado Kenzo (30 peças)", "sushi", 89.90, 4.9, 88,
          "Seleção do chef com 30 peças: sashimis, uramakis, niguiris e joys variados de salmão e atum.",
          tags=["mais_pedido"], serve_pessoas=2),
    _dish("DISH_008", "MERCH_002", "Hot Roll de Camarão (8 unidades)", "sushi", 31.90, 4.8, 80,
          "Enrolado empanado e frito recheado de camarão com cream cheese, 8 peças quentes e crocantes.",
          alergenos=["camarao", "gluten", "lactose"]),
    _dish("DISH_009", "MERCH_002", "Sashimi de Salmão (12 fatias)", "sushi", 49.90, 4.9, 76,
          "Doze fatias generosas de salmão fresco cortadas na hora. Leve, sem arroz e sem glúten.",
          tags=["sem_gluten"]),
    _dish("DISH_010", "MERCH_002", "Uramaki Filadélfia (8 peças)", "sushi", 28.90, 4.7, 72,
          "Uramaki de salmão com cream cheese e gergelim, o famoso filadélfia em 8 peças.",
          alergenos=["lactose"]),
    _dish("DISH_011", "MERCH_002", "Niguiri de Atum (4 unidades)", "sushi", 22.90, 4.6, 48,
          "Bolinho de arroz temperado coberto com fatia de atum fresco, 4 unidades.",
          tags=["sem_gluten"]),
    _dish("DISH_012", "MERCH_002", "Chá Gelado de Lichia 300ml", "bebida", 9.90, 4.5, 40,
          "Chá gelado artesanal de lichia, docinho e refrescante, feito na casa."),

    # --- Pizzaria Forno da Vila (MERCH_003, pizza) ---
    _dish("DISH_013", "MERCH_003", "Pizza Margherita (8 fatias)", "pizza", 49.90, 4.8, 85,
          "Molho de tomate italiano, mussarela de primeira e manjericão fresco no forno a lenha. "
          "A margherita clássica napolitana.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"], serve_pessoas=2),
    _dish("DISH_014", "MERCH_003", "Pizza Calabresa (8 fatias)", "pizza", 52.90, 4.7, 92,
          "Calabresa fatiada com cebola roxa e orégano sobre mussarela derretida. A pizza mais "
          "pedida das sextas-feiras.",
          tags=["mais_pedido"], alergenos=["gluten", "lactose"], serve_pessoas=2),
    _dish("DISH_015", "MERCH_003", "Pizza Portuguesa (8 fatias)", "pizza", 56.90, 4.6, 70,
          "Presunto, ovo cozido, cebola, ervilha, azeitona e mussarela. A portuguesa caprichada da casa.",
          alergenos=["gluten", "lactose", "ovo"], serve_pessoas=2),
    _dish("DISH_016", "MERCH_003", "Pizza Quatro Queijos (8 fatias)", "pizza", 58.90, 4.8, 78,
          "Mussarela, provolone, parmesão e gorgonzola gratinados no forno a lenha. Pra quem ama "
          "queijo de verdade.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"], serve_pessoas=2),
    _dish("DISH_017", "MERCH_003", "Pizza Doce de Chocolate com Morango", "doce", 46.90, 4.7, 58,
          "Chocolate ao leite derretido com morangos frescos, a sobremesa em formato de pizza.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"], serve_pessoas=2),
    _dish("DISH_018", "MERCH_003", "Guaraná 2 Litros", "bebida", 14.90, 4.4, 65,
          "Refrigerante de guaraná 2 litros gelado, o par perfeito da pizza em família.",
          serve_pessoas=4),

    # --- Burger do Zé (MERCH_004, lanches) ---
    _dish("DISH_019", "MERCH_004", "Combo Cheddar Bacon", "burger", 32.90, 4.8, 96,
          "Sanduíche artesanal (nosso lanche mais pedido): burger de 180g no pão brioche com "
          "cheddar duplo, bacon crocante e maionese da casa.",
          tags=["mais_pedido"], alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_020", "MERCH_004", "Batata Frita Grande", "porcao", 12.90, 4.6, 89,
          "Porção grande de batata frita sequinha e crocante com sal e páprica. Acompanha bem "
          "qualquer lanche e dá pra dividir.",
          serve_pessoas=2),
    _dish("DISH_021", "MERCH_004", "X-Salada Clássico", "burger", 24.90, 4.5, 70,
          "Burger de 150g com queijo prato, alface americana, tomate e maionese caseira no pão macio.",
          alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_022", "MERCH_004", "Burger Vegano de Grão de Bico", "burger", 28.90, 4.6, 52,
          "Hambúrguer 100% vegetal de grão de bico com crosta dourada, pão vegano, tomate e molho "
          "especial de ervas.",
          tags=["vegano", "vegetariano"], alergenos=["gluten"]),
    _dish("DISH_023", "MERCH_004", "Onion Rings (10 unidades)", "porcao", 14.90, 4.4, 47,
          "Anéis de cebola empanados e fritos, crocantes por fora e macios por dentro.",
          tags=["vegetariano"], alergenos=["gluten"]),
    _dish("DISH_024", "MERCH_004", "Guaraná Lata 350ml", "bebida", 9.00, 4.5, 66,
          "Refrigerante lata 350ml, o refri gelado pra acompanhar o lanche."),

    # --- Açaí do Ponto (MERCH_005, acai_sobremesas) ---
    _dish("DISH_025", "MERCH_005", "Açaí 500ml com Adicionais", "acai", 24.90, 4.9, 94,
          "Açaí cremoso batido na hora com granola, banana e leite condensado. Os adicionais já "
          "estão inclusos, é só montar do seu jeito.",
          tags=["mais_pedido", "vegetariano"], alergenos=["lactose"]),
    _dish("DISH_026", "MERCH_005", "Açaí 300ml Tradicional", "acai", 16.90, 4.8, 75,
          "Açaí puro batido na hora no copo de 300ml, com granola e banana. Sem leite condensado, "
          "sabor raiz.",
          tags=["vegetariano"]),
    _dish("DISH_027", "MERCH_005", "Barca de Açaí 1 Litro", "acai", 39.90, 4.8, 68,
          "Barca de 1 litro pra dividir: açaí, morango, banana, granola, leite em pó e calda de "
          "chocolate.",
          tags=["promo", "vegetariano"], alergenos=["lactose"], serve_pessoas=2),
    _dish("DISH_028", "MERCH_005", "Açaí Fit com Pasta de Amendoim", "acai", 22.90, 4.7, 61,
          "Açaí sem adição de açúcar com pasta de amendoim integral, banana e granola sem glúten.",
          tags=["vegano", "vegetariano", "sem_gluten"], alergenos=["amendoim"]),
    _dish("DISH_029", "MERCH_005", "Milk-shake de Morango 400ml", "bebida", 18.90, 4.6, 57,
          "Milk-shake cremoso de morango com sorvete artesanal e chantilly.",
          tags=["vegetariano"], alergenos=["lactose"]),
    _dish("DISH_030", "MERCH_005", "Suco de Laranja 500ml", "bebida", 12.90, 4.5, 44,
          "Suco de laranja espremido na hora, natural e sem açúcar.",
          tags=["vegano", "sem_gluten"]),

    # --- Marmitaria da Vó Cida (MERCH_006, caseira) ---
    _dish("DISH_031", "MERCH_006", "Marmita da Vó Tamanho M", "marmita", 22.90, 4.9, 97,
          "Comida caseira de verdade: arroz soltinho, feijão temperado, bife acebolado, farofa e "
          "salada do dia. A marmita (quentinha) mais querida de Maringá.",
          tags=["mais_pedido"]),
    _dish("DISH_032", "MERCH_006", "Feijoada Completa de Sábado", "marmita", 34.90, 4.9, 82,
          "Feijoada completa servida aos sábados: feijão preto com carnes selecionadas, arroz, "
          "couve refogada, torresmo, farofa e laranja.",
          serve_pessoas=2),
    _dish("DISH_033", "MERCH_006", "Marmita Fit de Frango Grelhado", "marmita", 24.90, 4.7, 66,
          "Peito de frango grelhado com arroz integral, brócolis no vapor e legumes salteados. "
          "Leve e sem glúten.",
          tags=["sem_gluten"]),
    _dish("DISH_034", "MERCH_006", "Escondidinho de Carne Seca", "marmita", 26.90, 4.8, 63,
          "Purê de mandioca cremoso gratinado com queijo, coberto de carne seca desfiada na "
          "manteiga de garrafa.",
          alergenos=["lactose"]),
    _dish("DISH_035", "MERCH_006", "Strogonoff de Frango", "marmita", 25.90, 4.7, 71,
          "Strogonoff de frango cremoso com arroz branco e batata palha crocante, receita da vó.",
          alergenos=["lactose"]),
    _dish("DISH_036", "MERCH_006", "Suco de Laranja Natural 500ml", "bebida", 9.90, 4.6, 45,
          "Suco de laranja natural espremido na hora pra acompanhar a marmita.",
          tags=["vegano"]),

    # --- Pastel & Cia Central (MERCH_007, pastelaria) ---
    _dish("DISH_037", "MERCH_007", "Pastel de Carne", "pastel", 12.90, 4.6, 88,
          "Pastel de feira grandão recheado de carne moída temperada com azeitona. Massa fininha "
          "que estala na mordida.",
          tags=["mais_pedido"], alergenos=["gluten"]),
    _dish("DISH_038", "MERCH_007", "Pastel de Queijo", "pastel", 12.90, 4.5, 80,
          "Pastel crocante recheado com muito queijo mussarela derretido.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_039", "MERCH_007", "Pastel de Camarão", "pastel", 16.90, 4.7, 69,
          "Pastel recheado com camarão refogado no alho e catupiry cremoso.",
          alergenos=["camarao", "gluten", "lactose"]),
    _dish("DISH_040", "MERCH_007", "Pastel de Pizza", "pastel", 13.90, 4.4, 58,
          "Recheio de mussarela, tomate e orégano, o sabor de pizza dentro do pastel.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_041", "MERCH_007", "Pastel Doce de Banana com Canela", "doce", 13.90, 4.6, 50,
          "Pastel doce de banana com canela e açúcar, servido quentinho.",
          tags=["vegetariano"], alergenos=["gluten"]),
    _dish("DISH_042", "MERCH_007", "Caldo de Cana 500ml", "bebida", 8.90, 4.5, 62,
          "Caldo de cana (garapa) gelado, moído na hora, o par clássico do pastel.",
          tags=["vegano", "sem_gluten"]),

    # --- Cantina Nonna Lucia (MERCH_008, massas) ---
    _dish("DISH_043", "MERCH_008", "Espaguete à Bolonhesa", "massa", 38.90, 4.7, 84,
          "Macarrão tipo massa fresca ao molho bolonhesa encorpado de carne e tomate pelado, "
          "finalizado com parmesão.",
          tags=["mais_pedido"], alergenos=["gluten", "lactose"]),
    _dish("DISH_044", "MERCH_008", "Lasanha Quatro Queijos", "massa", 42.90, 4.8, 77,
          "Camadas de massa fresca com molho branco e a combinação de mussarela, provolone, "
          "parmesão e gorgonzola.",
          tags=["vegetariano"], alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_045", "MERCH_008", "Nhoque ao Sugo", "massa", 36.90, 4.6, 60,
          "Nhoque de batata artesanal (gnocchi) ao molho sugo de tomates frescos com manjericão.",
          tags=["vegetariano"], alergenos=["gluten", "ovo"]),
    _dish("DISH_046", "MERCH_008", "Risoto de Camarão", "risoto", 54.90, 4.8, 65,
          "Risoto cremoso de arroz arbóreo com camarões salteados na manteiga e raspas de limão "
          "siciliano.",
          alergenos=["camarao", "lactose"]),
    _dish("DISH_047", "MERCH_008", "Ravióli de Mussarela ao Pomodoro", "massa", 44.90, 4.7, 55,
          "Ravióli recheado de mussarela de búfala ao molho pomodoro com azeite extravirgem.",
          tags=["vegetariano"], alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_048", "MERCH_008", "Limonada Siciliana 500ml", "bebida", 11.90, 4.6, 42,
          "Limonada siciliana gelada com hortelã, feita na hora.",
          tags=["vegano"]),

    # --- Churras Prime (MERCH_009, churrasco) ---
    _dish("DISH_049", "MERCH_009", "Espeto de Picanha", "espeto", 18.90, 4.8, 91,
          "Espetinho de picanha no ponto, grelhado no carvão com sal grosso.",
          tags=["mais_pedido", "sem_gluten"]),
    _dish("DISH_050", "MERCH_009", "Espeto de Frango com Bacon", "espeto", 14.90, 4.6, 78,
          "Espetinho de frango envolto em bacon defumado, direto da churrasqueira.",
          tags=["sem_gluten"]),
    _dish("DISH_051", "MERCH_009", "Combo Churrasco Família", "churrasco", 79.90, 4.7, 73,
          "Cinco espetos variados com farofa, vinagrete e pão de alho. Churrasco completo pra "
          "família toda.",
          tags=["promo"], alergenos=["gluten", "lactose"], serve_pessoas=4),
    _dish("DISH_052", "MERCH_009", "Costela no Bafo 500g", "churrasco", 44.90, 4.8, 64,
          "Costela bovina assada lentamente no bafo por 8 horas, desmanchando de macia.",
          tags=["sem_gluten"], serve_pessoas=2),
    _dish("DISH_053", "MERCH_009", "Pão de Alho (4 unidades)", "porcao", 12.90, 4.5, 59,
          "Pão de alho cremoso tostado na churrasqueira, 4 unidades.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_054", "MERCH_009", "Guaraná 1,5 Litro", "bebida", 12.90, 4.4, 49,
          "Refrigerante de guaraná 1,5 litro bem gelado.",
          serve_pessoas=3),

    # --- Veggie Vida (MERCH_010, vegetariana) ---
    _dish("DISH_055", "MERCH_010", "Bowl Vegano de Falafel", "vegano", 29.90, 4.8, 79,
          "Bowl com falafel de grão de bico assado, homus, quinoa, folhas verdes e legumes "
          "tostados. Completo e 100% vegetal.",
          tags=["vegano", "vegetariano", "mais_pedido"]),
    _dish("DISH_056", "MERCH_010", "Burger Vegetariano de Cogumelos", "burger", 27.90, 4.7, 68,
          "Hambúrguer de cogumelos portobello e shimeji no pão australiano com maionese vegana "
          "de castanhas.",
          tags=["vegetariano"], alergenos=["gluten"]),
    _dish("DISH_057", "MERCH_010", "Salada Caesar Vegetariana", "salada", 24.90, 4.6, 54,
          "Alface romana, croutons crocantes, lascas de parmesão e molho caesar sem anchova.",
          tags=["vegetariano"], alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_058", "MERCH_010", "Wrap de Tofu Grelhado", "vegano", 23.90, 4.5, 51,
          "Wrap integral com tofu grelhado, pasta de abacate, cenoura e mix de folhas.",
          tags=["vegano", "vegetariano"], alergenos=["gluten"]),
    _dish("DISH_059", "MERCH_010", "Brownie Vegano com Amendoim", "doce", 12.90, 4.7, 56,
          "Brownie de cacau intenso sem leite e sem ovos, com pedaços de amendoim torrado.",
          tags=["vegano", "vegetariano"], alergenos=["amendoim", "gluten"]),
    _dish("DISH_060", "MERCH_010", "Suco Verde Detox 400ml", "bebida", 11.90, 4.5, 46,
          "Couve, maçã, gengibre e limão batidos com água de coco, prensado a frio.",
          tags=["vegano", "sem_gluten"]),

    # --- Taco Loko (MERCH_011, mexicana) ---
    _dish("DISH_061", "MERCH_011", "Taco de Camarão (2 unidades)", "taco", 26.90, 4.6, 62,
          "Dois tacos de tortilha macia com camarão grelhado ao molho chipotle levemente picante "
          "e creme azedo.",
          tags=["picante"], alergenos=["camarao", "gluten", "lactose"]),
    _dish("DISH_062", "MERCH_011", "Taco de Carnitas (3 unidades)", "taco", 28.90, 4.5, 76,
          "Três tacos de carnitas: porco desfiado suculento com cebola, coentro e molho de "
          "pimenta defumada.",
          tags=["mais_pedido", "picante"], alergenos=["gluten"]),
    _dish("DISH_063", "MERCH_011", "Burrito de Frango", "burrito", 27.90, 4.4, 60,
          "Burrito gigante de frango desfiado com arroz mexicano, feijão, queijo e guacamole.",
          alergenos=["gluten", "lactose"]),
    _dish("DISH_064", "MERCH_011", "Nachos com Guacamole e Cheddar", "entrada", 24.90, 4.5, 57,
          "Totopos crocantes cobertos com cheddar derretido, guacamole fresco, pico de gallo e "
          "jalapeños.",
          tags=["vegetariano", "picante"], alergenos=["lactose"], serve_pessoas=2),
    _dish("DISH_065", "MERCH_011", "Quesadilla de Queijo", "entrada", 22.90, 4.4, 48,
          "Tortilha de trigo dourada na chapa recheada de queijo derretido, servida com sour cream.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_066", "MERCH_011", "Refrigerante de Limão Lata 350ml", "bebida", 7.90, 4.3, 38,
          "Refrigerante de limão lata 350ml bem gelado."),

    # --- Padoca do Bairro (MERCH_012, padaria_cafe) ---
    _dish("DISH_067", "MERCH_012", "Bolo de Cenoura com Cobertura de Chocolate", "doce", 9.90, 4.9, 87,
          "Fatia caprichada de bolo de cenoura fofinho com muita cobertura de chocolate meio "
          "amargo, receita de família.",
          tags=["vegetariano", "mais_pedido"], alergenos=["gluten", "lactose", "ovo"]),
    _dish("DISH_068", "MERCH_012", "Pão na Chapa com Manteiga", "lanche", 7.90, 4.7, 90,
          "Pão francês fresquinho prensado na chapa com manteiga derretida.",
          tags=["vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_069", "MERCH_012", "Combo Café da Manhã", "combo", 19.90, 4.8, 72,
          "Pão na chapa, café coado grande e suco de laranja natural. O trio matinal da padoca.",
          tags=["promo", "vegetariano"], alergenos=["gluten", "lactose"]),
    _dish("DISH_070", "MERCH_012", "Pão de Queijo (6 unidades)", "lanche", 11.90, 4.8, 81,
          "Meia dúzia de pão de queijo mineiro quentinho, naturalmente sem glúten.",
          tags=["vegetariano", "sem_gluten"], alergenos=["lactose", "ovo"]),
    _dish("DISH_071", "MERCH_012", "Misto Quente", "lanche", 12.90, 4.6, 67,
          "Misto quente na chapa com presunto e queijo derretido no pão de forma.",
          alergenos=["gluten", "lactose"]),
    _dish("DISH_072", "MERCH_012", "Café com Leite Grande 300ml", "bebida", 8.90, 4.7, 74,
          "Café coado na hora com leite vaporizado, o pingado grande da padoca.",
          tags=["vegetariano"], alergenos=["lactose"]),
]


# ═══════════════════════════════════════════════════════════════════════════
#  ORDERS (12) - 10 for Gabriel + 2 fillers. Storylines:
#    (a) AIQ-8842 out for delivery RIGHT NOW (Temaki do Tio combo, courier
#        Jonas, left the store 12 minutes ago);
#    (b) AIQ-8807 delivered yesterday with the large fries missing (the
#        instant refund flagship);
#    (c) coherent history: Friday = pizza at Forno da Vila (3x), recurring
#        Japanese, 1 marmita, 1 açaí, and the 2025-05 wrong-item order behind
#        the single historical refund (0.9% refund rate).
#  Totals always derive from the item list, so the math never drifts.
# ═══════════════════════════════════════════════════════════════════════════

def _item(dish_id: str, nome: str, qty: int, preco: float) -> dict:
    return {"dish_id": dish_id, "nome": nome, "qty": qty, "preco": preco}


def _order(
    order_id: str,
    customer_id: str,
    merchant_id: str,
    itens: list[dict],
    status: str,
    criado_em: str,
    *,
    courier_id: str | None = None,
    entregue_em: str | None = None,
    pagamento: str = "pix",
    observacao: str | None = None,
) -> dict:
    """Build an order row; total is always the sum of the embedded items."""
    total = round(sum(item["qty"] * item["preco"] for item in itens), 2)
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "merchant_id": merchant_id,
        "itens": itens,
        "total": total,
        "status": status,
        "courier_id": courier_id,
        "criado_em": criado_em,
        "entregue_em": entregue_em,
        "pagamento": pagamento,
        "observacao": observacao,
    }


ORDERS = [
    # (a) CANONICAL: out for delivery right now with courier Jonas (CUR_001)
    _order("AIQ-8842", DEMO_USER_ID, "MERCH_001",
           [_item("DISH_004", "Combo Xodó: 2 Temakis de Salmão + Hot Roll", 1, 84.90)],
           "saiu_para_entrega", "2026-07-15T11:14:00+00:00",
           courier_id="CUR_001", pagamento="pix",
           observacao="Capricha no gengibre e no wasabi, por favor."),
    # (b) CANONICAL: yesterday's order with the missing large fries
    _order("AIQ-8807", DEMO_USER_ID, "MERCH_004",
           [_item("DISH_019", "Combo Cheddar Bacon", 1, 32.90),
            _item("DISH_020", "Batata Frita Grande", 1, 12.90),
            _item("DISH_024", "Guaraná Lata 350ml", 1, 9.00)],
           "entregue", "2026-07-14T22:12:00+00:00",
           courier_id="CUR_003", entregue_em="2026-07-14T22:54:00+00:00", pagamento="credito",
           observacao="Entrega concluída, mas a batata frita grande não veio na sacola. "
                      "Item faltante relatado pelo cliente."),
    # (c) History: Sunday breakfast at the padoca (the carrot cake tie-in)
    _order("AIQ-8835", DEMO_USER_ID, "MERCH_012",
           [_item("DISH_069", "Combo Café da Manhã", 1, 19.90),
            _item("DISH_067", "Bolo de Cenoura com Cobertura de Chocolate", 1, 9.90)],
           "entregue", "2026-07-12T11:05:00+00:00",
           courier_id="CUR_002", entregue_em="2026-07-12T11:38:00+00:00", pagamento="pix"),
    # (c) Friday pizza #3 (2026-07-10 is a Friday)
    _order("AIQ-8830", DEMO_USER_ID, "MERCH_003",
           [_item("DISH_014", "Pizza Calabresa (8 fatias)", 1, 52.90),
            _item("DISH_018", "Guaraná 2 Litros", 1, 14.90)],
           "entregue", "2026-07-10T22:35:00+00:00",
           courier_id="CUR_001", entregue_em="2026-07-10T23:22:00+00:00", pagamento="credito",
           observacao="Sexta da pizza. Sem cebola na calabresa, por favor."),
    # (c) Recurring Japanese: two salmon temakis at Temaki do Tio
    _order("AIQ-8824", DEMO_USER_ID, "MERCH_001",
           [_item("DISH_001", "Temaki de Salmão com Cream Cheese", 2, 32.90)],
           "entregue", "2026-07-07T22:48:00+00:00",
           courier_id="CUR_002", entregue_em="2026-07-07T23:26:00+00:00", pagamento="pix"),
    # (c) Sunday açaí
    _order("AIQ-8818", DEMO_USER_ID, "MERCH_005",
           [_item("DISH_025", "Açaí 500ml com Adicionais", 1, 24.90),
            _item("DISH_026", "Açaí 300ml Tradicional", 1, 16.90)],
           "entregue", "2026-07-05T18:20:00+00:00",
           courier_id="CUR_003", entregue_em="2026-07-05T18:52:00+00:00", pagamento="pix"),
    # (c) Friday pizza #2 (2026-07-03 is a Friday)
    _order("AIQ-8813", DEMO_USER_ID, "MERCH_003",
           [_item("DISH_016", "Pizza Quatro Queijos (8 fatias)", 1, 58.90)],
           "entregue", "2026-07-03T22:41:00+00:00",
           courier_id="CUR_001", entregue_em="2026-07-03T23:30:00+00:00", pagamento="credito",
           observacao="Sexta da pizza com a família."),
    # (c) Monday marmita
    _order("AIQ-8804", DEMO_USER_ID, "MERCH_006",
           [_item("DISH_031", "Marmita da Vó Tamanho M", 1, 22.90),
            _item("DISH_036", "Suco de Laranja Natural 500ml", 1, 9.90)],
           "entregue", "2026-06-29T14:55:00+00:00",
           courier_id="CUR_003", entregue_em="2026-06-29T15:31:00+00:00", pagamento="pix"),
    # (c) Friday pizza #1 (2026-06-26 is a Friday)
    _order("AIQ-8801", DEMO_USER_ID, "MERCH_003",
           [_item("DISH_013", "Pizza Margherita (8 fatias)", 1, 49.90),
            _item("DISH_018", "Guaraná 2 Litros", 1, 14.90)],
           "entregue", "2026-06-26T22:30:00+00:00",
           courier_id="CUR_002", entregue_em="2026-06-26T23:18:00+00:00", pagamento="dinheiro",
           observacao="Troco para R$ 70,00."),
    # (c) 14 months ago: the wrong-item order behind the single refund (REF_001)
    _order("AIQ-8517", DEMO_USER_ID, "MERCH_005",
           [_item("DISH_027", "Barca de Açaí 1 Litro", 1, 39.90),
            _item("DISH_029", "Milk-shake de Morango 400ml", 1, 18.90)],
           "entregue", "2025-05-17T19:10:00+00:00",
           courier_id="CUR_002", entregue_em="2025-05-17T19:47:00+00:00", pagamento="credito",
           observacao="Milk-shake veio de chocolate em vez de morango. Item errado, "
                      "reembolso parcial solicitado."),

    # --- Fillers from other fominhas (dataset density) ---
    _order("AIQ-8839", "CUST_002", "MERCH_009",
           [_item("DISH_051", "Combo Churrasco Família", 1, 79.90),
            _item("DISH_054", "Guaraná 1,5 Litro", 1, 12.90)],
           "em_preparo", "2026-07-15T11:35:00+00:00", pagamento="pix"),
    _order("AIQ-8837", "CUST_003", "MERCH_010",
           [_item("DISH_055", "Bowl Vegano de Falafel", 1, 29.90),
            _item("DISH_060", "Suco Verde Detox 400ml", 1, 11.90)],
           "recebido", "2026-07-15T11:52:00+00:00", pagamento="credito"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  COURIERS (3) - Jonas carries the live order AIQ-8842; his position encodes
#  the canonical "left the store 12 minutes ago" fact.
# ═══════════════════════════════════════════════════════════════════════════

COURIERS = [
    {
        "courier_id": "CUR_001", "nome": "Jonas Pereira", "veiculo": "moto",
        "status": "em_rota",
        "posicao_atual": "a 1,2 km do destino, subindo a Av. Colombo (saiu da loja há 12 minutos)",
        "avaliacao": 4.9,
    },
    {
        "courier_id": "CUR_002", "nome": "Carla Mendes", "veiculo": "bike",
        "status": "disponivel",
        "posicao_atual": "na praça da Catedral, centro de Maringá",
        "avaliacao": 4.8,
    },
    {
        "courier_id": "CUR_003", "nome": "Edson Luiz", "veiculo": "moto",
        "status": "disponivel",
        "posicao_atual": "próximo ao Parque do Ingá",
        "avaliacao": 4.7,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  REFUND REQUESTS (1) - the single historical refund in 14 months (2025-05,
#  wrong item, approved on the spot). Anchors the 0.9% refund_rate story.
# ═══════════════════════════════════════════════════════════════════════════

REFUND_REQUESTS = [
    {
        "refund_id": "REF_001",
        "customer_id": DEMO_USER_ID,
        "order_id": "AIQ-8517",
        "motivo": "item_errado",
        "valor": 18.90,
        "status": "aprovado",
        "data_abertura": "2025-05-17T20:05:00+00:00",
        "data_resolucao": "2025-05-17T20:06:00+00:00",
        "descricao": "Pedi milk-shake de morango e veio de chocolate. Foi o único item errado do pedido.",
        "resolucao": "Reembolso aprovado na hora pelo bom histórico do fominha. "
                     "Crédito de R$ 18,90 na carteira aiqfome.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  VOUCHERS (1) - active R$ 15.00 loyalty voucher for the demo fominha
# ═══════════════════════════════════════════════════════════════════════════

VOUCHERS = [
    {
        "voucher_id": "VOU_001",
        "customer_id": DEMO_USER_ID,
        "valor": 15.00,
        "motivo": "fidelidade clube aiqfome",
        "validade": "2026-07-31",
        "status": "ativo",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (10) - aiqfome policies in PT-BR
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {
        "policy_id": "POL_001", "title": "Reembolso e itens faltantes", "category": "reembolso",
        "content": (
            "Se um item veio errado, faltou na sacola ou chegou impróprio pro consumo, o fominha "
            "pode pedir reembolso total ou parcial direto pelo app. Fominhas com bom histórico "
            "(taxa de reembolso baixa e score de fraude saudável) têm aprovação instantânea, com "
            "crédito na carteira aiqfome na hora. Casos atípicos ou de alto valor passam por "
            "verificação com foto do pedido e o prazo de análise é de até 24 horas. O reembolso "
            "pode ser em crédito na carteira ou estorno na forma de pagamento original."
        ),
    },
    {
        "policy_id": "POL_002", "title": "Clube aiqfome", "category": "clube",
        "content": (
            "O clube aiqfome dá frete grátis em todos os restaurantes parceiros, identificados "
            "com o selo do clube no app. No plano promocional vigente não há mensalidade. "
            "Assinantes também recebem vouchers de fidelidade periódicos e ofertas exclusivas "
            "dos parceiros. O benefício de frete grátis vale para entregas na cidade do fominha, "
            "sem valor mínimo de pedido nos parceiros."
        ),
    },
    {
        "policy_id": "POL_003", "title": "Prazo de entrega", "category": "entrega",
        "content": (
            "Cada restaurante informa seu tempo estimado de entrega (ETA), que aparece no app "
            "antes de fechar o pedido. A média da plataforma fica entre 35 e 50 minutos, variando "
            "por distância, clima e movimento. Depois que o pedido sai pra entrega, o fominha "
            "acompanha o entregador em tempo real no mapa. Se o pedido atrasar muito além do ETA, "
            "o suporte pode oferecer crédito ou reembolso conforme o caso."
        ),
    },
    {
        "policy_id": "POL_004", "title": "Taxa de entrega", "category": "taxa",
        "content": (
            "A taxa de entrega varia por restaurante e por distância, e é exibida antes da "
            "confirmação do pedido. Assinantes do clube aiqfome têm frete grátis nos restaurantes "
            "parceiros. Em horários de pico ou condições de clima adversas pode haver taxa "
            "dinâmica, sempre informada de forma transparente na tela de pagamento."
        ),
    },
    {
        "policy_id": "POL_005", "title": "Formas de pagamento", "category": "pagamento",
        "content": (
            "O aiqfome aceita Pix, cartão de crédito e débito pelo app e dinheiro na entrega. "
            "Pagando em dinheiro, o fominha informa o valor pra troco no fechamento do pedido. "
            "Créditos de reembolso e vouchers ficam na carteira aiqfome e são aplicados "
            "automaticamente no pagamento quando elegíveis."
        ),
    },
    {
        "policy_id": "POL_006", "title": "Cancelamento de pedido", "category": "cancelamento",
        "content": (
            "O cancelamento é gratuito enquanto o restaurante ainda não aceitou o pedido. Depois "
            "do aceite, o cancelamento pode ter cobrança proporcional do que já foi preparado. "
            "Se o restaurante cancelar o pedido por qualquer motivo, o reembolso é integral e "
            "automático, sem necessidade de acionar o suporte."
        ),
    },
    {
        "policy_id": "POL_007", "title": "Cupons e vouchers", "category": "cupom",
        "content": (
            "Cupons e vouchers são aplicados na tela de pagamento antes de confirmar o pedido. "
            "Cada cupom tem validade própria, indicada no detalhe do benefício, e os descontos "
            "não são cumulativos: vale um benefício por pedido. Vouchers de fidelidade do clube "
            "aiqfome aparecem na carteira e podem ser usados em qualquer restaurante da "
            "plataforma dentro da validade."
        ),
    },
    {
        "policy_id": "POL_008", "title": "Alergias e ingredientes", "category": "alergia",
        "content": (
            "Os cardápios exibem alertas de alérgenos informados pelos restaurantes, como "
            "camarão, glúten, lactose, amendoim e ovo. A responsabilidade é compartilhada: o "
            "restaurante mantém as informações do cardápio atualizadas e o fominha deve sempre "
            "avisar restrições alimentares no campo de observação do pedido. Mesmo com os "
            "alertas, pode haver contaminação cruzada na cozinha, por isso casos de alergia "
            "grave merecem contato direto com o restaurante antes de pedir."
        ),
    },
    {
        "policy_id": "POL_009", "title": "Gorjeta do entregador", "category": "gorjeta",
        "content": (
            "A gorjeta é opcional e pode ser adicionada no fechamento do pedido ou depois da "
            "entrega, na avaliação. O valor é repassado 100% ao entregador, sem desconto de "
            "taxas da plataforma."
        ),
    },
    {
        "policy_id": "POL_010", "title": "Atendimento e suporte", "category": "suporte",
        "content": (
            "O AIQ, concierge do aiqfome, atende 24 horas pelo app: acompanha pedidos, resolve "
            "reembolsos e responde dúvidas de cardápio e de conta. Casos que precisam de "
            "atendimento humano geram protocolo com resposta em até 24 horas. O histórico de "
            "pedidos, reembolsos e vouchers do fominha fica disponível pro time de atendimento, "
            "que resolve sem pedir os dados de novo."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE STORE (1) - Gabriel's online features, read in real time by AIQ.
#  Calibrated for the flagship: 214 orders with 0.9% refund rate and fraud
#  score 0.03 unlock the instant refund; favorite cuisine and Friday peak
#  power the concierge recommendations; the R$ 15.00 voucher closes offers.
# ═══════════════════════════════════════════════════════════════════════════

FEATURE_STORE = [
    {
        "customer_id": DEMO_USER_ID,
        "pedidos_total": 214,
        "pedidos_90d": 23,
        "ticket_medio": 67.40,
        "ltv_12m": 4980.00,
        "refund_rate_pct": 0.9,
        "fraude_score": 0.03,
        "cozinha_favorita": "japonesa",
        "dia_pico": "sexta",
        "clube_aiqfome": True,
        "voucher_ativo": 15.00,
        "cidade": "maringa",
        "fominha_desde": "2019-04",
        "ultima_atualizacao": ts(now - timedelta(minutes=8)),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN - generate embeddings + write JSONLs
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

    print("Gerando embeddings das políticas e do cardápio...")
    policy_contents = [p["content"] for p in POLICIES_TEXT]
    policy_embeddings = embed(policy_contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, policy_embeddings)]

    dish_texts = [f"{d['nome']}. {d['descricao']}" for d in DISHES]
    dish_embeddings = embed(dish_texts)
    dishes = [{**d, "content_embedding": emb} for d, emb in zip(DISHES, dish_embeddings)]

    print("Escrevendo arquivos JSONL:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "merchants.jsonl", MERCHANTS)
    write_jsonl(resolved_output_dir, "dishes.jsonl", dishes)
    write_jsonl(resolved_output_dir, "orders.jsonl", ORDERS)
    write_jsonl(resolved_output_dir, "couriers.jsonl", COURIERS)
    write_jsonl(resolved_output_dir, "refund_requests.jsonl", REFUND_REQUESTS)
    write_jsonl(resolved_output_dir, "vouchers.jsonl", VOUCHERS)
    write_jsonl(resolved_output_dir, "feature_store.jsonl", FEATURE_STORE)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["nome"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nFominha demo: {demo['nome']} ({demo['customer_id']})")
    print("Pronto.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["customer_id"],
            "DEMO_USER_NAME": demo["nome"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "customers": len(CUSTOMERS),
            "merchants": len(MERCHANTS),
            "dishes": len(DISHES),
            "orders": len(ORDERS),
            "couriers": len(COURIERS),
            "refund_requests": len(REFUND_REQUESTS),
            "vouchers": len(VOUCHERS),
            "feature_store": len(FEATURE_STORE),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
