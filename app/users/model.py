"""
app/users/model.py

User SQLAlchemy ORM model.
Defines the 'users' table in PostgreSQL.

Relationships:
    - User has many WorkspaceMembers (via workspaces)
    - User has many Tasks (assigned tasks)
    - User has many Comments
    - User has many Notifications
    - User has many ActivityLogs
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # ---- Primary Key ----
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # ---- Identity ----
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # ---- Security ----
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ---- Profile ----
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ---- Timestamps ----
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ---- Relationships ----
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(  # type: ignore
        "WorkspaceMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(  # type: ignore
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
    )
    created_tasks: Mapped[list["Task"]] = relationship(  # type: ignore
        "Task",
        back_populates="creator",
        foreign_keys="Task.creator_id",
    )
    comments: Mapped[list["Comment"]] = relationship(  # type: ignore
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} username={self.username}>"
