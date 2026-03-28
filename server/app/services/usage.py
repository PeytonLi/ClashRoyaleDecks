"""
Persistent usage-tracking service backed by the UsageTracking table.
"""

import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsageTracking

FREE_USAGE_LIMIT = int(os.getenv("FREE_USAGE_LIMIT", "20"))


async def get_or_create_usage(db: AsyncSession, ip_address: str) -> UsageTracking:
    """Return the UsageTracking row for *ip_address*, creating one if absent.

    Uses SELECT … FOR UPDATE to serialise concurrent callers on the same IP.
    """
    result = await db.execute(
        select(UsageTracking)
        .where(UsageTracking.ip_address == ip_address)
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = UsageTracking(
            ip_address=ip_address,
            usage_count=0,
            is_paid=False,
        )
        db.add(row)
        await db.flush()
    return row


async def check_quota(
    db: AsyncSession,
    ip_address: str,
    free_limit: int = FREE_USAGE_LIMIT,
) -> tuple[bool, int, int, bool]:
    """Check whether *ip_address* may make another recommendation request.

    Returns ``(allowed, current_count, limit, is_paid)``.
    Paid users are always allowed.
    """
    row = await get_or_create_usage(db, ip_address)
    if row.is_paid:
        return True, row.usage_count, free_limit, True
    return row.usage_count < free_limit, row.usage_count, free_limit, False


async def increment_usage(db: AsyncSession, ip_address: str) -> UsageTracking:
    """Atomically bump *usage_count* and touch *last_used*."""
    row = await get_or_create_usage(db, ip_address)
    row.usage_count += 1
    row.last_used = datetime.now(timezone.utc)
    await db.flush()
    return row
