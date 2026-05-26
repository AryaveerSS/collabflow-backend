"""
app/users/routes.py

User profile API endpoints.

Endpoints:
    GET    /users/me              → get current user profile
    PATCH  /users/me              → update current user profile
    POST   /users/me/password     → change password
    GET    /users/{username}      → get public profile of any user
    DELETE /users/me              → deactivate own account
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.users.service import UserService
from app.users.schema import (
    UserResponse,
    UserUpdate,
    UserPublicProfile,
    PasswordChange,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ================================
# GET /users/me
# ================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full profile of the currently authenticated user.
    Requires: Bearer token in Authorization header.
    """
    service = UserService(db)
    user = await service.get_user_by_id(uuid.UUID(current_user["sub"]))
    return user


# ================================
# PATCH /users/me
# ================================


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_my_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update profile fields — full_name, bio, avatar_url.
    Only provided fields are updated.
    """
    service = UserService(db)
    user = await service.update_profile(uuid.UUID(current_user["sub"]), data)
    return user


# ================================
# POST /users/me/password
# ================================


@router.post(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
async def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change the current user's password.
    Requires the current password for verification.
    """
    service = UserService(db)
    await service.change_password(uuid.UUID(current_user["sub"]), data)
    return {"message": "Password updated successfully."}


# ================================
# GET /users/{username}
# ================================


@router.get(
    "/{username}",
    response_model=UserPublicProfile,
    summary="Get public profile of a user",
)
async def get_public_profile(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the public profile of any user by username.
    Hides sensitive data like email.
    """
    service = UserService(db)
    user = await service.get_user_by_email(username)  # re-using by username
    return user


# ================================
# DELETE /users/me
# ================================


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Deactivate own account",
)
async def deactivate_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft deletes the current user's account.
    Account is deactivated, not permanently deleted.
    """
    service = UserService(db)
    await service.deactivate_user(uuid.UUID(current_user["sub"]))
    return {"message": "Account deactivated successfully."}
