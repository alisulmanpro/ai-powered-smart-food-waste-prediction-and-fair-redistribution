from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """Server-side role check (NFR-SC-03). Hiding buttons in the UI is not enough."""

    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]
DonorUser = Annotated[User, Depends(require_roles(UserRole.donor))]
RecipientUser = Annotated[User, Depends(require_roles(UserRole.recipient))]
