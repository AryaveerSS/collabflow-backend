"""
app/users/service.py

Business logic layer for User operations.
Sits between routes and repository.

Rules:
    - Routes call service methods
    - Service calls repository methods
    - Service never directly touches the DB session
    - Service raises HTTPExceptions for business rule violations
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.repository import UserRepository
from app.users.schema import UserCreate, UserUpdate, UserResponse, PasswordChange
from app.users.model import User
from app.core.security import hash_password, verify_password


class UserService:

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    # ================================
    # Create User
    # ================================

    async def create_user(self, data: UserCreate) -> User:
        """
        Register a new user.

        Steps:
            1. Check email not already taken
            2. Check username not already taken
            3. Hash the password
            4. Insert into DB

        Raises:
            400 if email or username already exists
        """
        # Check email uniqueness
        if await self.repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        # Check username uniqueness
        if await self.repo.username_exists(data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken.",
            )

        # Prepare user data with hashed password
        user_data = {
            "email": data.email.lower(),
            "username": data.username.lower(),
            "full_name": data.full_name,
            "hashed_password": hash_password(data.password),
            "is_active": True,
            "is_verified": False,
        }

        return await self.repo.create(user_data)

    # ================================
    # Get User
    # ================================

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """
        Fetch user by ID.
        Raises 404 if not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def get_user_by_email(self, email: str) -> User:
        """
        Fetch user by email.
        Raises 404 if not found.
        """
        user = await self.repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    # ================================
    # Update User
    # ================================

    async def update_profile(
        self,
        user_id: uuid.UUID,
        data: UserUpdate,
    ) -> User:
        """
        Update user profile fields.
        Only updates fields that are actually provided (not None).
        """
        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update.",
            )

        update_data["updated_at"] = datetime.now(timezone.utc)

        user = await self.repo.update(user_id, update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    # ================================
    # Password Change
    # ================================

    async def change_password(
        self,
        user_id: uuid.UUID,
        data: PasswordChange,
    ) -> None:
        """
        Change user password.

        Steps:
            1. Fetch current user
            2. Verify current password
            3. Hash and save new password

        Raises:
            400 if current password is wrong
        """
        user = await self.get_user_by_id(user_id)

        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        new_hashed = hash_password(data.new_password)
        await self.repo.update_password(user_id, new_hashed)

    # ================================
    # Deactivate User
    # ================================

    async def deactivate_user(self, user_id: uuid.UUID) -> None:
        """
        Soft delete — mark user as inactive.
        User data is preserved in DB.
        """
        success = await self.repo.delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
