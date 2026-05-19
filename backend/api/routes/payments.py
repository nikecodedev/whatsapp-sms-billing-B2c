from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.payment import Payment
from models.schemas import PaymentOut
from models.short_url import ShortUrl
from payments.shortener import resolve

router = APIRouter(tags=["Payments"])
pay_router = APIRouter(prefix="/tenants/{tenant_id}/payments", tags=["Payments"])


@router.get("/p/{slug}")
async def redirect_payment_link(slug: str, db: AsyncSession = Depends(get_db)):
    """Resolve short payment link and redirect to Asaas invoice."""
    destination = await resolve(slug, db)
    if not destination:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    return RedirectResponse(url=destination, status_code=302)


@pay_router.get("/", response_model=list[PaymentOut])
async def list_payments(tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Payment).where(Payment.tenant_id == tenant_id).order_by(Payment.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@pay_router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(tenant_id: UUID, payment_id: UUID, db: AsyncSession = Depends(get_db)):
    payment = await db.get(Payment, payment_id)
    if not payment or payment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
