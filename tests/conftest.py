"""Test configuration and fixtures using testcontainers."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from api.core.database import Base, get_db
from api.main import app


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Create PostgreSQL testcontainer for the entire test session."""
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    """Get database URL from testcontainer."""
    # Get the connection URL and ensure it uses asyncpg driver
    url = postgres_container.get_connection_url()
    # Replace psycopg2 driver with asyncpg
    return url.replace("psycopg2", "asyncpg")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine(database_url: str) -> AsyncGenerator[Any, None]:
    """Create async engine for tests."""
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def override_get_db(db_session: AsyncSession) -> Generator[None, None, None]:
    """Override the get_db dependency to use test database."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db: None) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(override_get_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for advanced testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
