"""Import every model here so Alembic autogenerate and Base.metadata see all tables."""

from app.models.donation import Allocation, Donation
from app.models.enums import AllocationStatus, DonationStatus, UserRole
from app.models.misc import (
    AppSetting,
    AuditLog,
    CollectionPlan,
    FoodCategory,
    Notification,
    StorageType,
)
from app.models.prediction import HistoricalData, ModelVersion, Prediction
from app.models.user import DonorProfile, RecipientProfile, User

__all__ = [
    "Allocation",
    "AllocationStatus",
    "AppSetting",
    "AuditLog",
    "CollectionPlan",
    "Donation",
    "DonationStatus",
    "DonorProfile",
    "FoodCategory",
    "HistoricalData",
    "ModelVersion",
    "Notification",
    "Prediction",
    "RecipientProfile",
    "StorageType",
    "User",
    "UserRole",
]
