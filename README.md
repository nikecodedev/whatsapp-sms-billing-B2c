# QUESH — Plataforma de Cobrança B2C com IA

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose

---

## Setup Local

### 1. Suba PostgreSQL e Redis

```bash
docker-compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Copie e preencha o .env
cp .env.example .env
# edite .env com suas credenciais

# Crie as tabelas via Alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Inicie a API
uvicorn main:app --reload --port 8000
```

### 3. Celery Worker + Beat (em terminais separados)

```bash
cd backend
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# edite VITE_TENANT_ID com o UUID do tenant criado

npm run dev
```

Acesse: http://localhost:5173

---

## Primeiros passos após subir

1. **Criar tenant** via `POST /api/v1/tenants`
2. Copie o `id` retornado para `VITE_TENANT_ID` no frontend
3. **Importar devedores** na tela de Devedores (Excel/CSV)
4. **Criar campanha** na tela de Campanhas
5. **Lançar campanha** — o Claude decide canal, tom, horário e gera mensagens automaticamente
6. Contatos são enviados a cada 5 min pelo Celery Beat

---

## Estrutura

```
/backend
  /ai            — Motor de decisão Claude
  /api/routes    — Endpoints FastAPI
  /campaigns     — Gerenciador de campanhas + compliance CDC
  /channels      — WhatsApp (Z-API) + SMS (Twilio)
  /core          — Config, banco de dados
  /importers     — Importador Excel/CSV
  /models        — SQLAlchemy models + Pydantic schemas
  /payments      — Asaas (Pix/Boleto) + encurtador de URL
  /workers       — Tarefas Celery
/frontend
  /src
    /api         — Clientes HTTP
    /components  — Componentes reutilizáveis
    /pages       — Dashboard, Campanhas, Devedores
```

---

## Webhook Asaas

Configure no painel Asaas:
```
POST https://seu-dominio.com/webhooks/asaas
```

---

## Compliance CDC

- Nenhum contato antes das 08:00 ou após as 21:00 (horário de Brasília)
- Máximo 1 contato por dia por devedor
- Intervalo mínimo configurável entre tentativas (padrão: 48h)
- Linguagem não vexatória controlada pelo prompt do Claude
# whatsapp-sms-billing-B2c
