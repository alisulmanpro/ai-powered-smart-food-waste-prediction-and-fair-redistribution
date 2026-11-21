from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HistoricalData(Base):
    __tablename__ = "historical_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    donor_id: Mapped[int | None] = mapped_column(ForeignKey("donor_profiles.user_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    meal_period: Mapped[str | None] = mapped_column(Text)
    food_category: Mapped[str] = mapped_column(Text)
    prepared_amount: Mapped[float | None] = mapped_column(Numeric)
    sold_amount: Mapped[float | None] = mapped_column(Numeric)
    leftover_amount: Mapped[float | None] = mapped_column(Numeric)
    is_event: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # BR-07: synthetic data must always be labelled
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    algorithm: Mapped[str] = mapped_column(Text)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    mae: Mapped[float | None] = mapped_column(Numeric)
    rmse: Mapped[float | None] = mapped_column(Numeric)
    file_path: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    donor_id: Mapped[int | None] = mapped_column(ForeignKey("donor_profiles.user_id"))
    date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(Text)
    predicted_amount: Mapped[float] = mapped_column(Numeric)
    model_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"))
