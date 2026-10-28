# Plataforma SaaS de Gestão de Estacionamentos com ALPR

Sistema integrado para gestão de estacionamentos privados com Reconhecimento Automático de Placas de Veículos (ALPR), controle de permanência, bilhetagem automatizada, planos/assinaturas e arquitetura multi-tenant.

## 🚀 Tecnologias

- **Visão Computacional**: Python 3.12, OpenCV, YOLO (Ultralytics), CRNN (PyTorch com decodificação CTC), NumPy, PyYAML.
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Alembic, PostgreSQL, JWT Authentication.
- **Frontend**: Angular, TypeScript, SCSS.
- **Infraestrutura**: Docker & Docker Compose, Pytest.
- **Hardware**: Compatível com macOS Apple Silicon (MPS) e CPU/CUDA.

---

## 📁 Estrutura do Repositório

```text
parking-saas/
├── computer-vision/        # Módulo autônomo de processamento de imagens e vídeos ALPR
│   ├── config/             # Configurações de modelos, pré-processamento e thresholds (YAML)
│   ├── data/
│   │   ├── input/          # Arquivos de vídeo e imagens de entrada
│   │   └── output/         # Vídeos anotados, CSVs e JSONs de métricas
│   ├── models/
│   │   └── weights/        # Pesos dos modelos treinados (YOLO e CRNN)
│   ├── src/
│   │   └── alpr/           # Pipeline de visão computacional
│   └── tests/              # Testes automatizados do módulo de visão
│
├── backend/                # API REST SaaS Multi-tenant
│   ├── app/
│   │   ├── api/            # Rotas e controladores REST
│   │   ├── core/           # Configurações, segurança e tokens JWT
│   │   ├── models/         # Entidades ORM (SQLAlchemy)
│   │   ├── schemas/        # Esquemas de validação e serialização (Pydantic)
│   │   └── services/       # Regras de negócio (tarifação, permanência, assinaturas)
│   ├── alembic/            # Migrações versionadas do banco de dados
│   └── tests/              # Testes unitários e de integração da API
│
├── frontend/               # Interface Web Administrativa e Portal do Cliente (Angular)
├── infrastructure/         # Definições de infraestrutura, Dockerfiles e scripts
├── docs/                   # Documentação de arquitetura e modelo de banco de dados
├── docker-compose.yml      # Orquestração de serviços para desenvolvimento e produção
├── pytest.ini              # Configuração global de testes automatizados
└── .env.example            # Exemplo de variáveis de ambiente
```

---

## 🛠️ Como Iniciar o Ambiente Local

### 1. Pré-requisitos
- Python 3.12
- Git
- Docker & Docker Compose (para banco de dados PostgreSQL)

### 2. Ativar Ambiente Virtual
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r computer-vision/requirements.txt
pip install -r backend/requirements.txt
```

### 3. Executar Testes de Validação do Ambiente
```bash
pytest computer-vision/tests/
```

### 4. Configurações
Copie o arquivo de exemplo de ambiente:
```bash
cp .env.example .env
```
Ajuste os parâmetros conforme necessário em `.env` e `computer-vision/config/alpr_config.yaml`.
