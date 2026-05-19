import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class PaymentMethod(str, PyEnum):
    PIX = "pix"
    BOLETO = "boleto"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    OVERDUE = "overdue"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    debtor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)

    # Asaas identifiers
    asaas_charge_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    asaas_invoice_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # shortened payment link

    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    debtor: Mapped["Debtor"] = relationship("Debtor", back_populates="payments")
    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="payment")
