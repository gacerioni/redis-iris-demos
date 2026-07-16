# Deploy da BIA (Bradesco) em irisbia.platformengineer.io

Demo `bradesco_bia` rodando isolada no bastion `56.124.109.24` (AWS sa-east-1) + Redis Cloud Pro
novo, sem encostar no ambiente local nem no autoscaler que já roda na caixa.

```
DNS A: irisbia.platformengineer.io ──► 56.124.109.24 (EC2 Ubuntu 24.04, sa-east-1)
                                          │
                                          ├─ nginx :443 (TLS certbot) + basic_auth   [vhost novo]
                                          │     ├─ /        → SPA estática (/opt/iris-bia/dist)
                                          │     └─ /api/*   → 127.0.0.1:8040 (container)
                                          │
                                          ├─ (já existe) nginx vhost keynoteaws → autoscaler-ui :8000
                                          └─ container iris-bia-backend (uvicorn :8040)
                                               ├─► Redis Cloud PRO novo (cub-grade-education-70903:18540, PRIVADO)
                                               ├─► Context Surfaces / Agent Memory / LangCache (SaaS)
                                               └─► OpenAI
```

Realidade da caixa (recon 22/06): Ubuntu 24.04, sudo sem senha, Docker 28, **nginx+certbot já
instalados** (vhost `keynoteaws` → autoscaler), :8040 livre, SEM uv. O Redis novo é **privado**:
o laptop NÃO o alcança (timeout), o bastion SIM (PING PONG ok). Por isso o STEP 0 roda NO BASTION.

---

## O que ainda preciso de você
1. **Chaves SaaS** pra montar o `.env` (decisão: reusar as de dev vs dedicadas). Ver "Decisão de chaves".
2. **DNS** `irisbia.platformengineer.io` → `56.124.109.24` (antes do certbot).
3. **Senha do basic_auth** (eu gero o hash com openssl).
4. **OPENAI_API_KEY** (idealmente Project com teto de gasto).

Redis e bastion eu já tenho e testei.

---

## STEP 0 — de-risk NO BASTION (o de-risk que importa)
O Redis é privado, então cunhar a surface + carregar dados roda no bastion (que o alcança). É aqui
que se confirma o ÚNICO risco real: **a Context Surface consegue alcançar esse Redis privado?**
(Ela conecta a partir da nuvem da Redis, managed-side.)

```bash
# no bastion: ubuntu@56.124.109.24
# 1. uv (o Makefile usa uv; não vem no host)
curl -LsSf https://astral.sh/uv/install.sh | sh && . $HOME/.local/bin/env

# 2. código em /opt/iris-bia/code  (a etapa de "ship" do scripts/deploy_iris_bia.sh já faz isso)
# 3. /opt/iris-bia/.env preenchido (a partir de deploy/irisbia/.env.example.prod):
#      REDIS_HOST=cub-grade-education-70903.db.redis.io  REDIS_PORT=18540  REDIS_SSL=false
#      REDIS_PASSWORD=<a do redis://...>  ; CTX_SURFACE_ID e MCP_AGENT_KEY EM BRANCO
#      CTX_ADMIN_KEY + MEMORY_* + LANGCACHE_* + OPENAI_API_KEY (ver Decisão de chaves)

# 4. cunhar a surface + carregar dados no Redis novo
cd /opt/iris-bia/code && cp /opt/iris-bia/.env .env
make setup DOMAIN=bradesco_bia
cp .env /opt/iris-bia/.env       # .env agora tem CTX_SURFACE_ID + MCP_AGENT_KEY frescos
```
CONFIRME: `setup_surface` não falhou (= a surface alcançou o Redis privado, DE-RISK PASSOU), os
dados carregaram, e um chat de teste responde. Se `setup_surface` falhar por não alcançar o Redis,
é aqui que aparece (barato), e a saída é liberar o endpoint público do Redis (com allowlist) pra
surface, em vez de PrivateLink-only.

---

## Setup do bastion (uma vez só) — nginx, NÃO Caddy
A caixa já tem nginx + certbot. NÃO instalar Caddy (conflito em 80/443). Adicionar um vhost:

