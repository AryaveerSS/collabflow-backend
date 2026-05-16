"""
app/core/database.py

Database engine, session factory, and Base model setup.
All DB interaction in the app flows through this module.

Usage:
    - Import `get_db` as a FastAPI dependency in routes
    - Import `Base` in all models so they're registered for migrations
    - Import `engine` only in main.py for startup/teardown
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings


# ================================
# Engine
# ================================

engine: AsyncEngine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DEBUG,           # logs all SQL queries in DEBUG mode
    pool_size=10,                  # number of persistent connections
    max_overflow=20,               # extra connections allowed under load
    pool_pre_ping=True,            # verify connection is alive before using
)


# ================================
# Session Factory
# ================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


# ================================
# Base Model
# ================================

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Every model in the app inherits from this.

    Example:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
    """
    pass


# ================================
# Dependency: get_db
# ================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
    Automatically commits on success, rolls back on exception, always closes.

    Usage in routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ================================
# Health Check
# ================================

async def check_database_connection() -> bool:
    """
    Verifies the database is reachable.
    Called during app startup health check.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        return False


# ================================
# Create / Drop Tables (dev only)
# ================================

async def create_all_tables() -> None:
    """
    Creates all tables defined in ORM models.
    Only used in development/testing — use Alembic in production.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """
    Drops all tables. Used in test teardown only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)