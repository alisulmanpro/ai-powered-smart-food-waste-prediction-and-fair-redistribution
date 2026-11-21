from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FoodCategory(Base):
    __tablename__ = "food_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)


class StorageType(Base):
    __tablename__ = "storage_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)


class AppSetting(Base):
    """Key/value settings editable by admins (allocation weights, response window, ...)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)


class CollectionPlan(Base):
    __tablename__ = "collection_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_date: Mapped[date] = mapped_column(Date)
    ordered_stops: Mapped[list | None] = mapped_column(JSONB)
    est_distance_km: Mapped[float | None] = mapped_column(Numeric)
    est_time_min: Mapped[float | None] = mapped_column(Numeric)
    feasibility_flags: Mapped[dict | None] = mapped_column(JSONB)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class AuditLog(Base):
    """Every override, allocation decision and status change is logged (FR-AD-01)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(Text)
    entity: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[int | None] = mapped_column()
    details: Mapped[dict | None] = mapped_column(JSONB)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
