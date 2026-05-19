from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from .campaign import CampaignStatus
from .contact import Channel, ContactStatus
from .payment import PaymentMethod, PaymentStatus


# ── Tenant ──────────────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str
    cnpj: str | None = None
    email: EmailStr


class TenantOut(BaseModel):
    id: UUID
    name: str
    cnpj: str | None
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Debtor ───────────────────────────────────────────────────────────────────

class DebtorCreate(BaseModel):
    nome_completo: str
    cpf: str
    telefone: str
    email: str | None = None
    valor_divida: Decimal = Field(gt=0)
    data_vencimento: date
    descricao: str | None = None
    canal_preferencial: str | None = None
    permite_parcelamento: bool = False
    observacoes: str | None = None


class DebtorOut(BaseModel):
    id: UUID
    tenant_id: UUID
    nome_completo: str
    cpf: str
    telefone: str
    email: str | None
    valor_divida: Decimal
    data_vencimento: date
    descricao: str | None
    canal_preferencial: str | None
    permite_parcelamento: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DebtorImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    errors: list[str]


# ── Campaign ─────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    max_whatsapp_attempts: int = 2
    max_sms_attempts: int = 2
    max_call_attempts: int = 1
    contact_interval_hours: int = 48
    settings: dict | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: CampaignStatus | None = None
    max_whatsapp_attempts: int | None = None
    max_sms_attempts: int | None = None
    max_call_attempts: int | None = None
    contact_interval_hours: int | None = None
    settings: dict | None = None


class CampaignOut(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    status: CampaignStatus
    max_whatsapp_attempts: int
    max_sms_attempts: int
    max_call_attempts: int
    contact_interval_hours: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactOut(BaseModel):
    id: UUID
    campaign_id: UUID
    debtor_id: UUID
    channel: Channel
    attempt_number: int
    message_body: str | None
    tone: str | None
    scheduled_at: datetime
    sent_at: datetime | None
    status: ContactStatus
    error_message: str | None

    model_config = {"from_attributes": True}


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentOut(BaseModel):
    id: UUID
    debtor_id: UUID
    asaas_charge_id: str
    short_url: str | None
    method: PaymentMethod
    amount: Decimal
    status: PaymentStatus
    due_date: datetime | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_debtors: int
    active_campaigns: int
    contacts_sent_today: int
    contacts_sent_total: int
    payments_pending: int
    payments_confirmed: int
    total_collected: Decimal
    total_outstanding: Decimal
    recovery_rate: float


class CampaignStats(BaseModel):
    campaign_id: UUID
    campaign_name: str
    total_debtors: int
    contacts_sent: int
    delivered: int
    responded: int
    paid: int
    failed: int
    recovery_rate: float
