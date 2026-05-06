"""
User account helpers for password and OAuth authentication.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000


class AuthServiceError(ValueError):
    """Raised when an account operation cannot be completed."""


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise AuthServiceError("Enter a valid email address.")
    return normalized


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthServiceError("Password must be at least 8 characters.")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    if not stored_hash:
        return False

    try:
        algorithm, iterations_raw, salt, expected = stored_hash.split("$", 3)
        iterations = int(iterations_raw)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual, expected)


async def create_password_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: Optional[str] = None,
) -> User:
    normalized_email = normalize_email(email)
    validate_password(password)

    result = await db.execute(select(User).where(User.email == normalized_email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise AuthServiceError("An account with this email already exists.")

    user = User(
        email=normalized_email,
        name=name.strip() if name and name.strip() else None,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_password_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> Optional[User]:
    normalized_email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def upsert_google_user(
    db: AsyncSession,
    *,
    email: str,
    google_sub: str,
    email_verified: bool,
    name: Optional[str] = None,
    image_url: Optional[str] = None,
) -> User:
    if not email_verified:
        raise AuthServiceError("Google account email must be verified.")

    normalized_email = normalize_email(email)
    clean_sub = google_sub.strip()
    if not clean_sub:
        raise AuthServiceError("Google account id is missing.")

    result = await db.execute(
        select(User).where(or_(User.google_sub == clean_sub, User.email == normalized_email))
    )
    matches = result.scalars().all()
    if len(matches) > 1:
        raise AuthServiceError("This Google account is already linked to another user.")
    user = matches[0] if matches else None

    now = datetime.now(timezone.utc)
    clean_name = name.strip() if name and name.strip() else None

    if user is None:
        user = User(
            email=normalized_email,
            name=clean_name,
            google_sub=clean_sub,
            image_url=image_url,
            updated_at=now,
        )
        db.add(user)
    else:
        if user.google_sub and user.google_sub != clean_sub:
            raise AuthServiceError("This email is already linked to another Google account.")
        user.google_sub = user.google_sub or clean_sub
        user.name = user.name or clean_name
        user.image_url = image_url or user.image_url
        user.updated_at = now

    await db.flush()
    return user
