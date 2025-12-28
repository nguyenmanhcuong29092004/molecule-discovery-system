"""
Database Session Configuration

Provides async database session and engine configuration.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://moldb:1@postgres:5432/molecule_discovery",
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        ```python
        async with get_db() as session:
            result = await session.execute(select(Run))
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    
    Note: In production, use Alembic migrations instead.
    """
    from app.db.base import Base
    from app.db.models import Run, Molecule, Trace  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data!
    Use only in development/testing.
    """
    from app.db.base import Base
    from app.db.models import Run, Molecule, Trace  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)