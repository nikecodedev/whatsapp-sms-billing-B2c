"""
Asaas webhook handler — receives payment status updates.
Register this URL in your Asaas dashboard:
  POST https://your-domain.com/webhooks/asaas
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.payment import Payment, PaymentStatus
from models.contact import Contact, ContactStatus

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
