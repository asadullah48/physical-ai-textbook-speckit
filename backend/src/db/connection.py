"""Database connection management using asyncpg and SQLAlchemy."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.config import get_settings

# Global engine and session factory (initialized lazily)
_engine = None
_session_factory = None


def get_engine():
    """Get or create the async database engine.

    Returns:
        AsyncEngine instance configured for the application.
    """
    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.async_database_url,
            pool_size=settings.db_pool_min_size,
            max_overflow=settings.db_pool_max_size - settings.db_pool_min_size,
            pool_timeout=settings.db_connection_timeout,
            pool_recycle=300,  # Recycle connections every 5 minutes
            pool_pre_ping=True,  # Check connection health before use
            echo=settings.debug,  # Log SQL in debug mode
            connect_args={
                "ssl": "require",  # Required for Neon
                "server_settings": {
                    "application_name": "physical-ai-textbook",
                },
            },
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory.

    Returns:
        AsyncSessionmaker instance for creating database sessions.
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Yields:
        AsyncSession instance for database operations.

    Note:
        The session is automatically committed on success
        and rolled back on exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions.

    Yields:
        AsyncSession instance for database operations.

    Note:
        Use this for operations outside of FastAPI request handlers.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """Check if the database connection is working.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


async def close_database() -> None:
    """Close the database engine and connection pool.

    Note:
        Call this during application shutdown.
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
