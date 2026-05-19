from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.debtor import Debtor
from models.schemas import DebtorOut, DebtorImportResult
from importers.debtor_importer import import_debtors

router = APIRouter(prefix="/tenants/{tenant_id}/debtors", tags=["Debtors"])

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


@router.post("/import", response_model=DebtorImportResult)
async def import_debtor_file(
    tenant_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not supported. Use: {ALLOWED_EXTENSIONS}")
    content = await file.read()
    return await import_debtors(content, file.filename, tenant_id, db)


@router.get("/", response_model=list[DebtorOut])
async def list_debtors(
    tenant_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Debtor)
        .where(Debtor.tenant_id == tenant_id, Debtor.is_active == True)
        .offset(skip)
        .limit(limit)
        .order_by(Debtor.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{debtor_id}", response_model=DebtorOut)
async def get_debtor(tenant_id: UUID, debtor_id: UUID, db: AsyncSession = Depends(get_db)):
    debtor = await db.get(Debtor, debtor_id)
    if not debtor or debtor.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Debtor not found")
    return debtor


@router.delete("/{debtor_id}", status_code=204)
async def deactivate_debtor(tenant_id: UUID, debtor_id: UUID, db: AsyncSession = Depends(get_db)):
    debtor = await db.get(Debtor, debtor_id)
    if not debtor or debtor.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Debtor not found")
    debtor.is_active = False
    await db.commit()
