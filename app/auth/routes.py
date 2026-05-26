"""
app/auth/routes.py

Authentication API endpoints.

Endpoints:
    POST /auth/register  → create account + return tokens
    POST /auth/login     → login + return tokens
    POST /auth/refresh   → get new access token
    POST /auth/logout    → blacklist current token
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.service import AuthService
from app.auth.schema import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    RegisterResponse,
    LogoutResponse,
)
from app.users.schema import UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer()


# ================================
# POST /auth/register
# ================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.

    - Validates email format and uniqueness
    - Validates username format and uniqueness
    - Enforces password strength rules
    - Returns user info + JWT token pair (user is immediately logged in)
    """
    service = AuthService(db)
    return await service.register(data)


# ================================
# POST /auth/login
# ================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email and password.

    - Returns access token (30 min) + refresh token (7 days)
    - Use access token in Authorization: Bearer <token> header
    - Use refresh token at /auth/refresh when access token expires
    """
    service = AuthService(db)
    return await service.login(data)


# ================================
# POST /auth/refresh
# ================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a new access token using a valid refresh token.

    - Both access and refresh tokens are rotated on each refresh
    - Old refresh token becomes invalid after rotation
    """
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


# ================================
# POST /auth/logout
# ================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and invalidate token",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout the current user.

    - Blacklists the current access token's JTI in Redis
    - Token cannot be reused even if it hasn't expired yet
    - Client should delete both tokens from storage
    """
    service = AuthService(db)
    await service.logout(credentials.credentials)
    return LogoutResponse()
