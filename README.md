# VISORA — Gestão Inteligente de Estacionamentos com ALPR

O VISORA é uma plataforma SaaS multi-tenant para gestão automatizada de estacionamentos privados, integrando visão computacional de ponta (YOLOv8 + CRNN + PyTorch), backend REST assíncrono (FastAPI + PostgreSQL) e interface web reativa moderna (Angular 17 SPA com Signals).

## Execução  com Docker

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env

# 2. Subir a stack completa (Postgres + Backend + Frontend/Nginx)
docker compose up --build -d

# 3. Criar o primeiro administrador SaaS
docker compose exec backend python scripts/create_saas_admin.py --email admin@parkingsaas.com --nome "Super Admin"
```

Acesse:
- **Aplicação Web:** [http://localhost:4200](http://localhost:4200)
- **API Swagger:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

