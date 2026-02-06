from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncAttrs,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True


# Создание асинхронного движка базы данных
engine = create_async_engine(
    url=settings.get_db,
    echo=True if settings.DEBUG else False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
