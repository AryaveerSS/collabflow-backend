"""
app/auth/service.py

Authentication business logic.
Handles login, logout, and token refresh operations.

Flow:
    Register → UserService.create_user() → create_token_pair()
    Login    → verify credentials → update_last_login() → create_token_pair()
    Refresh  → verify_refresh_token() → create_token_pair()
    Logout   → blacklist token JTI in Redis
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.repository import UserRepository
from app.auth.jwt_handler import (
    verify_refresh_token,
    create_token_pair,
    get_token_jti,
)
from app.auth.schema import LoginRequest, TokenResponse, RegisterResponse
from app.users.schema import UserCreate
from app.users.service import UserService
from app.core.security import verify_password
from app.config import settings

import redis.asyncio as aioredis


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.user_service = UserService(db)

    # ================================
    # Register
    # ================================

    async def register(self, data: UserCreate) -> RegisterResponse:
        """
        Register a new user and return tokens immediately.
        User is logged in right after registration — no separate login step needed.
        """
        # Create user via UserService (handles validation + hashing)
        user = await self.user_service.create_user(data)

        # Generate token pair
        tokens = create_token_pair(
            user_id=str(user.id),
            email=user.email,
            role="member",
        )

        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            **tokens,
        )

    # ================================
    # Login
    # ================================

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate user with email and password.

        Steps:
            1. Find user by email
            2. Verify password
            3. Check account is active
            4. Update last_login_at
            5. Return token pair

        Raises:
            401 for invalid credentials (intentionally vague for security)
            403 if account is deactivated
        """
        # Fetch user
        user = await self.user_repo.get_by_email(data.email)

        # Intentionally same error for wrong email OR wrong password
        # Never reveal which one is wrong — prevents user enumeration attacks
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )

        # Update last login timestamp
        await self.user_repo.update_last_login(user.id)

        # Create and return token pair
        tokens = create_token_pair(
            user_id=str(user.id),
            email=user.email,
            role="member",  # TODO: fetch actual workspace role in later phase
        )

        return TokenResponse(**tokens)

    # ================================
    # Refresh Token
    # ================================

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new access token using a valid refresh token.

        Steps:
            1. Verify refresh token signature and expiry
            2. Fetch user to make sure they still exist and are active
            3. Return new token pair (refresh token is also rotated)

        Raises:
            401 if refresh token is invalid or expired
        """
        try:
            payload = verify_refresh_token(refresh_token)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

        user = await self.user_repo.get_by_id(payload["sub"])

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account deactivated.",
            )

        tokens = create_token_pair(
            user_id=str(user.id),
            email=user.email,
            role="member",
        )

        return TokenResponse(**tokens)

    # ================================
    # Logout
    # ================================

    async def logout(self, access_token: str) -> None:
        """
        Blacklist the access token's JTI in Redis so it can't be reused.

        Even though JWTs are stateless, we store the JTI (unique token ID)
        in Redis with a TTL equal to the token's remaining lifetime.
        The auth middleware checks this blacklist on every request.

        Steps:
            1. Extract JTI from token (without verifying expiry)
            2. Store JTI in Redis with TTL = ACCESS_TOKEN_EXPIRE_MINUTES
        """
        jti = get_token_jti(access_token)

        if not jti:
            return  # Token already invalid, nothing to blacklist

        try:
            redis_client = aioredis.from_url(settings.REDIS_URL)
            ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

            # Store blacklisted JTI
            await redis_client.setex(
                name=f"blacklist:{jti}",
                time=ttl_seconds,
                value="1",
            )
            await redis_client.aclose()

        except Exception:
            # Redis failure should not block logout
            # Token will expire naturally
            pass
