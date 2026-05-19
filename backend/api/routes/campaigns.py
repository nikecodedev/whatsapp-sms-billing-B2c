from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.campaign import Campaign, CampaignStatus
from models.contact import Contact, ContactStatus
from models.payment import Payment, PaymentStatus
from models.schemas import CampaignCreate, CampaignUpdate, CampaignOut, CampaignStats
from campaigns.manager import enqueue_campaign_contacts

router = APIRouter(prefix="/tenants/{tenant_id}/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    tenant_id: UUID,
    body: CampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(tenant_id=tenant_id, **body.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/", response_model=list[CampaignOut])
async def list_campaigns(tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign).where(Campaign.tenant_id == tenant_id).order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(tenant_id: UUID, campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    body: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/launch", status_code=202)
async def launch_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Set campaign to active and enqueue contact scheduling in background."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="Campaign already active")

    campaign.status = CampaignStatus.ACTIVE
    await db.commit()

    background_tasks.add_task(enqueue_campaign_contacts, campaign_id, tenant_id, db)
    return {"message": "Campaign launched. Contact scheduling started in background."}


@router.post("/{campaign_id}/pause", response_model=CampaignOut)
async def pause_campaign(tenant_id: UUID, campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def campaign_stats(tenant_id: UUID, campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Count contacts by status
    contact_counts = {}
    for s in ContactStatus:
        r = await db.execute(
            select(func.count()).where(
                Contact.campaign_id == campaign_id,
                Contact.status == s,
            )
        )
        contact_counts[s.value] = r.scalar() or 0

    total_contacts = sum(contact_counts.values())

    paid = contact_counts.get(ContactStatus.PAID.value, 0)
    recovery_rate = (paid / total_contacts * 100) if total_contacts else 0.0

    # Unique debtors
    unique_debtors = await db.execute(
        select(func.count(Contact.debtor_id.distinct())).where(Contact.campaign_id == campaign_id)
    )

    return CampaignStats(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_debtors=unique_debtors.scalar() or 0,
        contacts_sent=contact_counts.get(ContactStatus.SENT.value, 0),
        delivered=contact_counts.get(ContactStatus.DELIVERED.value, 0),
        responded=contact_counts.get(ContactStatus.RESPONDED.value, 0),
        paid=paid,
        failed=contact_counts.get(ContactStatus.FAILED.value, 0),
        recovery_rate=round(recovery_rate, 2),
    )
