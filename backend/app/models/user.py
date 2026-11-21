from datetime import datetime, time

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    fcm_token: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    donor_profile: Mapped["DonorProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    recipient_profile: Mapped["RecipientProfile | None"] = relationship(
        back_populates="user", uselist=False
    )


class DonorProfile(Base):
    __tablename__ = "donor_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    business_name: Mapped[str] = mapped_column(Text)
    business_type: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    user: Mapped[User] = relationship(back_populates="donor_profile")


class RecipientProfile(Base):
    __tablename__ = "recipient_profiles"
    __table_args__ = (CheckConstraint("need_level BETWEEN 1 AND 5", name="need_level_range"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    organisation_name: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    capacity_units: Mapped[int] = mapped_column(Integer)
    storage_types: Mapped[list[str]] = mapped_column(ARRAY(Text))  # e.g. ambient, chilled, frozen
    accepted_categories: Mapped[list[str]] = mapped_column(ARRAY(Text))
    open_from: Mapped[time | None] = mapped_column(Time)
    open_to: Mapped[time | None] = mapped_column(Time)
    need_level: Mapped[int] = mapped_column(SmallInteger, default=3, server_default="3")
    verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    user: Mapped[User] = relationship(back_populates="recipient_profile")
