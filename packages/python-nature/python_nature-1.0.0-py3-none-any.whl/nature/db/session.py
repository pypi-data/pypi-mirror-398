"""Session management utilities for nature database.

This module provides context managers for database sessions.
Users must initialize session factories before use.

Example:
    from nature.db.session import init_sessions, sync_session

    # Initialize once at application startup
    init_sessions(
        db_url="postgresql+psycopg2://user:pass@localhost/nature",
        async_db_url="postgresql+asyncpg://user:pass@localhost/nature"
    )

    # Use throughout your application
    with sync_session() as db:
        db.add(my_entity)
        # Auto-commits on success
"""
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Module-level session factories
# Users must call init_sessions() to initialize these
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_session_factory: sessionmaker[Session] | None = None


def init_sessions(db_url: str, async_db_url: str | None = None, echo: bool = False):
    """Initialize session factories with database URLs.

    Call this once at application startup before using any session
    context managers.

    Args:
        db_url: Synchronous database URL (e.g., postgresql+psycopg2://...)
        async_db_url: Optional async database URL (e.g., postgresql+asyncpg://...)
        echo: Whether to echo SQL statements (default: False)

    Example:
        # Sync-only setup
        init_sessions(db_url="postgresql+psycopg2://user:pass@localhost/nature")

        # Both sync and async
        init_sessions(
            db_url="postgresql+psycopg2://user:pass@localhost/nature",
            async_db_url="postgresql+asyncpg://user:pass@localhost/nature"
        )
    """
    global _async_session_factory, _sync_session_factory

    # Create sync engine and factory
    sync_engine = create_engine(db_url, echo=echo)
    _sync_session_factory = sessionmaker(
        bind=sync_engine, autoflush=False, expire_on_commit=False
    )

    # Create async engine and factory if URL provided
    if async_db_url:
        async_engine = create_async_engine(async_db_url, echo=echo)
        _async_session_factory = async_sessionmaker(
            bind=async_engine, autoflush=False, expire_on_commit=False
        )


@contextmanager
def sync_session(
    session: Session | None = None, autocommit: bool = True
) -> Generator[Session, None, None]:
    """Context manager for synchronous database sessions.

    If a session is provided, it's yielded as-is without lifecycle management.
    If no session is provided, creates a new one and manages its lifecycle.

    Args:
        session: Optional existing session (caller manages lifecycle)
        autocommit: If True and session=None, commits on success (default: True)

    Yields:
        Database session

    Raises:
        RuntimeError: If init_sessions() hasn't been called

    Example:
        # Create new session (auto-managed)
        with sync_session(autocommit=True) as db:
            db.add(entity)
            # Auto-commits on success, auto-rolls back on error

        # Use existing session (caller manages)
        with sync_session(session=existing_db) as db:
            db.add(entity)
            # Caller must commit
    """
    # If session provided, just yield it
    if session is not None:
        yield session
        return

    # Validate factory exists
    if _sync_session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_sessions() first."
        )

    # Create and manage new session
    db = _sync_session_factory()
    try:
        yield db
        if autocommit:
            db.commit()
    except:
        if autocommit:
            db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def async_session(
    session: AsyncSession | None = None, autocommit: bool = True
) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for asynchronous database sessions.

    If a session is provided, it's yielded as-is without lifecycle management.
    If no session is provided, creates a new one and manages its lifecycle.

    Args:
        session: Optional existing async session (caller manages lifecycle)
        autocommit: If True and session=None, commits on success (default: True)

    Yields:
        Async database session

    Raises:
        RuntimeError: If init_sessions() hasn't been called with async_db_url

    Example:
        # Create new session (auto-managed)
        async with async_session(autocommit=True) as db:
            db.add(entity)
            # Auto-commits on success, auto-rolls back on error

        # Use existing session (caller manages)
        async with async_session(session=existing_db) as db:
            db.add(entity)
            # Caller must commit
    """
    # If session provided, just yield it
    if session is not None:
        yield session
        return

    # Validate factory exists
    if _async_session_factory is None:
        raise RuntimeError(
            "Async session factory not initialized. "
            "Call init_sessions() with async_db_url parameter."
        )

    # Create and manage new session
    db = _async_session_factory()
    try:
        yield db
        if autocommit:
            await db.commit()
    except:
        if autocommit:
            await db.rollback()
        raise
    finally:
        await db.close()
