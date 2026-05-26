"""
app/users/repository.py

Database query layer for User.
All raw DB operations live here — no business logic.

The service layer calls these methods.
This separation makes unit testing easy (mock the repo, test the service).
"""

import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import User


class UserRepository:
    """
    Handles all User database operations.
    Injected into UserService via dependency injection.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ================================
    # Create
    # ================================

    async def create(self, user_data: dict) -> User:
        """
        Insert a new user into the database.

        Args:
            user_data: dict with all user fields (password already hashed)

        Returns:
            The created User ORM object
        """
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()  # flush to get the generated ID without committing
        await self.db.refresh(user)  # reload from DB to get defaults
        return user

    # ================================
    # Read
    # ================================

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key UUID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email address. Used during login."""
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Fetch user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def username_exists(self, username: str) -> bool:
        """Check if username is already taken."""
        result = await self.db.execute(
            select(User.id).where(User.username == username.lower())
        )
        return result.scalar_one_or_none() is not None

    # ================================
    # Update
    # ================================

    async def update(self, user_id: uuid.UUID, update_data: dict) -> Optional[User]:
        """
        Update user fields by ID.

        Args:
            user_id: UUID of the user to update
            update_data: dict of fields to update

        Returns:
            Updated User ORM object or None if not found
        """
        await self.db.execute(
            update(User).where(User.id == user_id).values(**update_data)
        )
        return await self.get_by_id(user_id)

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update the last_login_at timestamp. Called after successful login."""
        from datetime import datetime, timezone

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

    async def update_password(self, user_id: uuid.UUID, hashed_password: str) -> None:
        """Update user's hashed password."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed_password)
        )

    # ================================
    # Delete
    # ================================

    async def delete(self, user_id: uuid.UUID) -> bool:
        """
        Soft delete — deactivate user instead of removing from DB.
        Hard delete rarely makes sense in production systems.
        """
        result = await self.update(user_id, {"is_active": False})
        return result is not None
