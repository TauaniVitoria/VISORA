# Manual de Implantação e Operação (Deploy & Runbook) — VISORA

Este documento descreve os procedimentos completos para executar, testar e implantar a plataforma **VISORA** em ambientes locais e de produção.

---

## 1. Requisitos do Sistema

### 1.1. Desenvolvimento Local
- **macOS** (Apple Silicon M1/M2/M3 suportado via PyTorch MPS) ou **Linux x86_64 / arm64**.
- **Python 3.12+**.
- **Node.js 20+** e **npm 10+**.
- **Git**.

### 1.2. Ambiente Conteinerizado (Recomendado para Produção)
- **Docker Engine 24.0+** e **Docker Compose v2+**.
- Mínimo de 4 GB de memória RAM livre (recomendado 8 GB para inferência de visão computacional).

---

## 2. Execução Rápida com Docker Compose

A plataforma inteira (Banco PostgreSQL, Backend FastAPI + ALPR Engine e Frontend Angular SPA servido por Nginx) pode ser instanciada com um único comando:

```bash
# 1. Copiar variáveis de ambiente de exemplo
cp .env.example .env

# 2. Construir e subir todos os contêineres em segundo plano
docker compose up --build -d

# 3. Verificar o status dos serviços
docker compose ps
```

### URLs de Acesso dos Serviços:
- **Frontend SPA (Portal do Cliente & Painel Administrativo):** [http://localhost:4200](http://localhost:4200)
- **Documentação Interativa da API (Swagger UI):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **OpenAPI Schema (JSON):** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)
- **PostgreSQL Database:** `localhost:5432`

---

## 3. Criação do Primeiro Usuário Administrador (Bootstrap)

Como o endpoint `POST /api/v1/auth/register` exige credenciais administrativas com RBAC para evitar escalada de privilégios, o primeiro administrador SaaS deve ser inicializado pelo script de bootstrap:

```bash
# Execução no contêiner backend:
docker compose exec backend python scripts/create_saas_admin.py --email admin@parkingsaas.com --nome "Super Admin"

# Ou localmente com o ambiente virtual ativo:
source .venv/bin/activate
cd backend
SAAS_ADMIN_PASSWORD="SuaSenhaSuperSegura123" python scripts/create_saas_admin.py --email admin@parkingsaas.com --nome "Super Admin"
```

---

## 4. Execução Local para Desenvolvimento

### 4.1. Backend & ALPR
```bash
# 1. Ativar venv
source .venv/bin/activate

# 2. Executar migrações do banco
cd backend
alembic upgrade head

# 3. Iniciar o servidor com auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2. Frontend Angular 17
```bash
cd frontend
npm install
npm start
# Acessar http://localhost:4200
```

---

## 5. Execução dos Testes Automatizados

A suíte completa possui 98 testes unitários e de integração cobrindo regras de negócio, visão computacional, isolamento multi-tenant e portal do cliente:

```bash
source .venv/bin/activate
pytest -v
```

---

## 6. Comandos Operacionais Úteis do Docker

- **Acompanhar logs unificados:** `docker compose logs -f`
- **Acompanhar logs do backend:** `docker compose logs -f backend`
- **Parar todos os contêineres:** `docker compose down`
- **Parar e limpar volumes persistentes:** `docker compose down -v`

