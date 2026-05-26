"""
app/users/schema.py

Pydantic schemas for User request/response validation.

Schemas:
    - UserCreate        : for registration input
    - UserUpdate        : for profile update input
    - UserResponse      : for API responses (no password)
    - UserPublicProfile : minimal public info
    - PasswordChange    : for changing password
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import is_password_strong

# ================================
# Base Schema
# ================================


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Only letters, numbers, underscores. No spaces.",
    )
    full_name: str = Field(..., min_length=2, max_length=150)


# ================================
# Request Schemas
# ================================


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        is_valid, message = is_password_strong(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating user profile. All fields optional."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        is_valid, message = is_password_strong(v)
        if not is_valid:
            raise ValueError(message)
        return v


# ================================
# Response Schemas
# ================================


class UserResponse(BaseModel):
    """
    Full user response — returned after login, register, or get_me.
    Never includes hashed_password.
    """

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}  # allows ORM model → schema conversion


class UserPublicProfile(BaseModel):
    """
    Minimal public profile — shown when other users view someone's profile.
    Hides sensitive fields like email.
    """

    id: uuid.UUID
    username: str
    full_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    """
    Tiny user summary — used inside Task, Comment, Notification responses.
    """

    id: uuid.UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}
