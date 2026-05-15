"""
Shared FastAPI dependencies for BFF authentication and client identification.
"""

import os

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User


BFF_SHARED_SECRET = os.getenv("BFF_SHARED_SECRET", "")
USER_ID_HEADER = "X-User-Id"


async def verify_bff_origin(request: Request) -> None:
    """Reject requests that did not pass through the BFF proxy.

    When ``BFF_SHARED_SECRET`` is empty (local dev) the check is skipped.
    """
    if not BFF_SHARED_SECRET:
        return
    if request.headers.get("X-BFF-Secret") != BFF_SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


async def require_authenticated_user_id(request: Request) -> int:
    """Return the authenticated app user id forwarded by the BFF proxy."""
    raw_user_id = request.headers.get(USER_ID_HEADER)
    if not raw_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_id = int(raw_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authenticated user")

    if user_id <= 0:
        raise HTTPException(status_code=401, detail="Invalid authenticated user")

    return user_id


async def require_existing_user_id(
    user_id: int = Depends(require_authenticated_user_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Validate that the forwarded authenticated user still exists."""
    result = await db.execute(select(User.id).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=401, detail="Invalid authenticated user")
    return user_id


def get_client_ip(request: Request) -> str:
    """Extract the real client IP from proxy headers, falling back to the
    direct connection address."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    if request.client:
        return request.client.host

    return "127.0.0.1"
