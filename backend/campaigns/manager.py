"""
Campaign manager: orchestrates debtor selection, AI decisions,
payment link generation, and contact scheduling.
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from models.debtor import Debtor
from models.campaign import Campaign
from models.contact import Contact, ContactStatus, Channel
from models.payment import Payment, PaymentMethod, PaymentStatus
from ai.decision_engine import decide_contact
from payments.asaas import get_or_create_customer, create_pix_charge
from payments.shortener import shorten
from .compliance import (
    parse_send_time,
    contacted_today,
    interval_elapsed,
    next_allowed_slot,
)

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


async def enqueue_campaign_contacts(
    campaign_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    For each eligible debtor in the campaign's tenant, determine the next contact
    attempt and create a scheduled Contact record.
    Returns a summary dict.
    """
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise ValueError("Campaign not found")

    # Fetch all active debtors for this tenant
    result = await db.execute(
        select(Debtor).where(
            Debtor.tenant_id == tenant_id,
            Debtor.is_active == True,
        )
    )
    debtors = result.scalars().all()

    scheduled = 0
    skipped = 0

    for debtor in debtors:
        # Fetch existing contacts for this debtor in this campaign
        contact_result = await db.execute(
            select(Contact)
            .where(Contact.campaign_id == campaign_id, Contact.debtor_id == debtor.id)
            .order_by(Contact.created_at.desc())
        )
        prior_contacts = contact_result.scalars().all()

        # Skip if debtor already paid
        paid_result = await db.execute(
            select(Payment).where(
                Payment.debtor_id == debtor.id,
                Payment.status == PaymentStatus.CONFIRMED,
            )
        )
        if paid_result.scalar_one_or_none():
            skipped += 1
            continue

        last_contact = prior_contacts[0] if prior_contacts else None

        # CDC check: don't schedule if contacted today
        last_sent = last_contact.sent_at if last_contact else None
        if contacted_today(last_sent):
            skipped += 1
            continue

        # CDC check: minimum interval between attempts
        if not interval_elapsed(last_sent, campaign.contact_interval_hours):
            skipped += 1
            continue

        total_attempts = len([c for c in prior_contacts if c.status != ContactStatus.FAILED])
        max_total = campaign.max_whatsapp_attempts + campaign.max_sms_attempts + campaign.max_call_attempts
        if total_attempts >= max_total:
            skipped += 1
            continue

        attempt_number = total_attempts + 1

        # Build history for AI context
        history = [
            {
                "channel": c.channel.value,
                "sent_at": c.sent_at.strftime("%d/%m/%Y %H:%M") if c.sent_at else "agendado",
                "status": c.status.value,
            }
            for c in prior_contacts
        ]

        # Ask Claude for the decision
        decision = await decide_contact(
            nome_completo=debtor.nome_completo,
            valor_divida=float(debtor.valor_divida),
            data_vencimento=debtor.data_vencimento,
            canal_preferencial=debtor.canal_preferencial,
            permite_parcelamento=debtor.permite_parcelamento,
            attempt_number=attempt_number,
            max_whatsapp=campaign.max_whatsapp_attempts,
            max_sms=campaign.max_sms_attempts,
            previous_contacts=history,
            observacoes=debtor.observacoes,
        )

        # Generate payment charge (Pix by default)
        customer_id = await get_or_create_customer(
            cpf=debtor.cpf,
            nome=debtor.nome_completo,
            email=debtor.email,
        )
        charge = await create_pix_charge(
            customer_id=customer_id,
            amount=debtor.valor_divida,
            due_date=debtor.data_vencimento,
            description=debtor.descricao or f"Cobrança QUESH — {debtor.nome_completo}",
            external_reference=str(debtor.id),
        )

        # Shorten the payment link
        short_link = await shorten(charge.invoice_url, db)

        # Save payment record
        payment = Payment(
            tenant_id=tenant_id,
            debtor_id=debtor.id,
            asaas_charge_id=charge.asaas_id,
            asaas_invoice_url=charge.invoice_url,
            short_url=short_link,
            method=PaymentMethod.PIX,
            amount=debtor.valor_divida,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)

        # Embed payment link in message
        message = decision.message.replace("[PAYMENT_LINK]", short_link)

        # Determine scheduled send time
        scheduled_at = parse_send_time(decision.send_time)

        contact = Contact(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            debtor_id=debtor.id,
            channel=Channel(decision.channel),
            attempt_number=attempt_number,
            message_body=message,
            tone=decision.tone,
            ai_reasoning={"reasoning": decision.reasoning},
            scheduled_at=scheduled_at,
            status=ContactStatus.SCHEDULED,
        )
        db.add(contact)
        scheduled += 1

    await db.commit()
    return {"scheduled": scheduled, "skipped": skipped, "total_debtors": len(debtors)}
