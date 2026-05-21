"""
Webhook handlers:
  - POST /webhooks/asaas              — Asaas payment status updates
  - GET  /webhooks/voice/twiml/{id}   — TwiML Twilio fetches when a call connects
  - POST /webhooks/voice/status/{id}  — Twilio call-completion status callback
  - POST /webhooks/voice/gather/{id}  — DTMF result handler (caller pressed 1, etc.)
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.database import get_db
from models.payment import Payment, PaymentStatus
from models.contact import Contact, ContactStatus, Channel
from models.debtor import Debtor
from channels.sms import send_sms

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")

ASAAS_CONFIRMED = {"RECEIVED", "CONFIRMED"}


@router.post("/asaas")
async def asaas_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("event", "")
    charge_data = payload.get("payment", {})
    asaas_id = charge_data.get("id")

    if not asaas_id:
        return {"status": "ignored"}

    result = await db.execute(select(Payment).where(Payment.asaas_charge_id == asaas_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return {"status": "not_found"}

    if event in ("PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"):
        payment.status = PaymentStatus.CONFIRMED
        payment.paid_at = datetime.now(BRAZIL_TZ)
        if payment.contact_id:
            contact = await db.get(Contact, payment.contact_id)
            if contact:
                contact.status = ContactStatus.PAID

    elif event == "PAYMENT_OVERDUE":
        payment.status = PaymentStatus.OVERDUE

    elif event in ("PAYMENT_REFUNDED", "PAYMENT_DELETED"):
        payment.status = PaymentStatus.CANCELLED

    await db.commit()
    return {"status": "ok"}


# ── Twilio Voice ───────────────────────────────────────────────────────────

def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _strip_payment_link_for_speech(message: str) -> str:
    """The AI message contains a [PAYMENT_LINK] placeholder (or a real URL after
    rendering) that doesn't read well aloud. Replace with a spoken cue."""
    spoken_cue = "Para receber o link de pagamento por SMS, pressione 1 ao final desta mensagem."
    for token in ("[PAYMENT_LINK]", "[LINK]"):
        if token in message:
            return message.replace(token, "").strip()
    # If the message contains an http link, drop the trailing URL — we'll prompt via Gather.
    lines = [ln for ln in message.splitlines() if "http" not in ln.lower()]
    cleaned = "\n".join(lines).strip() or message
    return cleaned


@router.api_route("/voice/twiml/{contact_id}", methods=["GET", "POST"])
async def voice_twiml(contact_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return TwiML that Twilio plays when the call connects.
    Speaks the AI-generated message in pt-BR, then offers DTMF press-1 to
    receive the payment link via SMS."""
    contact = await db.get(Contact, contact_id)
    voice = settings.TWILIO_VOICE_NAME
    lang = settings.TWILIO_VOICE_LANGUAGE

    if not contact:
        body = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Say voice="{voice}" language="{lang}">'
            f"Não foi possível identificar este contato. Encerrando a chamada."
            f"</Say><Hangup/></Response>"
        )
        return Response(content=body, media_type="application/xml")

    spoken = _strip_payment_link_for_speech(contact.message_body or "")
    spoken_xml = _escape_xml(spoken) if spoken else "Olá, esta é uma ligação automática da QUESH."

    gather_action = f"{(settings.PUBLIC_BASE_URL or settings.APP_BASE_URL).rstrip('/')}/webhooks/voice/gather/{contact_id}"

    body = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response>'
        f'<Pause length="1"/>'
        f'<Say voice="{voice}" language="{lang}">{spoken_xml}</Say>'
        f'<Pause length="1"/>'
        f'<Gather numDigits="1" timeout="6" action="{gather_action}" method="POST">'
        f'<Say voice="{voice}" language="{lang}">'
        f'Para receber o link de pagamento por SMS agora, pressione 1. '
        f'Para encerrar, pressione qualquer outra tecla.'
        f'</Say>'
        f'</Gather>'
        f'<Say voice="{voice}" language="{lang}">Não recebemos sua resposta. Até logo.</Say>'
        f'<Hangup/>'
        f'</Response>'
    )
    return Response(content=body, media_type="application/xml")


@router.post("/voice/gather/{contact_id}")
async def voice_gather(
    contact_id: uuid.UUID,
    Digits: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """DTMF result. If caller pressed 1, send the payment link via SMS."""
    voice = settings.TWILIO_VOICE_NAME
    lang = settings.TWILIO_VOICE_LANGUAGE

    if Digits.strip() != "1":
        body = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Say voice="{voice}" language="{lang}">Obrigado. Até logo.</Say><Hangup/></Response>'
        )
        return Response(content=body, media_type="application/xml")

    contact = await db.get(Contact, contact_id)
    if not contact:
        body = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Say voice="{voice}" language="{lang}">Contato não encontrado.</Say><Hangup/></Response>'
        )
        return Response(content=body, media_type="application/xml")

    debtor = await db.get(Debtor, contact.debtor_id)

    # Find a pending payment for this debtor (most recent first)
    pay_result = await db.execute(
        select(Payment)
        .where(Payment.debtor_id == contact.debtor_id, Payment.status == PaymentStatus.PENDING)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    payment = pay_result.scalar_one_or_none()

    link = payment.short_url or payment.asaas_invoice_url if payment else None

    if debtor and link:
        sms_body = f"QUESH: seu link de pagamento — {link}"
        # send_sms is sync; safe to call from async since this is short-lived
        send_sms(debtor.telefone, sms_body)
        spoken = "Enviamos o link de pagamento por SMS. Obrigado e tenha um bom dia."
    else:
        spoken = "Não encontramos um pagamento pendente. Por favor, entre em contato com o suporte."

    body = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Say voice="{voice}" language="{lang}">{_escape_xml(spoken)}</Say><Hangup/></Response>'
    )
    return Response(content=body, media_type="application/xml")


@router.post("/voice/status/{contact_id}")
async def voice_status(
    contact_id: uuid.UUID,
    CallStatus: str = Form(default=""),
    CallSid: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Twilio status callback: completed | no-answer | busy | failed."""
    contact = await db.get(Contact, contact_id)
    if not contact or contact.channel != Channel.CALL:
        return {"status": "ignored"}

    now = datetime.now(BRAZIL_TZ)
    if CallStatus == "completed":
        contact.status = ContactStatus.DELIVERED
        contact.sent_at = contact.sent_at or now
    elif CallStatus in ("no-answer", "busy", "failed", "canceled"):
        contact.status = ContactStatus.FAILED
        contact.error_message = f"Call {CallStatus}"
    if CallSid and not contact.provider_message_id:
        contact.provider_message_id = CallSid

    await db.commit()
    return {"status": "ok"}
