"""
JWT security utilities and dependency functions for RBAC.

Responsibilities:
  - Password hashing / verification (bcrypt via passlib)
  - JWT token creation and verification (python-jose)
  - FastAPI dependency functions: get_current_user, require_admin
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.database.session import get_db

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme – token extracted from Authorization: Bearer <token> ────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload claims (typically {"sub": email, "role": role}).
        expires_delta: Optional custom expiry. Defaults to settings value.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises:
        UnauthorizedError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedError("Could not validate credentials")


# ── FastAPI Dependency Functions ──────────────────────────────────────────────


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency that extracts and validates the current authenticated user.
    Import User model lazily to avoid circular imports.
    """
    from app.repositories.user_repository import UserRepository

    payload = decode_token(token)
    email: Optional[str] = payload.get("sub")
    if not email:
        raise UnauthorizedError("Could not validate credentials")

    repo = UserRepository(db)
    user = await repo.find_by_email(email)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise ForbiddenError("Account is inactive")
    return user


async def require_admin(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency that requires the current user to have ADMIN role.
    Raises 403 Forbidden if not an admin.
    """
    from app.models.user import Role

    if current_user.role != Role.ADMIN:
        raise ForbiddenError("Administrator access required")
    return current_user
