"""
Shared FastAPI dependencies for BFF authentication and client identification.
"""

import os

from fastapi import HTTPException, Request


BFF_SHARED_SECRET = os.getenv("BFF_SHARED_SECRET", "")


async def verify_bff_origin(request: Request) -> None:
    """Reject requests that did not pass through the BFF proxy.

    When ``BFF_SHARED_SECRET`` is empty (local dev) the check is skipped.
    """
    if not BFF_SHARED_SECRET:
        return
    if request.headers.get("X-BFF-Secret") != BFF_SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


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
