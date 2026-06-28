import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.database import Base

TEST_DB_URL = "postgresql+asyncpg://realestate:realestate123@localhost:5432/taichung"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.connect() as conn:
        # Use a transaction that rolls back to avoid polluting / dropping dev data
        await conn.begin()
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as session:
            yield session
        await conn.rollback()
    await engine.dispose()
