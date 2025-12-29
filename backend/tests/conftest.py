"""
Pytest Configuration and Fixtures

Provides test fixtures for unit and integration tests.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to Python path
backend_dir = Path(__file__).parent
app_dir = backend_dir / "app"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(app_dir))

from app.db import Base
from app.main import app

# Test database URL
TEST_DATABASE_URL = (
    "postgresql+asyncpg://moldb:1@postgres:5432/molecule_discovery_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    
    Scope: session - one loop for all tests.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create test database engine.
    
    Creates all tables at session start, drops them at session end.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.
    
    Scope: function - new session for each test.
    Truncates all tables after each test for isolation.
    """
    from app.db.models import Run, Molecule, Trace
    
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        
        # Clean up: truncate all tables after test
        try:
            # If session has pending rollback (e.g., from constraint error),
            # rollback first before truncating
            await session.rollback()
            await session.execute(
                text("TRUNCATE TABLE traces, molecules, runs RESTART IDENTITY CASCADE")
            )
            await session.commit()
        except Exception:
            # If cleanup fails, rollback
            await session.rollback()


@pytest_asyncio.fixture
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Alias for db_session - used by test_api_results.py
    
    Scope: function - new session for each test.
    Truncates all tables after each test for isolation.
    """
    from app.db.models import Run, Molecule, Trace
    
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as sess:
        yield sess
        
        # Clean up: truncate all tables after test
        try:
            # If session has pending rollback (e.g., from constraint error),
            # rollback first before truncating
            await sess.rollback()
            await sess.execute(
                text("TRUNCATE TABLE traces, molecules, runs RESTART IDENTITY CASCADE")
            )
            await sess.commit()
        except Exception:
            # If cleanup fails, rollback
            await sess.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing API.
    
    Overrides the database dependency to use test database.
    """
    from app.db.session import get_db

    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()