"""
Database configuration and utilities for Overwatch.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DatabaseManager:
    """Database manager for Overwatch admin panel."""

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.echo = echo
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        self.engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            future=True,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            await self.initialize()

        assert self.engine is not None
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self.engine:
            await self.initialize()

        assert self.engine is not None
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            await self.initialize()

        assert self.session_factory is not None
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. Call initialize_database() first."
        )
    return _db_manager


async def initialize_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.

    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements

    Returns:
        Database manager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo)
    await _db_manager.initialize()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    db_manager = get_database_manager()
    async for session in db_manager.get_session():
        yield session
