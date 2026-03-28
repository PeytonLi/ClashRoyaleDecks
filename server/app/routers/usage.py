"""
Usage-tracking endpoints consumed exclusively by the BFF proxy.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_bff_origin
from app.services.usage import FREE_USAGE_LIMIT, check_quota, increment_usage

router = APIRouter(dependencies=[Depends(verify_bff_origin)])


# --- Schemas ---


class UsageRequest(BaseModel):
    ip_address: str


class CheckResponse(BaseModel):
    allowed: bool
    usage_count: int
    limit: int
    is_paid: bool


class IncrementResponse(BaseModel):
    usage_count: int
    limit: int
    remaining: int


# --- Endpoints ---


@router.post("/check", response_model=CheckResponse)
async def check_usage(body: UsageRequest, db: AsyncSession = Depends(get_db)):
    """Return whether *ip_address* is still within the free-tier quota."""
    allowed, count, limit, is_paid = await check_quota(db, body.ip_address)
    return CheckResponse(
        allowed=allowed,
        usage_count=count,
        limit=limit,
        is_paid=is_paid,
    )


@router.post("/increment", response_model=IncrementResponse)
async def increment(body: UsageRequest, db: AsyncSession = Depends(get_db)):
    """Bump the usage counter for *ip_address* after a successful recommendation."""
    row = await increment_usage(db, body.ip_address)
    remaining = max(0, FREE_USAGE_LIMIT - row.usage_count)
    return IncrementResponse(
        usage_count=row.usage_count,
        limit=FREE_USAGE_LIMIT,
        remaining=remaining,
    )
