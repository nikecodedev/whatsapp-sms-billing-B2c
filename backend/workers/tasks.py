"""
Celery tasks: dispatch scheduled contacts and sync payment statuses.
These tasks run synchronously (Celery is sync by default).
Async DB calls are bridged via asyncio.run().
"""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from celery_app import celery
from core.database import AsyncSessionLocal
from models.contact import Contact, ContactStatus, Channel
from models.payment import Payment, PaymentStatus
from channels.whatsapp import send_whatsapp
from channels.sms import send_sms
from channels.voice import place_call
from payments.asaas import get_payment_status

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery.task(name="workers.tasks.dispatch_pending_contacts", bind=True, max_retries=3)
def dispatch_pending_contacts(self):
    """Find all contacts scheduled for now-or-earlier and send them."""
    async def _inner():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, and_

            now = datetime.now(BRAZIL_TZ)
            result = await db.execute(
                select(Contact)
                .where(
                    Contact.status == ContactStatus.SCHEDULED,
                    Contact.scheduled_at <= now,
                )
                .limit(100)
            )
            contacts = result.scalars().all()

            for contact in contacts:
                await _send_contact(contact, db)

            await db.commit()
            return len(contacts)

    count = _run(_inner())
    return {"dispatched": count}


async def _send_contact(contact: Contact, db):
    from sqlalchemy import select
    from models.debtor import Debtor

    debtor = await db.get(Debtor, contact.debtor_id)
    if not debtor:
        contact.status = ContactStatus.FAILED
        contact.error_message = "Debtor not found"
        return

    message = contact.message_body or ""

    import asyncio
    loop = asyncio.get_event_loop()

    if contact.channel == Channel.WHATSAPP:
        result = await send_whatsapp(debtor.telefone, message)
    elif contact.channel == Channel.SMS:
        # Twilio SDK is sync — offload to thread pool
        result = await loop.run_in_executor(None, send_sms, debtor.telefone, message)
    elif contact.channel == Channel.CALL:
        # Voice: place outbound call. Twilio will fetch TwiML from our webhook
        # using contact.id to look up the AI-generated message.
        result = await loop.run_in_executor(None, place_call, debtor.telefone, str(contact.id))
    else:
        contact.status = ContactStatus.FAILED
        contact.error_message = f"Unknown channel: {contact.channel}"
        contact.sent_at = datetime.now(BRAZIL_TZ)
        return

    contact.sent_at = datetime.now(BRAZIL_TZ)
    if result.success:
        contact.status = ContactStatus.SENT
        contact.provider_message_id = result.message_id
    else:
        contact.status = ContactStatus.FAILED
        contact.error_message = result.error


@celery.task(name="workers.tasks.sync_payment_statuses")
def sync_payment_statuses():
    """Sync pending payment statuses from Asaas."""
    async def _inner():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(
                select(Payment).where(Payment.status == PaymentStatus.PENDING).limit(200)
            )
            payments = result.scalars().all()

            updated = 0
            for payment in payments:
                try:
                    remote_status = await get_payment_status(payment.asaas_charge_id)
                    if remote_status == "RECEIVED" or remote_status == "CONFIRMED":
                        payment.status = PaymentStatus.CONFIRMED
                        payment.paid_at = datetime.now(BRAZIL_TZ)
                        # Mark related contact as paid
                        if payment.contact_id:
                            contact = await db.get(Contact, payment.contact_id)
                            if contact:
                                contact.status = ContactStatus.PAID
                        updated += 1
                    elif remote_status == "OVERDUE":
                        payment.status = PaymentStatus.OVERDUE
                except Exception:
                    pass

            await db.commit()
            return updated

    updated = _run(_inner())
    return {"synced": updated}
