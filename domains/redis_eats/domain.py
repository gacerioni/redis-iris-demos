from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Sequence

from backend.app.memory_service import MemoryService
from backend.app.core.domain_contract import (
    BrandingConfig,
    DomainManifest,
    GeneratedDataset,
    GuardrailConfig,
    GuardrailRouteConfig,
    IdentityConfig,
    InternalToolDefinition,
    NamespaceConfig,
    PromptCard,
    RagConfig,
    SeedLangCacheEntry,
    SeedMemory,
    ThemeConfig,
)
from backend.app.core.domain_schema import EntitySpec, validate_entity_specs
from backend.app.redis_connection import create_redis_client
from domains.redis_eats.data_generator import generate_demo_data
from domains.redis_eats.prompt import build_system_prompt
from domains.redis_eats.schema import ENTITY_SPECS

ROOT = Path(__file__).resolve().parents[2]


class RedisEatsDomain:
    manifest = DomainManifest(
        id="redis_eats",
        description="Demo brasileiro de atendimento de delivery — compara Context Surfaces vs RAG simples, com humor paulistano.",
        generated_models_module="domains.redis_eats.generated_models",
        generated_models_path="domains/redis_eats/generated_models.py",
        output_dir="output/redis_eats",
        branding=BrandingConfig(
            app_name="Redis Eats",
            subtitle="Atendimento ao Cliente",
            hero_title="Como posso te ajudar?",
            placeholder_text="Pergunta do pedido, status da entrega, política da casa…",
            logo_path="domains/redis_eats/assets/logo.svg",
            demo_steps=[
                "Por que meu pedido tá demorando tanto?",
                "Lembra pra próxima: sem coentro em pedido nenhum, e prefiro motoboy que toca campainha em vez de ligar.",
                "Clica em Memory",
                "Sabendo o que você sabe de mim, olha meus pedidos recentes e me sugere o que pedir agora.",
            ],
            starter_prompts=[
                PromptCard(eyebrow="Context", title="Por que meu pedido tá demorando?", prompt="Por que meu pedido tá demorando tanto?"),
                PromptCard(eyebrow="Context", title="Meus pedidos recentes", prompt="Me mostra meus últimos pedidos"),
                PromptCard(eyebrow="Memory", title="Salvar preferências", prompt="Lembra que eu não como coentro, em pedido nenhum."),
                PromptCard(eyebrow="Memory", title="Recomendação", prompt="O que você sugere pra eu pedir agora?"),
                PromptCard(eyebrow="Cached", title="Política de reembolso", prompt="Qual a política de reembolso pra entregas atrasadas?"),
            ],
            theme=ThemeConfig(
                bg="#0d0f14",
                bg_accent_a="rgba(255, 68, 56, 0.12)",
                bg_accent_b="rgba(255, 140, 66, 0.1)",
                panel="rgba(20, 23, 32, 0.88)",
                panel_strong="rgba(24, 28, 40, 0.96)",
                panel_elevated="rgba(30, 35, 50, 0.92)",
                line="rgba(255, 120, 90, 0.1)",
                line_strong="rgba(255, 120, 90, 0.18)",
                text="#f2f0ed",
                muted="#9a9490",
                soft="#d4cfc8",
                accent="#ff4438",
                user="#2a2420",
                landing_bg="#FFF3D9",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="redis_eats",
            dataset_meta_key="redis_eats:meta:dataset",
            checkpoint_prefix="redis_eats:checkpoint",
            checkpoint_write_prefix="redis_eats:checkpoint_write",
            redis_instance_name="Redis Eats Redis Cloud",
            surface_name="Redis Eats Delivery Surface",
            agent_name="Redis Eats Delivery Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_policies",
            status_text="Buscando políticas via similaridade vetorial…",
            generating_text="Gerando resposta…",
            index_name_contains="policy",
            vector_field="content_embedding",
            return_fields=["title", "category", "content", "policy_id"],
            num_results=3,
            answer_system_prompt=(
                "Você é o assistente de atendimento do Redis Eats. "
                "Responda usando APENAS os documentos de política abaixo. Se as políticas não cobrirem "
                "a pergunta, diga isso. Seja conciso e prestativo. Responda em português brasileiro."
            ),
        ),
        identity=IdentityConfig(
            default_id="CUST_DEMO_001",
            default_name="Gabriel Cerioni",
            default_email="gabriel.cerioni@redis.com",
            description=(
                "Retorna o ID, nome e email do cliente logado. "
                "Chame isso sempre que o cliente perguntar sobre os pedidos, conta ou histórico dele."
            ),
        ),
        guardrail=GuardrailConfig(
            router_name="redis-eats-guardrails",
            allowed_route_name="food_delivery",
            routes=[
                GuardrailRouteConfig(
                    name="food_delivery",
                    references=[
                        "Cadê meu pedido?",
                        "Onde tá meu pedido?",
                        "Qual o status da minha entrega?",
                        "Meu pedido tá atrasado",
                        "Por que meu pedido tá demorando?",
                        "Por que meu pedido tá demorando tanto?",
                        "Por que tá demorando tanto?",
                        "Pô, tá demorando mesmo, hein",
                        "Tá demorando muito esse pedido",
                        "Demora demais esse pedido",
                        "Já era pra ter chegado",
                        "Cadê o motoboy?",
                        "Onde tá o motoboy?",
                        "Quando minha comida chega?",
                        "Qual o ETA da entrega?",
                        "Rastrear meu pedido",
                        "Meu pedido não chegou",
                        "O motoboy não apareceu",
                        "Me mostra meu histórico de pedidos",
                        "Quais foram meus últimos pedidos?",
                        "Quero repetir meu último pedido",
                        "Dá pra cancelar o pedido?",
                        "Preciso mudar meu pedido",
                        "O que eu pedi da última vez?",
                        "Quais restaurantes tem aqui perto?",
                        "Me recomenda algo apimentado",
                        "O que tá bom pra hoje?",
                        "Tem opção vegetariana?",
                        "O que você sugere pra eu pedir hoje?",
                        "Procurando comida italiana",
                        "Tô a fim de pizza",
                        "Quero um lanche",
                        "Tô com fome",
                        "Quero pedir um açaí",
                        "Quero meu dinheiro de volta",
                        "Fui cobrado em dobro",
                        "A comida chegou fria",
                        "O pedido veio errado",
                        "Como faço pra ter o reembolso?",
                        "Tenho uma dúvida na cobrança",
                        "Usa meu crédito nesse pedido",
                        "Qual a política de reembolso?",
                        "Qual a política de cancelamento?",
                        "Quanto tempo costuma demorar a entrega?",
                        "Atualizar meu endereço de entrega",
                        "Qual o status da minha conta?",
                        "Como mudo a forma de pagamento?",
                        "Eu tenho assinatura?",
                        "Sou Plus ou Premium?",
                        "Lembra que eu sou alérgico a amendoim",
                        "O que você sabe sobre mim?",
                        "Prefiro entrega sem contato",
                        "Salva minha preferência por comida apimentada",
                        "Quais minhas preferências alimentares?",
                        "Entrega sempre na portaria",
                        "Não toca o interfone, liga no meu celular",
                        "Sim",
                        "Não",
                        "Por favor",
                        "Não, valeu",
                        "Me conta mais",
                        "Pode mandar",
                        "Manda ver",
                        "Beleza",
                        "Valeu",
                        "Obrigado",
                        "Brigadão",
                        "Oi",
                        "Bom dia",
                        "E aí",
                        "Pode me ajudar?",
                        "Tenho uma dúvida",
                        "O que mais você consegue fazer?",
                        "É isso, valeu",
                        "Tranquilo",
                        "OK",
                    ],
                    distance_threshold=0.85,
                ),
                GuardrailRouteConfig(
                    name="off_topic",
                    references=[
                        "Como tá o tempo hoje?",
                        "Me escreve um script em Python",
                        "Me ajuda no dever de casa",
                        "Me conta uma piada",
                        "Quanto é 2 + 2?",
                        "Quem ganhou o jogo do Brasil?",
                        "Me explica física quântica",
                        "Escreve um poema de amor",
                        "Quais as últimas notícias?",
                        "Quem é o presidente?",
                        "Traduz isso pra inglês",
                        "Me ajuda a debugar esse código",
                        "Qual o sentido da vida?",
                        "Joga um jogo comigo",
                        "Me fala sobre a Segunda Guerra",
                        "Como tá a Bolsa?",
                        "Como conserto meu carro?",
                        "Qual a capital da França?",
                        "Resolve essa equação de matemática",
                        "Gera uma imagem de um gato",
                    ],
                    distance_threshold=0.5,
                ),
            ],
        ),
        seed_memories=[
            SeedMemory(
                text=(
                    "Gabriel mora no 18º andar do prédio na Rua Aspicuelta, em Pinheiros. "
                    "O porteiro (Seu Genival) não atende o interfone depois das 22h — sempre instruir o motoboy a ligar direto no celular do cliente."
                ),
                topics=["entrega", "endereco", "logistica"],
            ),
            SeedMemory(
                text=(
                    "Gabriel detesta coentro. Em qualquer pedido de comida tailandesa, mexicana ou nordestina, "
                    "adicionar a observação 'sem coentro' mesmo se o cliente esquecer de marcar — ele já reclamou 2x."
                ),
                topics=["alimentar", "preferencias", "restricoes"],
            ),
            SeedMemory(
                text=(
                    "Gabriel é Plus desde mar/2023. Recebeu 4 cupons de cortesia por atrasos reais — "
                    "histórico de pagamento impecável, NÃO é abusador de política. Tratar com prioridade."
                ),
                topics=["conta", "assinatura", "fidelidade"],
            ),
            SeedMemory(
                text=(
                    "Em dias de jogo do Brasil na Copa, Gabriel costuma antecipar pedidos em ~2h. "
                    "Não sugerir restaurantes com fila >40min em dia de jogo — ele perde a paciência e cancela."
                ),
                topics=["preferencias", "horario", "padroes_de_uso"],
            ),
            SeedMemory(
                text=(
                    "Gabriel é flamenguista de carteirinha. Em dia de jogo do Mengão, sugerir restaurantes "
                    "que tenham bandeira ou menção ao rubro-negro — ele curte. No geral, valorizar narrativas "
                    "que conversem com o time do coração dele."
                ),
                topics=["preferencias", "marketing", "personalizacao"],
            ),
            SeedMemory(
                text=(
                    "Gabriel prefere motoboy que toca a campainha antes de ligar. "
                    "Já cancelou pedido em mai/2026 por motoboy que ligou direto — sempre orientar a tocar campainha primeiro, ligar só se não houver resposta."
                ),
                topics=["entrega", "preferencias", "atendimento"],
            ),
        ],
        seed_langcache=[
            SeedLangCacheEntry(
                prompt="Qual a política de voucher pra entregas atrasadas?",
                response=(
                    "Em entregas atrasadas, o Redis Eats aplica voucher de cortesia automático "
                    "no próximo pedido, com valores em reais conforme o tempo de atraso:\n\n"
                    "- **15 a 29 minutos** de atraso: voucher de **R$ 10**\n"
                    "- **30 a 44 minutos** de atraso: voucher de **R$ 20**\n"
                    "- **45 a 59 minutos** de atraso: voucher de **R$ 50**\n"
                    "- **60 minutos ou mais** de atraso: voucher de **R$ 100**\n\n"
                    "O voucher é creditado automaticamente em até 24h e vale por 30 dias. "
                    "Em casos de força maior em via pública (carreatas, eventos esportivos), pode rolar bônus extra. "
                    "Manda o número do pedido pra eu confirmar o valor exato do seu caso."
                ),
                attributes={},  # cache foi criado na UI sem attributes configurados; service skipa quando dict vazio
            ),
        ],
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def get_runtime_config(self, settings: Any) -> dict[str, Any]:
        memory_enabled = MemoryService(settings).is_configured() if settings else False
        return {
            "memory_enabled": memory_enabled,
        }

    def build_system_prompt(
        self,
        *,
        mcp_tools: Sequence[dict[str, Any]],
        runtime_config: dict[str, Any] | None = None,
    ) -> str:
        return build_system_prompt(
            mcp_tools=mcp_tools,
            memory_enabled=bool((runtime_config or {}).get("memory_enabled")),
        )

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        del runtime_config
        return (
            "Quando o cliente se referir a 'esse pedido', 'essa cobrança' ou outras referências de seguimento, "
            "resolva a referência pro pedido, pagamento ou chamado exato do turno anterior. Não mencione reembolsos, "
            "créditos ou conclusões de política a menos que os resultados das ferramentas ou a política citada suportem."
        )

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        del runtime_config
        detail = ""
        if isinstance(payload, dict):
            for key in ("query", "text", "order_id", "customer_id", "payment_id", "ticket_id"):
                value = payload.get(key)
                if value:
                    detail = str(value)
                    break

        if tool_name == self.manifest.identity.tool_name:
            return "Identifica o cliente logado antes de consultar dados de conta ou pedidos."
        if tool_name == "get_current_time":
            return "Compara o horário atual com os timestamps de pedido e entrega."
        if tool_name.startswith("search_policy_by_text"):
            return f"Busca diretriz de política: {detail or 'busca em políticas'}."
        if tool_name.startswith("filter_driver_by_"):
            return "Consulta o motoboy designado e o status atual do pedido."
        if tool_name.startswith("filter_payment_by_"):
            return "Inspeciona o pagamento antes de responder sobre cobranças, créditos ou reembolsos."
        if tool_name == "search_customer_memory":
            return "Busca memória durável do cliente: preferências, problemas anteriores, contexto guardado."
        if tool_name == "remember_customer_detail":
            return "Salva um fato ou preferência durável do cliente pra próximas conversas."
        return None

    def get_internal_tool_definitions(
        self,
        *,
        runtime_config: dict[str, Any] | None = None,
    ) -> Sequence[InternalToolDefinition]:
        tools: list[InternalToolDefinition] = [
            InternalToolDefinition(
                name=self.manifest.identity.tool_name,
                description=self.manifest.identity.description,
            ),
            InternalToolDefinition(
                name="get_current_time",
                description=(
                    "Retorna a data e hora atual em UTC (ISO 8601). "
                    "Use isso pra comparar com timestamps de pedido e determinar se uma entrega tá atrasada."
                ),
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description="Retorna um resumo do dataset atual do Redis Eats: contagem de clientes, restaurantes, pedidos e políticas.",
            ),
        ]
        if (runtime_config or {}).get("memory_enabled"):
            tools.extend(
                [
                    InternalToolDefinition(
                        name="search_customer_memory",
                        description=(
                            "Busca memória durável do cliente: preferências, incidentes passados ou fatos de sessões anteriores. "
                            "Use quando o cliente perguntar o que você lembra dele, referir uma preferência, ou pedir continuidade entre conversas."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "O que buscar na memória do cliente."},
                                "limit": {"type": "integer", "description": "Quantidade máxima opcional de memórias a retornar.", "default": 5},
                            },
                            "required": ["query"],
                        },
                    ),
                    InternalToolDefinition(
                        name="remember_customer_detail",
                        description=(
                            "Salva uma preferência ou fato durável do cliente na memória de longo prazo. "
                            "Use APENAS quando o cliente pedir explicitamente pra você lembrar ou declarar uma preferência duradoura clara."
                        ),
                        input_schema={
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "A preferência ou fato durável exato pra lembrar."},
                                "memory_type": {
                                    "type": "string",
                                    "description": "Tipo de memória: semantic pra preferências/fatos, episodic pra evento marcante, message pra nota verbatim.",
                                    "default": "semantic",
                                },
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Tags de tópico opcionais: entrega, comida, preferencias, reembolso, etc.",
                                },
                            },
                            "required": ["text"],
                        },
                    ),
                ]
            )
        return tuple(tools)

    def execute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        from datetime import datetime, timezone

        if tool_name == self.manifest.identity.tool_name:
            identity = self.manifest.identity
            return {
                identity.id_field: os.getenv(identity.id_env_var, identity.default_id),
                "name": os.getenv(identity.name_env_var, identity.default_name),
                "email": os.getenv(identity.email_env_var, identity.default_email),
            }
        if tool_name == "get_current_time":
            return {"current_time": datetime.now(timezone.utc).isoformat(), "timezone": "UTC"}
        if tool_name == "dataset_overview":
            client = create_redis_client(settings)
            raw = client.execute_command("JSON.GET", self.manifest.namespace.dataset_meta_key, "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
            return {"error": "Metadados do dataset não encontrados. Rode o carregador de dados primeiro."}
        return {"error": f"Ferramenta desconhecida: {tool_name}"}

    async def aexecute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        if tool_name not in {"search_customer_memory", "remember_customer_detail"}:
            return self.execute_internal_tool(tool_name, arguments, settings)

        identity = self.manifest.identity
        owner_id = os.getenv(identity.id_env_var, identity.default_id)
        memory_service = MemoryService(settings)
        if not memory_service.is_configured():
            return {"error": "Serviço de memória não está configurado pra essa demo."}

        if tool_name == "search_customer_memory":
            query = str(arguments.get("query", "")).strip()
            if not query:
                return {"error": "query é obrigatório"}
            limit = arguments.get("limit")
            memories = await memory_service.asearch_long_term_memory(
                text=query,
                owner_id=owner_id,
                limit=int(limit) if limit is not None else None,
            )
            return {
                "owner_id": owner_id,
                "query": query,
                "memory_count": len(memories),
                "memories": [
                    {
                        "id": memory.get("id"),
                        "text": memory.get("text"),
                        "memory_type": memory.get("memoryType"),
                        "topics": memory.get("topics", []),
                        "session_id": memory.get("sessionId"),
                        "created_at": memory.get("createdAt"),
                    }
                    for memory in memories
                ],
            }

        # ── remember_customer_detail ───────────────────────────────
        # NOTE: Aqui a gente DESTRAVA a persistência real do LTM (a trava do upstream
        # `demo_blocked=True` era pra demo shareada). Esse fork é local, então a memória
        # persiste de verdade via Redis Agent Memory.
        text = str(arguments.get("text", "")).strip()
        if not text:
            return {"error": "text é obrigatório"}
        memory_type = str(arguments.get("memory_type", "semantic")).strip() or "semantic"
        if memory_type not in {"semantic", "episodic", "message"}:
            memory_type = "semantic"
        topics_raw = arguments.get("topics") or []
        if not isinstance(topics_raw, list):
            topics_raw = []
        topics = [str(t).strip() for t in topics_raw if str(t).strip()]

        try:
            # MemoryService.create_long_term_memory é síncrono (usa httpx.Client).
            # Rodamos em thread separada pra não bloquear o event loop.
            created = await asyncio.to_thread(
                memory_service.create_long_term_memory,
                text=text,
                owner_id=owner_id,
                memory_type=memory_type,
                topics=topics,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "owner_id": owner_id,
                "saved_text": text,
                "memory_type": memory_type,
                "topics": topics,
                "persisted": False,
                "error": f"Falha ao salvar memória: {exc}",
            }

        return {
            "owner_id": owner_id,
            "saved_text": text,
            "memory_type": memory_type,
            "topics": topics,
            "persisted": True,
            "response": created,
        }

    def write_dataset_meta(self, *, settings: Any, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        summary = {
            "customers": len(records.get("Customer", [])),
            "restaurants": len(records.get("Restaurant", [])),
            "drivers": len(records.get("Driver", [])),
            "orders": len(records.get("Order", [])),
            "order_items": len(records.get("OrderItem", [])),
            "delivery_events": len(records.get("DeliveryEvent", [])),
            "payments": len(records.get("Payment", [])),
            "support_tickets": len(records.get("SupportTicket", [])),
            "policies": len(records.get("Policy", [])),
        }
        client = create_redis_client(settings)
        client.execute_command(
            "JSON.SET",
            self.manifest.namespace.dataset_meta_key,
            "$",
            json.dumps(summary, ensure_ascii=False),
        )
        return summary

    def generate_demo_data(
        self,
        *,
        output_dir: Path,
        seed: int | None = None,
        update_env_file: bool = True,
    ) -> GeneratedDataset:
        return generate_demo_data(output_dir=output_dir, seed=seed, update_env_file=update_env_file)

    def validate(self) -> list[str]:
        errors = validate_entity_specs(self.get_entity_specs())
        if not (ROOT / self.manifest.branding.logo_path).exists():
            errors.append(f"Arquivo de logo não encontrado: {self.manifest.branding.logo_path}")
        if not self.manifest.branding.starter_prompts:
            errors.append("Branding precisa definir pelo menos um starter prompt")
        return errors


DOMAIN = RedisEatsDomain()
