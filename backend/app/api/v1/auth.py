from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas.user import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> User:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role),
    )
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    """OAuth2 password flow: send form fields `username` (the email) and `password`."""
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not verify_password(form.password, user.password_hash if user else None) or user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")
    return Token(access_token=create_access_token(user.id, user.role.value))
