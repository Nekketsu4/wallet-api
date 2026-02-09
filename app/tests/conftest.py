import pytest
import asyncio
from typing import AsyncGenerator

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_async_db_session
from app.main import app
from app.config import settings

test_engine = create_async_engine(
    settings.TEST_DB_URL,
    # connect_args={"check_same_thread": False},
    poolclass=NullPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncSession:
    """Переопределенная зависимость для тестовой БД"""
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_async_db_session] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Фикстура для event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Создание и очистка тестовой БД для каждого теста"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД"""
    async with TestingSessionLocal() as session:
        yield session
