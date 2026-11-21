from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, DonorUser, RecipientUser
from app.models import DonorProfile, RecipientProfile, User
from app.schemas.user import (
    DonorProfileIn,
    DonorProfileOut,
    MeOut,
    RecipientProfileIn,
    RecipientProfileOut,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeOut)
def read_me(user: CurrentUser) -> User:
    return user


@router.put("/me/donor-profile", response_model=DonorProfileOut)
def upsert_donor_profile(payload: DonorProfileIn, user: DonorUser, db: DbSession) -> DonorProfile:
    profile = user.donor_profile or DonorProfile(user_id=user.id)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    return profile


@router.put("/me/recipient-profile", response_model=RecipientProfileOut)
def upsert_recipient_profile(
    payload: RecipientProfileIn, user: RecipientUser, db: DbSession
) -> RecipientProfile:
    # `verified` is not part of the payload: only admins can verify (FR-UM-04).
    profile = user.recipient_profile or RecipientProfile(user_id=user.id, verified=False)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    return profile
