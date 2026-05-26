"""
app/auth/schema.py

Pydantic schemas for authentication endpoints.

Schemas:
    - LoginRequest      : email + password for login
    - TokenResponse     : access + refresh token response
    - RefreshRequest    : refresh token input for token rotation
    - RegisterResponse  : user data + tokens after registration
"""

from pydantic import BaseModel, EmailStr, Field

# ================================
# Request Schemas
# ================================


class LoginRequest(BaseModel):
    """Input schema for POST /auth/login"""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Input schema for POST /auth/refresh"""

    refresh_token: str = Field(..., min_length=1)


# ================================
# Response Schemas
# ================================


class TokenResponse(BaseModel):
    """
    Returned after login or token refresh.
    Contains both access and refresh tokens.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RegisterResponse(BaseModel):
    """
    Returned after successful registration.
    Contains user info + tokens so user is immediately logged in.
    """

    message: str = "Registration successful."
    user_id: str
    email: str
    username: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    """Returned after successful logout."""

    message: str = "Logged out successfully."
