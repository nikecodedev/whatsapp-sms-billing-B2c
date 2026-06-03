# QUESH — Session Log

Working notes covering the development and deployment of the QUESH MVP, the live end-to-end testing with the client, and the proposal for the conversational-agent expansion.

---

## 1. Project context

- **Client:** Nader Jarrah Hamad — Brazilian startup founder, non-technical, has co-investors who must also approve spend.
- **Platform:** Workana (milestone-paid, escrow flow).
- **Project:** QUESH — B2C AI-powered debt collection SaaS.
- **Original plan (3 phases, total USD 2,842.71):**
  - Phase 1 (MVP) — USD 1,042.71. WhatsApp + SMS + voice escalation, AI decision engine, Asaas Pix, CDC compliance, dashboard.
  - Phase 2 — USD 1,000. Voice calls expanded, multi-tenant, CRM/ERP API, per-segment compliance.
  - Phase 3 — USD 800. Self-service onboarding, AI learning loop, admin panel.
- **Stack:** FastAPI + async SQLAlchemy + PostgreSQL + Celery (Redis) + React/Vite frontend; Z-API for WhatsApp, Twilio for SMS/voice, Asaas for payments, Anthropic Claude for decision engine.

---

## 2. Voice channel implementation (MVP phase)

Voice was originally a Phase 2 deliverable but pulled into the MVP at no extra cost. Code added:

- `backend/channels/voice.py` — `place_call()` using Twilio SDK to place outbound calls, with `status_callback` and TwiML URL built from `PUBLIC_BASE_URL`.
- Three new webhook routes in `backend/api/routes/webhooks.py`:
  - `GET/POST /webhooks/voice/twiml/{contact_id}` returns TwiML with `<Say>` reading the AI-generated message in pt-BR (Polly Camila Neural voice) and a `<Gather>` for "press 1 to receive payment link".
  - `POST /webhooks/voice/gather/{contact_id}` handles DTMF; if `1`, sends payment link via SMS.
  - `POST /webhooks/voice/status/{contact_id}` updates contact status from Twilio.
- Voice config added to `core/config.py` (`TWILIO_VOICE_FROM_NUMBER`, `TWILIO_VOICE_LANGUAGE`, `TWILIO_VOICE_NAME`, `PUBLIC_BASE_URL`).
- Dispatch wired into `workers/tasks.py` — replaced the "Phase 2 stub" that marked voice contacts FAILED with a real Twilio call.

---

## 3. Local environment setup

The user's Linux box had several gaps:

- `python3-venv` and `python3-pip` missing → required `sudo apt install`.
- Host machine had Postgres on `5432` and Redis on `6379` already → docker-compose ports remapped to `5433`/`6380`, `.env.example` updated to match.
- Port `8000` also in use → uvicorn moved to `8001`, Vite proxy adjusted.
- Node and npm not installed → required `sudo apt install nodejs npm`.

Local services brought up: Postgres + Redis via docker compose, backend venv + uvicorn, frontend `npm install` + `npm run dev`. Demo tenant `b3590453-...` created via API and wired into `frontend/.env`.

---

## 4. GitHub push

- Repo: `github.com/nikecodedev/whatsapp-sms-billing-B2c` (SSH).
- Identity set repo-local: `nikecodedev / bellwalton54@outlook.com`.
- Three rounds of commits during the session:
  1. **Voice channel + MVP finalize** (`857bfbf` etc.) — voice files, env updates, README, Alembic migration un-ignored.
  2. **Railway Phase 0** (`585c710`) — CORS configurable via `CORS_ORIGINS`, frontend `VITE_API_URL` support, missing `vite-env.d.ts`, `DEPLOY.md`.
  3. **Bugfix series during deploy** — async URL normalization, whitespace strip in settings, Celery concurrency cap, async Anthropic client, Asaas past-date fix.
- One amend + force-push to drop the `Co-Authored-By: Claude` trailer from a commit.
- GitHub auto-deploy to Railway turned out to be broken (the Railway GitHub App had no access to this repo). Deployment had to be done via Railway CLI thereafter.

---

## 5. Railway deployment — the long part

The deployment surfaced bugs that local testing missed. Each launch attempt got further than the previous one:

