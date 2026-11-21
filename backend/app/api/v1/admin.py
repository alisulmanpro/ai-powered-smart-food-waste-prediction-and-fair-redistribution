from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.audit import log_action
from app.core.security import hash_password
from app.models import RecipientProfile, User, UserRole
from app.schemas.user import ActiveUpdate, AdminCreate, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    _: AdminUser,
    db: DbSession,
    role: UserRole | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[User]:
    stmt = select(User).order_by(User.id).limit(limit).offset(offset)
    if role:
        stmt = stmt.where(User.role == role)
    return list(db.scalars(stmt))


@router.post("/admins", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_admin(payload: AdminCreate, admin: AdminUser, db: DbSession) -> User:
    """Admin accounts are created by an existing admin only (FR-UM-07)."""
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    new_admin = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.admin,
    )
    db.add(new_admin)
    db.flush()
    log_action(db, admin.id, "create_admin", "user", new_admin.id)
    db.commit()
    return new_admin


@router.post("/users/{user_id}/verify", response_model=UserOut)
def verify_recipient(user_id: int, admin: AdminUser, db: DbSession) -> User:
    """Recipient organisations must be verified before they can be allocated food (FR-UM-04)."""
    user = db.get(User, user_id)
    if user is None or user.role != UserRole.recipient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipient not found")
    profile = db.get(RecipientProfile, user_id)
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Recipient has not completed their profile")
    profile.verified = True
    log_action(db, admin.id, "verify_recipient", "user", user_id)
    db.commit()
    return user


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(user_id: int, payload: ActiveUpdate, admin: AdminUser, db: DbSession) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == admin.id and not payload.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate yourself")
    user.is_active = payload.is_active
    log_action(db, admin.id, "set_active", "user", user_id, {"is_active": payload.is_active})
    db.commit()
    return user
