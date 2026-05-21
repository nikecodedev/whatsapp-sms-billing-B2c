# QUESH — Railway Deployment Guide

QUESH runs as **5 services inside one Railway project**:

| Service        | Type            | Source            |
|----------------|-----------------|-------------------|
| PostgreSQL     | Railway managed | 1-click add       |
| Redis          | Railway managed | 1-click add       |
| Backend (API)  | Web service     | this repo `/backend`  |
| Worker + Beat  | Background      | this repo `/backend`  |
| Frontend       | Static site     | this repo `/frontend` |

> The `railway.json` config-as-code file is intentionally **not** used:
> the backend web and worker services share the `/backend` directory but
> need different start commands, and a single config file would force the
> same command on both. Start commands are set per-service in the UI below.

---

## 1. Project + databases

1. Sign in at **railway.app** (GitHub login recommended).
2. **New Project**.
3. `+ New` → **Database** → **Add PostgreSQL**.
4. `+ New` → **Database** → **Add Redis**.

---

## 2. Backend service (FastAPI)

1. `+ New` → **GitHub Repo** → `nikecodedev/whatsapp-sms-billing-B2c`.
2. Service **Settings**:
   - **Root Directory**: `backend`
   - **Start Command**:
     ```
     alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
3. **Settings → Networking → Generate Domain**. Copy the URL — this is
   `BACKEND_URL` (e.g. `https://quesh-backend.up.railway.app`).
4. Add the variables from the **Environment Variables** section below.

`alembic upgrade head` runs on every boot and creates/updates all tables
(it is idempotent — does nothing when already up to date).

---

## 3. Worker + Beat service (Celery)

1. `+ New` → **GitHub Repo** → the **same** repo.
2. Service **Settings**:
   - **Root Directory**: `backend`
   - **Start Command**:
     ```
     celery -A celery_app worker --beat --loglevel=info
     ```
3. No domain needed (background service).
4. Add the **same** environment variables as the backend.

---

## 4. Frontend service (React dashboard)

1. `+ New` → **GitHub Repo** → the **same** repo.
2. Service **Settings**:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: `npx serve -s dist -l $PORT`
3. **Generate Domain** — this is the URL opened in a browser.
4. Variables:
   - `VITE_TENANT_ID` — a tenant UUID (create one: `POST {BACKEND_URL}/api/v1/tenants/`)
   - `VITE_API_URL` — the `BACKEND_URL` from step 2

---

## 5. Post-deploy wiring

1. On the **backend** and **worker** services, set `PUBLIC_BASE_URL`
   and `APP_BASE_URL` to `BACKEND_URL`.
2. On the **backend**, set `CORS_ORIGINS` to the frontend domain.
3. In the **Asaas** dashboard, register the webhook:
   `{BACKEND_URL}/webhooks/asaas`
4. Twilio voice webhooks need no manual setup — they are built from
   `PUBLIC_BASE_URL` automatically.

---

## Environment variables (backend + worker services)

```
APP_NAME              QUESH
DEBUG                 false
SECRET_KEY            <long random string>
APP_BASE_URL          <BACKEND_URL>
PUBLIC_BASE_URL       <BACKEND_URL>
CORS_ORIGINS          <FRONTEND_URL>

DATABASE_URL          postgresql+asyncpg://...   (see note)
DATABASE_URL_SYNC     ${{Postgres.DATABASE_URL}}
REDIS_URL             ${{Redis.REDIS_URL}}

ANTHROPIC_API_KEY     sk-ant-...
CLAUDE_MODEL          claude-sonnet-4-6

ZAPI_INSTANCE_ID      <z-api instance id>
ZAPI_TOKEN            <z-api instance token>
ZAPI_CLIENT_TOKEN     <z-api client token>
ZAPI_BASE_URL         https://api.z-api.io

TWILIO_ACCOUNT_SID    <twilio sid>
TWILIO_AUTH_TOKEN     <twilio auth token>
TWILIO_FROM_NUMBER    <twilio number>
TWILIO_VOICE_LANGUAGE pt-BR
TWILIO_VOICE_NAME     Polly.Camila-Neural

ASAAS_API_KEY         <asaas key>
ASAAS_BASE_URL        https://api.asaas.com/v3
```

**`DATABASE_URL` note:** Railway's Postgres exposes a URL starting with
`postgresql://`. The QUESH async engine needs the `postgresql+asyncpg://`
prefix — copy Railway's Postgres URL into `DATABASE_URL` and change the
prefix manually. `DATABASE_URL_SYNC` uses Railway's value unchanged.

---

## Notes

- **Twilio trial**: while the Twilio account is in trial, SMS and voice
  reach only *verified* numbers — regardless of deployment. Deploying does
  not lift that limit; the account upgrade does.
- **Cost**: 5 services will consume Railway's free trial credit fairly
  quickly; budget for the Hobby plan (~USD 5/month).
- **Secrets**: `.env` files are gitignored and never deployed. Every
  variable must be entered into the Railway dashboard by hand.
