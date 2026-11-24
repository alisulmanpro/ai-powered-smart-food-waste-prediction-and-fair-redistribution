from typing import Annotated

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_verification_token,
    decode_verification_token,
    hash_password,
    verify_password,
)
from app.models import User, UserRole
from app.schemas.user import (
    EmailVerifyIn,
    MessageOut,
    ResendVerificationIn,
    Token,
    UserCreate,
    UserOut,
)
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _verification_link(user_id: int) -> str:
    token = create_verification_token(user_id)
    return f"{settings.PUBLIC_API_URL}{settings.API_PREFIX}/auth/verify-email?token={token}"


def _queue_verification_email(
    background_tasks: BackgroundTasks, *, email: str, name: str, user_id: int
) -> None:
    background_tasks.add_task(
        send_verification_email,
        to=email,
        name=name,
        verify_url=_verification_link(user_id),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession, background_tasks: BackgroundTasks) -> User:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role),
        email_verified=False,
    )
    db.add(user)
    db.commit()
    _queue_verification_email(background_tasks, email=email, name=payload.name, user_id=user.id)
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
    if not user.email_verified:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Email not verified. Check your inbox for the verification link.",
        )
    return Token(access_token=create_access_token(user.id, user.role.value))


def _apply_verification(db: DbSession, token: str) -> User:
    try:
        user_id = decode_verification_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token"
        ) from None
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not user.email_verified:
        user.email_verified = True
        db.commit()
    return user


@router.post("/verify-email", response_model=MessageOut)
def verify_email(payload: EmailVerifyIn, db: DbSession) -> MessageOut:
    """Programmatic verification (mobile/web clients that hold the token)."""
    user = _apply_verification(db, payload.token)
    return MessageOut(message=f"Email verified for {user.email}. You can now sign in.")


def _verification_page(*, ok: bool, title: str, body: str) -> str:
    accent = "#2f855a" if ok else "#c53030"
    return f"""\
<!DOCTYPE html>
<html>
  <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title></head>
  <body style="margin:0;padding:24px;background:#f5f7fa;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:480px;margin:48px auto;background:#fff;border-radius:12px;padding:28px;
                border-top:4px solid {accent};">
      <h2 style="margin:0 0 12px;color:{accent};">{title}</h2>
      <p style="color:#3e4c59;line-height:1.5;">{body}</p>
      <p style="color:#616e7c;font-size:13px;">You can close this page.</p>
    </div>
  </body>
</html>
"""


@router.get("/verify-email", response_class=HTMLResponse, include_in_schema=False)
def verify_email_link(token: str, db: DbSession) -> HTMLResponse:
    """Landing page for the link in the verification email (no app setup required)."""
    try:
        user = _apply_verification(db, token)
    except HTTPException as exc:
        return HTMLResponse(
            _verification_page(
                ok=False,
                title="Verification failed",
                body=str(exc.detail),
            ),
            status_code=exc.status_code,
        )
    return HTMLResponse(
        _verification_page(
            ok=True,
            title="Email verified",
            body=f"{user.email} is verified. You can now sign in to your account.",
        )
    )


@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(
    payload: ResendVerificationIn, db: DbSession, background_tasks: BackgroundTasks
) -> MessageOut:
    """Always returns the same message so accounts cannot be enumerated."""
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and not user.email_verified and user.is_active:
        _queue_verification_email(
            background_tasks, email=user.email, name=user.name, user_id=user.id
        )
    return MessageOut(
        message="If that address is registered and unverified, a verification email is on its way."
    )
