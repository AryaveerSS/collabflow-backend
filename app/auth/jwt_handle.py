"""
app/auth/jwt_handler.py

JWT token creation, verification, and refresh token management.
Handles the full token lifecycle for authentication.

Token Types:
    - Access Token  : short-lived (30 min), used for API requests
    - Refresh Token : long-lived (7 days), used to get new access tokens

Usage:
    from app.auth.jwt_handler import create_access_token, verify_access_token
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt

from app.config import settings

# ================================
# Token Payload Structure
# ================================

# Access token payload example:
# {
#     "sub": "user_id_123",        # subject (user id)
#     "email": "user@example.com",
#     "role": "member",
#     "type": "access",
#     "jti": "unique-token-id",    # JWT ID (for blacklisting)
#     "exp": 1716000000,           # expiry timestamp
#     "iat": 1715996400,           # issued at timestamp
# }


# ================================
# Create Tokens
# ================================


def create_access_token(
    user_id: str,
    email: str,
    role: str = "member",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: The user's unique ID (stored as 'sub' claim)
        email: The user's email
        role: The user's role (owner, admin, member, viewer)
        expires_delta: Optional custom expiry duration

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "jti": str(uuid4()),  # unique ID for blacklisting
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a long-lived JWT refresh token.
    Contains minimal info — only user_id and type.

    Args:
        user_id: The user's unique ID
        expires_delta: Optional custom expiry duration

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ================================
# Verify Tokens
# ================================


def verify_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Returns the full decoded payload dict on success.
    Raises ValueError with a descriptive message on failure.

    Checks:
        - Signature is valid
        - Token is not expired
        - Token type is 'access'
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as e:
        raise ValueError(f"Invalid or expired access token: {str(e)}")

    if payload.get("type") != "access":
        raise ValueError("Token type mismatch: expected access token.")

    return payload


def verify_refresh_token(token: str) -> dict:
    """
    Decode and verify a JWT refresh token.

    Returns the full decoded payload dict on success.
    Raises ValueError with a descriptive message on failure.

    Checks:
        - Signature is valid
        - Token is not expired
        - Token type is 'refresh'
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as e:
        raise ValueError(f"Invalid or expired refresh token: {str(e)}")

    if payload.get("type") != "refresh":
        raise ValueError("Token type mismatch: expected refresh token.")

    return payload


# ================================
# Extract Token Data
# ================================


def get_user_id_from_token(token: str) -> str:
    """
    Extract user_id (sub claim) from a verified access token.
    Raises ValueError if token is invalid.
    """
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token missing subject (user_id).")
    return user_id


def get_token_jti(token: str) -> str:
    """
    Extract the JTI (JWT ID) from a token WITHOUT verifying expiry.
    Used during logout to blacklist already-expired tokens too.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},  # skip expiry check
        )
        return payload.get("jti", "")
    except JWTError:
        return ""


# ================================
# Token Pair Helper
# ================================


def create_token_pair(user_id: str, email: str, role: str) -> dict:
    """
    Create both access and refresh tokens in one call.
    Used during login and token refresh.

    Returns:
        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "bearer",
            "expires_in": 1800       # seconds
        }
    """
    access_token = create_access_token(user_id=user_id, email=email, role=role)
    refresh_token = create_refresh_token(user_id=user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
