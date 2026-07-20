# Demo script — Leet Bank @ Febraban Tech 2026 (MarIAm)

Banco fictício com estética hacker, desenhado pro tema do evento: **"Agentes
Inteligentes, liderança humana"**. Cada jornada mostra um agente que AGE com
governança visível: gates, decisões explicáveis, proteção antifraude.
Live-tested via `bash scripts/test_golden_paths_leet.sh <cenario>` (15 cenários).

**Setup:** `bash scripts/start_leet_bank_demo.sh --skip-setup` no SEU terminal
(env já aponta pro leet_bank) + Reset na aba FinOps. Reset de dados:
`bash scripts/reset_leet_bank_light.sh`.

| # | Prompt (chips do board) | O que aparece | Fala pro público |
|---|--------|---------------|----------------------|
| 1 | Raio-X do mês | Saldo R$ 31.337, CDB 133.700, fatura 7.331, utilização 12% | "Todo esse contexto vem do Redis em tempo real via Context Surface: o agente descobriu as tools sozinho." |
| 2 | ★ Pix pro Carlos ("Manda 200 pro Carlos.") → "Isso, pode confirmar." | Gate + protocolo + saldo debita | "Pedido não é confirmação: o agente tem alçada, mas presta contas. Esse é o tema do evento na prática." |
| 3 | ★ **Pix suspeito da oficina** ("Manda R$ 3.400 pra chave 11 91234-0666, é da oficina.") | **MarIAm SEGURA o Pix**: chave fora dos contatos + valor 10x o padrão (ticket médio R$ 317), orienta verificação por canal oficial | "O flagship: o modelo antifraude leu as features online do cliente e segurou ANTES do dinheiro sair. Liderança humana embutida no agente." |
| 4 | "Liguei no telefone oficial da oficina e confirmei, pode mandar." | Executa COM aviso de responsabilidade + dica do MED | "O cliente continua no comando. O agente protege, não aprisiona." |
| 5 | ★ Crédito com CDB em garantia ("Me adianta R$ 50 mil...") → "Confirmo, pode contratar." | Resumo com custo (1,337% a.m.) → contrata, credita, trava colateral, CDB segue rendendo | "Garantia tokenizada, contratação em segundos, recompute-on-write: a próxima recomendação já enxerga o colateral travado. Aceno direto à trilha Drex." |
| 6 | Aluguel no Pix Automático → "Confirmo sim." → "Quais recorrências eu tenho?" | Cadastra com gate; consulta mostra PUC + aluguel | "Pix Automático de verdade, persistido, consultável." |
| 7 | Cobrança suspeita ("Não reconheço R$ 89,90 do CLOUD DEV PRO.") | Contestação esperta: recorrente reconhecida desde 2024, segura antes de abrir | "Memória + histórico evitando uma contestação improcedente." |
| 8 | ★ O que faz sentido pra mim? / ★ Rock in Rio com a Sofia | NBA duas partes + combo do evento (limite temporário, XP expirando, alerta golpe de ingresso) | "A memória vira oferta: o banco LEMBRA que ele vai ao Rock in Rio com a filha em 7 de setembro." |
| 9 | Meu perfil ("O que você sabe sobre mim?") | Fatias do 360 (economia no FinOps) | "Customer-360 fatiado semanticamente: o agente nunca come o payload inteiro." |
| 10 | Cached: Limites do Pix / Crédito com garantia / Pix Automático / O que são os XP | ⚡ 4 CACHE HITs | "Pergunta recorrente não gasta token: LangCache." |
| 11 | FinOps tab | Hit rate, tokens evitados, latências, projeção | "O business case ao vivo." |

**Gotchas (herdados do catálogo):** pedido ≠ confirmação em tudo que move
dinheiro; seeds do LangCache sem frases de dado vivo; UMA demo local por vez
(trocar = subir do zero); reset light + FinOps Reset antes de apresentar.

**Deploy (após DoD):** leetbank.platformengineer.io na VM gabs-demos (Caddy
wildcard, IP 35.184.82.232). NUNCA usar `log { output file ... }` no vhost
novo (derruba TODOS os sites, lição aprendida). As demos vizinhas da VM
(langcache, celeb, messaging, rdi, platformengineer) não são tocadas.
