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
  /channels      — WhatsApp (Z-API) + SMS (Twilio) + Voz (Twilio Voice)
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

## Ligações de voz (Twilio Voice)

A escalação WhatsApp → SMS → Voz usa **Twilio Voice** para a última etapa.
O fluxo:

1. Celery dispara `place_call(phone, contact_id)` → Twilio cria a chamada.
2. Twilio busca TwiML em `GET /webhooks/voice/twiml/{contact_id}` — o backend retorna `<Say>` com a mensagem gerada pela Claude usando a voz `Polly.Camila-Neural` (pt-BR).
3. `<Gather>` oferece: **pressione 1** para receber o link de pagamento via SMS.
4. `POST /webhooks/voice/status/{contact_id}` atualiza o `Contact` para `delivered` / `failed`.

**Requisitos:**
- Número Twilio com capacidade de **Voice** habilitada (~USD 1/mês).
- `PUBLIC_BASE_URL` apontando para uma URL acessível pela internet pública. Em dev local, use `ngrok http 8000` e cole a URL `https://...` no `.env`.
- Defina `TWILIO_VOICE_FROM_NUMBER` se quiser separar número de SMS e voz; caso contrário, usa `TWILIO_FROM_NUMBER`.

---

## Compliance CDC

- Nenhum contato antes das 08:00 ou após as 21:00 (horário de Brasília)
- Máximo 1 contato por dia por devedor
- Intervalo mínimo configurável entre tentativas (padrão: 48h)
- Linguagem não vexatória controlada pelo prompt do Claude
# whatsapp-sms-billing-B2c
