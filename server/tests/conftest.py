"""
Pytest configuration and shared fixtures for Clash Royale tests.

Provides:
- Database session with transaction rollback isolation
- FastAPI test client
- Supercell API client with real API calls
- Common test constants and fixtures
"""

import asyncio
import os
from typing import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.database import get_db
from app.services.cr_api import CRApiClient
from main import app

# Load test environment
load_dotenv(".env.test", override=True)

# Test constants
TEST_PLAYER_TAG = "#GGCQ2PJV"  # A real, stable test player tag
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clashroyale_test",
)


async def _ensure_test_database_exists(database_url: str) -> None:
    """Create the test database when missing so tests can run in isolation."""
    url = make_url(database_url)
    db_name = url.database
    admin_db = "postgres"

    conn = await asyncpg.connect(
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        database=admin_db,
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Create a test database engine."""
    await _ensure_test_database_exists(TEST_DATABASE_URL)

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Teardown: Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session with automatic rollback."""
    session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def cr_api_client() -> AsyncGenerator[CRApiClient, None]:
    """Provide the real Clash Royale API client."""
    client = CRApiClient()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing FastAPI endpoints."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def cleaned_db(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Database session with cleaned tables before test."""
    from app.models import Card, MetaDeck, CardSynergy, Player
    
    # Delete all records from all tables
    await db_session.execute(delete(CardSynergy))
    await db_session.execute(delete(MetaDeck))
    await db_session.execute(delete(Card))
    await db_session.execute(delete(Player))
    await db_session.commit()
    
    yield db_session


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers",
        "api: marks tests that hit the real Supercell API"
    )


# Event loop policy for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