```bash
# vhost irisbia (DNS já apontando pro EIP)
sudo cp /opt/iris-bia/code/deploy/irisbia/nginx-irisbia.conf \
        /etc/nginx/sites-available/irisbia.platformengineer.io
sudo ln -s /etc/nginx/sites-available/irisbia.platformengineer.io /etc/nginx/sites-enabled/

# cert (certbot já instalado; mesmo padrão do keynoteaws)
sudo certbot certonly --nginx -d irisbia.platformengineer.io

# basic_auth sem apache2-utils (usa openssl, que já existe)
printf "iris:$(openssl passwd -apr1 'SUA_SENHA')\n" | sudo tee /etc/nginx/.htpasswd-irisbia

sudo nginx -t && sudo systemctl reload nginx
```
SG da EC2: 80/443 já abertos (nginx). Allowlist do Redis Cloud novo travado no EIP do bastion.

`.env` no bastion (chmod 600):
```bash
scp -i ~/Downloads/gabs-itau-sa-east-1.pem deploy/irisbia/.env.example.prod ubuntu@56.124.109.24:/tmp/.env
ssh -i ~/Downloads/gabs-itau-sa-east-1.pem ubuntu@56.124.109.24 \
  'sudo mkdir -p /opt/iris-bia && sudo mv /tmp/.env /opt/iris-bia/.env && sudo chmod 600 /opt/iris-bia/.env'
# preencher os valores via ssh (vi/nano) antes do STEP 0
```

---

## Deploy (toda vez que atualizar)
```bash
EC2_HOST=ubuntu@56.124.109.24 SSH_KEY=~/Downloads/gabs-itau-sa-east-1.pem bash scripts/deploy_iris_bia.sh
```
Faz build do front, manda dist + código pra /opt/iris-bia, sobe o container `iris-bia-backend` e
espera o `/api/health`. O nginx (vhost irisbia) já fronta com TLS + basic_auth.

---

## Decisão de chaves (pra montar o .env)
- **Surface (Context Surfaces):** reusa o `CTX_ADMIN_KEY` de dev (é account-level); o `make setup`
  cunha uma surface NOVA amarrada ao Redis novo. Isolamento garantido (surface é por-DB). ✓
- **Agent Memory:** reusa store de dev com um **namespace distinto** (ex: `bradesco-bia-irisbia`)
  pra não colidir com o `bradesco-bia-demo` local. `DEMO_LTM_PERSIST=false` no público.
- **LangCache:** seedar a cache FAZ flush dela. Pra não derrubar o cache local, use uma **cache
  nova dedicada** OU pule o seed de langcache no STEP 0 (LangCache falha graciosamente = cache miss).
- **OpenAI:** reusa a key de dev pra subir; troque por uma de Project com teto de gasto HARD antes
  de publicar de verdade.

---

## Checklist de segurança (demo público com LLM atrás)
- [ ] OpenAI: Project próprio + teto HARD no nível da ORG (budget de projeto é soft, não barra).
- [ ] basic_auth no nginx ativo (`.htpasswd-irisbia`, credencial só pra plateia).
- [ ] `GUARDRAIL_ENABLED=true`, starters não bloqueados (`Me conta uma piada` => Blocked).
- [ ] `DEMO_LTM_PERSIST=false`.
- [ ] `/opt/iris-bia/.env` chmod 600; segredos só no backend (SPA chama same-origin `/api`).
- [ ] Redis allowlist travado no EIP do bastion; backend só em 127.0.0.1:8040.

## Reset / re-seed (sem rebuild)
```bash
ssh -i ~/Downloads/gabs-itau-sa-east-1.pem ubuntu@56.124.109.24 \
  'cd /opt/iris-bia/code && sudo docker compose -f deploy/irisbia/docker-compose.prod.yml exec backend bash scripts/reset_bradesco_light.sh'
```
Datas do seed são relativas (sempre frescas). Easter egg da Copa é datado (vale até 19/07/2026).
