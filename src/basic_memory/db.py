"""Database configuration and initialization for basic-memory."""

from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.pool import StaticPool

from basic_memory.models import Base


class DatabaseType(Enum):
    """Types of database configurations."""

    MEMORY = "memory"  # In-memory SQLite for testing
    FILESYSTEM = "file"  # File-based SQLite for projects


def get_database_url(
    project_path: Path,
    db_type: DatabaseType,
) -> str:
    """
    Get database URL based on type and optional project path.

    Args:
        db_type: Type of database to configure
        project_path: Project directory for file-based DBs (required if type is FILESYSTEM)

    Returns:
        Database URL string

    Raises:
        ValueError: If project_path is required but not provided
    """
    match db_type:
        case DatabaseType.MEMORY:
            return "sqlite+aiosqlite:///:memory:"

        case DatabaseType.FILESYSTEM:
            if not project_path:
                raise ValueError("project_path required for filesystem database")

            # Ensure data directory exists
            data_dir = project_path / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            db_path = data_dir / "memory.db"
            return f"sqlite+aiosqlite:///{db_path}"


async def init_database(url: str, echo: bool = False) -> tuple[AsyncEngine, async_sessionmaker]:
    """
    Initialize database with schema.

    Args:
        url: Database URL
        echo: Whether to echo SQL statements

    Returns:
        Configured async engine and session factory
    """
    # Configure engine based on URL
    connect_args = {"check_same_thread": False}

    if url == "sqlite+aiosqlite:///:memory:":
        engine = create_async_engine(
            url,
            echo=echo,
            poolclass=StaticPool,  # Single connection for in-memory
            connect_args=connect_args,
        )
    else:
        engine = create_async_engine(url, echo=echo, connect_args=connect_args)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory for this engine
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    return engine, session_factory


@asynccontextmanager
async def engine_session_factory(
    project_path: Path, db_type=DatabaseType.FILESYSTEM
) -> AsyncGenerator[tuple[AsyncEngine, async_sessionmaker[AsyncSession]], None]:
    """Get database engine and session factory with proper lifecycle management."""
    url = get_database_url(project_path, db_type=db_type)
    engine, session_factory = await init_database(url)
    logger.debug(f"engine url: {engine.url}")
    try:
        yield engine, session_factory
    finally:
        await engine.dispose()


@asynccontextmanager
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with proper lifecycle management.

    Args:
        session_factory: Async session factory to create session from

    Yields:
        AsyncSession configured for engine
    """
    # Create and yield session
    session = session_factory()
    try:
        # Ensure foreign keys enabled for this session
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_database(engine: AsyncEngine):
    """
    Clean up database engine.

    Args:
        engine: Engine to dispose
    """
    await engine.dispose()
