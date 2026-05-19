from uuid import UUID
from datetime import datetime, date
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.debtor import Debtor
from models.campaign import Campaign, CampaignStatus
from models.contact import Contact, ContactStatus
from models.payment import Payment, PaymentStatus
from models.schemas import DashboardStats

router = APIRouter(prefix="/tenants/{tenant_id}/dashboard", tags=["Dashboard"])
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


@router.get("/", response_model=DashboardStats)
async def get_dashboard(tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    today = datetime.now(BRAZIL_TZ).date()

    total_debtors = (await db.execute(
        select(func.count()).where(Debtor.tenant_id == tenant_id, Debtor.is_active == True)
    )).scalar() or 0

    active_campaigns = (await db.execute(
        select(func.count()).where(Campaign.tenant_id == tenant_id, Campaign.status == CampaignStatus.ACTIVE)
    )).scalar() or 0

    contacts_today = (await db.execute(
        select(func.count()).where(
            Contact.tenant_id == tenant_id,
            Contact.sent_at >= datetime.combine(today, datetime.min.time()),
            Contact.status.in_([ContactStatus.SENT, ContactStatus.DELIVERED]),
        )
    )).scalar() or 0

    contacts_total = (await db.execute(
        select(func.count()).where(
            Contact.tenant_id == tenant_id,
            Contact.status.in_([ContactStatus.SENT, ContactStatus.DELIVERED, ContactStatus.PAID]),
        )
    )).scalar() or 0

    payments_pending = (await db.execute(
        select(func.count()).where(Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.PENDING)
    )).scalar() or 0

    payments_confirmed = (await db.execute(
        select(func.count()).where(Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.CONFIRMED)
    )).scalar() or 0

    total_collected = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.CONFIRMED
        )
    )).scalar() or 0

    total_outstanding = (await db.execute(
        select(func.coalesce(func.sum(Debtor.valor_divida), 0)).where(
            Debtor.tenant_id == tenant_id, Debtor.is_active == True
        )
    )).scalar() or 0

    recovery_rate = (float(total_collected) / float(total_outstanding) * 100) if total_outstanding else 0.0

    return DashboardStats(
        total_debtors=total_debtors,
        active_campaigns=active_campaigns,
        contacts_sent_today=contacts_today,
        contacts_sent_total=contacts_total,
        payments_pending=payments_pending,
        payments_confirmed=payments_confirmed,
        total_collected=total_collected,
        total_outstanding=total_outstanding,
        recovery_rate=round(recovery_rate, 2),
    )
