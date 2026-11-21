from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AllocationStatus, DonationStatus


class Donation(Base):
    __tablename__ = "donations"
    __table_args__ = (
        CheckConstraint("confirmed_amount > 0", name="amount_positive"),
        CheckConstraint("deadline > available_from", name="deadline_after_available"),
        Index("ix_donations_status_deadline", "status", "deadline"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donor_profiles.user_id"), index=True)
    # Optional link only. A prediction never becomes a donation by itself (BR-01, FR-DN-05).
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id"))
    category: Mapped[str] = mapped_column(Text)
    confirmed_amount: Mapped[float] = mapped_column(Numeric)
    unit: Mapped[str] = mapped_column(Text, default="units", server_default="units")
    available_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    storage_requirements: Mapped[str] = mapped_column(Text)
    pickup_lat: Mapped[float | None] = mapped_column(Float)
    pickup_lng: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status"),
        default=DonationStatus.offered,
        server_default=DonationStatus.offered.value,
    )
    needs_manual_allocation: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    donation_id: Mapped[int] = mapped_column(ForeignKey("donations.id"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("recipient_profiles.user_id"))
    rank: Mapped[int | None] = mapped_column(SmallInteger)
    score: Mapped[float | None] = mapped_column(Numeric)
    reasons: Mapped[dict | None] = mapped_column(JSONB)  # per-criterion contributions (FR-AL-05)
    status: Mapped[AllocationStatus] = mapped_column(
        Enum(AllocationStatus, name="allocation_status"),
        default=AllocationStatus.recommended,
        server_default=AllocationStatus.recommended.value,
    )
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    override_reason: Mapped[str | None] = mapped_column(Text)
    respond_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
