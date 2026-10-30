# Parking SaaS com Reconhecimento Automático de Placas (ALPR)

Plataforma SaaS multi-tenant para gestão automatizada de estacionamentos privados, integrando visão computacional de ponta (YOLOv8 + CRNN + PyTorch), backend REST assíncrono (FastAPI + PostgreSQL) e interface web reativa moderna (Angular 17 SPA com Signals).

---

## 🚀 Principais Funcionalidades

1. **Visão Computacional e ALPR Autônomo:**
   - Detecção de veículos (carros, caminhões, ônibus) com YOLOv8.
   - Detecção e recorte especializado de placas veiculares brasileiras.
   - Normalização, equalização adaptativa de contraste (CLAHE) e redução de ruído.
   - Reconhecimento de caracteres com rede neural convolucional e recorrente (**CRNN**) e decodificação gulosa **CTC**.
   - Validação estrita dos padrões **Mercosul (ABC1D23)** e **Antigo (ABC1234)** via regex regulatório sem substituição arbitrária de caracteres.
   - Rastreamento temporal de veículos por centroide/IoU com cooldown anti-duplicidade.
   - Suporte a leitura de arquivos de vídeo locais e streams contínuos de rede via **RTSP/IP**.
   - Calculadora quantitativa de métricas (**CER - Character Error Rate**, precisão, revocação e acurácia).

2. **Backend Multi-Tenant & Regras de Negócio (FastAPI):**
   - Isolamento estrito de dados por estacionamento (`estacionamento_id`).
   - Autenticação JWT com controle de acesso baseado em papéis (**RBAC**): `SAAS_ADMIN`, `ESTACIONAMENTO_ADMIN`, `CLIENTE`.
   - Política segura de criação de contas e fluxo de recuperação de senha com tokens de uso único e notificação segura (sem exposição de existência de conta e sem vazamento em logs).
   - Cadastro de clientes com exigência de pelo menos 1 veículo inicial e unicidade de placa por estacionamento.
   - Tarifação horária avulsa (primeira hora, horas adicionais, diária, tolerância) e planos recorrentes para mensalistas.
   - Bilhetagem automática na saída com tratamento de inconsistências (saída sem entrada registrada).
   - Trilha completa de auditoria em operações cadastrais e correções manuais.

3. **Portal do Cliente:**
   - Interface segura e isolada para clientes do estacionamento.
   - Minimização de dados (**LGPD**) com mascaramento de documento.
   - Visualização em tempo real de permanência dos veículos no pátio.
   - Consulta de histórico de passagens, assinaturas de planos e status de cobranças/pagamentos.

4. **Painel Administrativo & Central ALPR (Angular 17):**
   - Dashboard com KPIs executivos em tempo real e lista das últimas movimentações.
   - Gestão de clientes, frotas, tarifas vigentes e planos.
   - Histórico com modal de correção manual com justificativa obrigatória para auditoria.
   - Painel financeiro de cobranças e registro de pagamentos (PIX, Dinheiro, Cartões, Boleto).
   - Central ALPR para cadastro de câmeras (entrada, saída, bidirecional), teste de detecção em tempo real e ingestão de vídeos com telemetria e gráficos de métricas.

---

## 🛠️ Tecnologias Utilizadas

- **Visão Computacional:** Python 3.12, OpenCV, PyTorch, Ultralytics YOLOv8, NumPy, PyYAML.
- **Backend:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PostgreSQL, python-jose, bcrypt.
- **Frontend:** Angular 17 (Standalone Components, Signals), TypeScript, SCSS, RxJS.
- **DevOps & Infraestrutura:** Docker, Docker Compose, Nginx, Pytest.

---

## 📦 Execução Rápida com Docker

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
- **API Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testes Automatizados

A suíte conta com **98 testes automatizados** cobrindo todos os módulos:

```bash
# Executar a suíte de testes
source .venv/bin/activate
pytest -v
```

Para mais detalhes de arquitetura e modelo relacional, consulte a pasta [docs/](file:///Users/tvitoriaferreira/Documents/alpr_project/docs).
