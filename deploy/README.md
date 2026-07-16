# Itaú Assist — deploy em produção (gabs-iris-bank)

Stack pra rodar o demo em `irisbank.platformengineer.io` sob HTTPS via Caddy do host.

## Topologia

```
   Internet (HTTPS)
        │
        ▼
  Caddy do HOST  ─── irisbank.platformengineer.io ───┐
        │                                            │
        │  /api/*  → 127.0.0.1:8040                  │
        │  /*      → /opt/iris-bank/dist/  (estático)│
        ▼                                            │
  Docker container "iris-bank-backend"               │
  (FastAPI uvicorn na porta 8040)                    │
        │                                            │
        ▼                                            │
  Redis Cloud + Agent Memory + LangCache + OpenAI ◄──┘
  (todos externos, gerenciados — sem Redis local)
```

## Layout na VM (`/opt/iris-bank/`)

```
/opt/iris-bank/
├── .env                  # secrets (NÃO versionado)
├── dist/                 # frontend build (vite dist)
└── code/                 # repo rsync (backend, domains, scripts, deploy/)
    └── deploy/
        ├── backend/Dockerfile
        ├── docker-compose.prod.yml
        ├── Caddyfile.snippet
        └── .env.example.prod
```

## Setup inicial na VM (uma vez só)

```bash
# Na VM gabs-iris-bank
sudo -i
mkdir -p /opt/iris-bank/{dist,code}
chown -R gabriel_cerioni:gabriel_cerioni /opt/iris-bank
exit

# Volta pro user normal e prepara o .env
cp /tmp/.env.prod /opt/iris-bank/.env
chmod 600 /opt/iris-bank/.env

# Caddy snippet (adiciona ao Caddyfile)
sudo tee -a /etc/caddy/Caddyfile < /opt/iris-bank/code/deploy/Caddyfile.snippet
sudo systemctl reload caddy
```

## DNS

Adicione um `A record` no seu provedor DNS:
```
irisbank.platformengineer.io  A  <IP-da-VM-gabs-iris-bank>
```

A VM atual tem IP `34.136.162.94` (ephemeral — sobreviveu o stop/start mas pode mudar
em futuro restart). Pra evitar mudança, **reserve um IP estático** no GCP:

```
gcloud compute addresses create iris-bank-ip --region us-central1
gcloud compute instances delete-access-config gabs-iris-bank --zone us-central1-a
gcloud compute instances add-access-config gabs-iris-bank \
    --zone us-central1-a --address <ip-reservado>
```

## Deploy contínuo (do laptop)

```bash
# Da raiz do repo, no laptop
bash scripts/deploy_iris_bank.sh
```

O script:
1. Faz `npm run build` no frontend → `frontend/dist/`
2. Roda `generate_data.py` localmente pra gerar `output/itau_assist/*.jsonl`
3. rsync `frontend/dist/` → `gabs-iris-bank:/opt/iris-bank/dist/`
4. rsync código (backend, domains, scripts, deploy, pyproject.toml, uv.lock) → `gabs-iris-bank:/opt/iris-bank/code/`
5. SSH → `cd /opt/iris-bank/code && docker compose -f deploy/docker-compose.prod.yml up -d --build`
6. Aguarda healthcheck do backend e printa status

## Operações comuns na VM

```bash
# Logs do backend
docker compose -f /opt/iris-bank/code/deploy/docker-compose.prod.yml logs -f backend

# Restart só do backend
docker compose -f /opt/iris-bank/code/deploy/docker-compose.prod.yml restart backend

# Status do Caddy
sudo systemctl status caddy

# Tail do log da Caddy específico do irisbank
sudo tail -f /var/log/caddy/irisbank.log
```

## Reset / re-seed da demo

Se você precisar regenerar os dados no Redis Cloud durante a demo (sem refazer o build):

```bash
# No laptop, mantendo Redis Cloud apontado, roda local:
bash scripts/reset_itau_light.sh

# Ou na VM (entra no container):
docker compose -f /opt/iris-bank/code/deploy/docker-compose.prod.yml exec backend \
    bash scripts/reset_itau_light.sh
```

## Troubleshooting

| Sintoma | Causa | Fix |
|---|---|---|
| 502 no /api/* | container backend não respondeu / Caddy não alcança 127.0.0.1:8040 | `docker compose logs backend`; conferir se o `ports: 127.0.0.1:8040:8040` está mapeado |
| Certificado não emitiu | DNS ainda não propagou ou A record errado | `dig irisbank.platformengineer.io`; aguardar 5-10min; conferir Caddy logs `journalctl -u caddy` |
| 404 no path do frontend | dist vazio ou paths errados | `ls /opt/iris-bank/dist/` deve ter `index.html`, `assets/`, `RedisLogo.png`, `backgrounds/itau_assist/` |
| Memory API 400 ID inválido | namespace com underscore | `MEMORY_NAMESPACE=itau-assist-demo` (hyphen!) no .env |
| LangCache 400 attributes | cache não tem attributes configurados na UI | usar `attributes={}` (já está no seed) |
