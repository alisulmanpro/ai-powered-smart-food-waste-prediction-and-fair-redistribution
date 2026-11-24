"""Idempotent seed: default categories, storage types, settings and the first admin.

Run:  python -m scripts.seed   (the dev/prod container entrypoints do this automatically)
"""

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import AppSetting, FoodCategory, StorageType, User, UserRole

DEFAULT_CATEGORIES = ["bakery", "cooked meals", "fruit and vegetables", "dairy", "beverages"]
DEFAULT_STORAGE_TYPES = ["ambient", "chilled", "frozen"]
DEFAULT_SETTINGS = {
    # Allocation criteria weights (sum to 1). Editable by admins (FR-AD-03).
    "allocation_weights": {
        "need": 0.30,
        "capacity_fit": 0.15,
        "urgency": 0.20,
        "distance": 0.15,
        "fairness": 0.20,
    },
    "response_window_minutes": settings.ALLOCATION_RESPONSE_MINUTES,
}


def seed() -> None:
    with SessionLocal() as db:
        for name in DEFAULT_CATEGORIES:
            if not db.scalar(select(FoodCategory.id).where(FoodCategory.name == name)):
                db.add(FoodCategory(name=name))
        for name in DEFAULT_STORAGE_TYPES:
            if not db.scalar(select(StorageType.id).where(StorageType.name == name)):
                db.add(StorageType(name=name))
        for key, value in DEFAULT_SETTINGS.items():
            if db.get(AppSetting, key) is None:
                db.add(AppSetting(key=key, value=value))

        admin_email = settings.FIRST_ADMIN_EMAIL.lower()
        if not db.scalar(select(User.id).where(User.email == admin_email)):
            db.add(
                User(
                    name=settings.FIRST_ADMIN_NAME,
                    email=admin_email,
                    password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
                    role=UserRole.admin,
                    email_verified=True,
                )
            )
            print(f"Created first admin: {admin_email}")

        db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