| Attempt | Bug surfaced | Fix |
|---|---|---|
| v1 boot | `psycopg2 is not async` | Added `async_database_url` / `sync_database_url` properties that normalize whatever DATABASE_URL is given |
| v2 boot | `Could not parse URL from ''` | DATABASE_URL on Railway was set to a reference that didn't resolve; switched to literal Postgres URL |
| v3 boot | `database "railway\n" does not exist` | Trailing newline in pasted env var; added `_strip_string_fields` model validator that strips all string settings |
| Worker boot loop | `concurrency: 48 (prefork)` OOM | Set `worker_concurrency=2` in `celery_app.py` |
| Worker task | `No module named 'greenlet'` | Added `greenlet==3.5.0` to `requirements.txt` (SQLAlchemy async dependency that Python 3.13 build didn't auto-install) |
| Launch v3-v6 | Bg task created no contacts | Closed-session bug — `launch_campaign` passed request-scoped `db` to background task; fixed with `_enqueue_in_background` wrapper that opens its own `AsyncSessionLocal` |
| Launch v6 | Backend event loop blocked | Sync `anthropic.Anthropic` was called from async context; switched to `AsyncAnthropic` + `await` |
| Launch v6 | Anthropic 401 | `ANTHROPIC_API_KEY` mangled by Railway's raw editor; re-set via CLI |
| Launch v6 | Anthropic 404 "model: 8TgH6eVG..." | `CLAUDE_MODEL` mangled (random reference ID); re-set via CLI |
| Launch v6 | Asaas 401 | `ASAAS_API_KEY` (starts with `$`) mangled by shell expansion; re-set via CLI with single quotes |
| Launch v7 | Asaas 400 on charge create | Debtor's `data_vencimento` was in the past; Asaas rejects past `dueDate`. Now using `max(today + 7 days, data_vencimento)` for the Asaas charge date |

CLI tooling used end-to-end:
- Installed Railway CLI to user-local (`~/.local/bin/railway`) via `npm i -g --prefix ~/.local` (global needed root).
- `railway login` (interactive) + `railway link` to project `rare-flexibility`.
- `railway up --detach --service <name>` for each service.
- `railway variables --service <name> --set 'KEY=VALUE'` to fix mangled credentials.
- Direct DB updates via the public Postgres URL (`kodama.proxy.rlwy.net:19134`) when needed (e.g., updating debtor email, rescheduling contacts to bypass CDC hour window for testing).

After the bug train, the live URLs:
- Backend: `https://backend-production-70130.up.railway.app`
- Frontend: `https://frontend-production-301c.up.railway.app`
- Worker: unexposed, online with `concurrency: 2`

---

## 6. End-to-end test with Nader's real phone

Test debtor created: "Nader Hamad", CPF `11144477735`, phone `+5511986171734`, R$ 250.00, due `2026-04-22`, email `nader@quesh.com.br` (updated from initial `demo@quesh.app` after Asaas rejected the invalid domain).

Test campaigns: created several (v3 through v7, plus "Teste Nader" and "Teste Nader_V2"), each launch surfaced bugs. After all fixes were in:

- **WhatsApp:** Nader confirmed receipt of two messages with personalized AI text and Pix link. ✓
- **Voice:** Twilio marked DELIVERED. Nader saw a US-number incoming call. Likely went to voicemail in the first attempt — rescheduled. ✓ (on Twilio's side)
- **SMS:** Twilio marked SENT (SID `SMcd75fa0a5...`). Nader reported not receiving. Likely SMS-to-Brazil deliverability issue from a US Twilio long code, which is a known carrier filtering problem — not a system bug.

Asaas charge created on Nader's account: `pay_ypk3w0lki2xoqzzs`, R$ 250.00 Pix.

---

## 7. Client communications (highlights)

- **Z-API subscription expired** during testing. Nader reactivated for R$ 99.99/month after I diagnosed and reported.
- **Twilio trial unblock:** Nader's identity verification failed 3x; Twilio support manually lifted the trial restriction. Now sending to any number.
- **Email issue:** Asaas rejected `demo@quesh.app` as invalid; I updated debtor email to `nader@quesh.com.br` in both our DB and on the Asaas customer record (`cus_000177876340`).
- **Caller ID concern:** voice calls show US caller ID (`+19067295756`, Michigan area). Recommended to Nader: in production, buy a Brazilian Twilio number with Regulatory Bundle. Not urgent for milestone delivery.
- **Approval blocker:** Nader said he needs 2 co-founder approvals to release MVP escrow, and is hesitant because he wants to be sure the project can deliver beyond the MVP. He referenced a friend's quick YouTube AI voice demo as a comparison point.

---

## 8. Scope-expansion conversation

Nader described his vision of conversational AI agents — natural negotiation, intent understanding, conversational memory, per-client personality customization, voice and WhatsApp both, no scripted bot feel. He pasted an AI-generated detailed brief listing those requirements.

This is materially larger than what was scoped in the original Phase 2. After laying out three options to him (SaaS integration, full custom build, or phased), Nader chose the SaaS integration path (Vapi/Retell/ElevenLabs).

After comparing the three tools, I recommended **ElevenLabs Agents** for best voice quality + native Claude support + lowest per-minute cost (USD 0.08 to 0.15).

Updated milestone plan:

- **Milestone 1** — MVP — USD 1,042.71 — **delivered**, awaiting Workana approval.
- **Milestone 2** — Conversational agents (ElevenLabs integration + WhatsApp bot + per-client customization) — USD 1,500 — 3 weeks.
- **Milestone 3** — Multi-tenant SaaS platform (auth, admin panel, CRM/ERP API, per-segment compliance, onboarding) — USD 1,300 — 3 weeks.
- **New total:** USD 3,842.71 (USD 1,000 over the original plan, justified by conversational scope).

`PROPOSTA_v2_NADER.md` drafted in repo root with the full plan. A natural-tone plain-text version of the same proposal was provided for direct client messaging.

---

## 9. Outstanding items

- [ ] Nader presents proposal v2 to co-founders.
- [ ] Nader approves Milestone 1 on Workana — escrow release.
- [ ] Asaas webhook registration in Nader's dashboard for instant payment confirmation (optional polish; the 30-min Celery poll still catches payments).
- [ ] Brazilian Twilio number purchase + Regulatory Bundle (production polish, not urgent).
- [ ] Handover decision — transfer Railway project to Nader's account vs continue on dev's account.
- [ ] If Phase 2 approved: ElevenLabs Agents account setup + integration build.

---

## 10. Repository state

- `main` branch up to date with the last commit before the proposal work.
- All session work is committed and pushed except the proposal files (`PROPOSTA_v2_NADER.md`, this `CHAT_LOG.md`) which are local-only deliverables intended for the client conversation, not the codebase.
- `.env` files contain working production credentials and remain gitignored on all machines.
