"""Database management for Polymarket Fetcher."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..models.market import Base


class DatabaseManager:
    """Database manager for SQLite database operations.

    Supports both synchronous and asynchronous operations.
    """

    def __init__(self, db_path: str, pool_size: int = 5, async_mode: bool = False):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
            pool_size: Connection pool size.
            async_mode: Whether to use async mode.
        """
        self.db_path = Path(db_path)
        self._async_mode = async_mode

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engines
        if async_mode:
            self._sync_engine = create_engine(
                f"sqlite:///{self.db_path}",
                pool_size=pool_size,
                echo=False,
            )
            self._async_engine = create_async_engine(
                f"sqlite+aiosqlite:///{self.db_path}",
                pool_size=pool_size,
                echo=False,
            )
            self._session_factory = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        else:
            self._sync_engine = create_engine(
                f"sqlite:///{self.db_path}",
                pool_size=pool_size,
                echo=False,
            )
            self._session_factory = sessionmaker(
                self._sync_engine,
                expire_on_commit=False,
            )

    @property
    def is_async(self) -> bool:
        """Check if the database is in async mode."""
        return self._async_mode

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self._sync_engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(self._sync_engine)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session context manager.

        Yields:
            AsyncSession instance.
        """
        if not self._async_mode:
            raise RuntimeError("Database is not in async mode")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_session(self):
        """Get a sync session (for sync operations)."""
        return self._session_factory()

    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Query result.
        """
        if self._async_mode:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        else:
            with self._sync_engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                conn.commit()
                return result

    def vacuum(self) -> None:
        """Run VACUUM to optimize the database."""
        with self._sync_engine.connect() as conn:
            conn.execute(text("VACUUM"))
            conn.commit()

    async def close(self) -> None:
        """Close all connections."""
        if self._async_mode and self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


class AsyncDatabaseManager(DatabaseManager):
    """Async database manager for SQLite operations."""

    def __init__(self, db_path: str, pool_size: int = 5):
        """Initialize the async database manager.

        Args:
            db_path: Path to the SQLite database file.
            pool_size: Connection pool size.
        """
        super().__init__(db_path, pool_size, async_mode=True)


def create_database(
    db_path: str,
    pool_size: int = 5,
    create_tables: bool = True,
) -> DatabaseManager:
    """Create and initialize a database manager.

    Args:
        db_path: Path to the SQLite database file.
        pool_size: Connection pool size.
        create_tables: Whether to create tables on initialization.

    Returns:
        DatabaseManager instance.
    """
    manager = DatabaseManager(db_path, pool_size)
    if create_tables:
        manager.create_tables()
    return manager


async def create_async_database(
    db_path: str,
    pool_size: int = 5,
    create_tables: bool = True,
) -> AsyncDatabaseManager:
    """Create and initialize an async database manager.

    Args:
        db_path: Path to the SQLite database file.
        pool_size: Connection pool size.
        create_tables: Whether to create tables on initialization.

    Returns:
        AsyncDatabaseManager instance.
    """
    manager = AsyncDatabaseManager(db_path, pool_size)
    if create_tables:
        manager.create_tables()
    return manager
