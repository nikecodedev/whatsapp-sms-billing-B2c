import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from core.database import Base


class Channel(str, PyEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    CALL = "call"


class ContactStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RESPONDED = "responded"
    PAID = "paid"


class Contact(Base):
    """A single contact attempt — one row per message/call sent."""
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    debtor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True)

    channel: Mapped[Channel] = mapped_column(Enum(Channel), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    # AI-generated content
    message_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_reasoning: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[ContactStatus] = mapped_column(Enum(ContactStatus), default=ContactStatus.SCHEDULED)

    # Provider message ID (Twilio SID, Z-API message ID, etc.)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="contacts")
    debtor: Mapped["Debtor"] = relationship("Debtor", back_populates="contacts")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="contact", uselist=False)
