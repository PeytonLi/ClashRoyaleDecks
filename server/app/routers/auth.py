"""
Authentication endpoints consumed by the Next.js BFF/Auth.js layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import verify_bff_origin
from app.models import User
from app.services.auth import (
    AuthServiceError,
    authenticate_password_user,
    create_password_user,
    upsert_google_user,
)


router = APIRouter(dependencies=[Depends(verify_bff_origin)])


class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleOAuthRequest(BaseModel):
    email: str
    google_sub: str
    email_verified: bool
    name: Optional[str] = None
    image_url: Optional[str] = None


class AuthUserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    image_url: Optional[str] = None


def _response_from_user(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        image_url=user.image_url,
    )


@router.post("/signup", response_model=AuthUserResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> AuthUserResponse:
    try:
        user = await create_password_user(
            db,
            email=body.email,
            password=body.password,
            name=body.name,
        )
    except AuthServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return _response_from_user(user)


@router.post("/login", response_model=AuthUserResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthUserResponse:
    try:
        user = await authenticate_password_user(db, email=body.email, password=body.password)
    except AuthServiceError:
        user = None

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _response_from_user(user)


@router.post("/oauth/google", response_model=AuthUserResponse)
async def google_oauth(
    body: GoogleOAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthUserResponse:
    try:
        user = await upsert_google_user(
            db,
            email=body.email,
            google_sub=body.google_sub,
            email_verified=body.email_verified,
            name=body.name,
            image_url=body.image_url,
        )
    except AuthServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return _response_from_user(user)
