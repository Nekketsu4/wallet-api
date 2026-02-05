from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.endpoints.wallets import router as wallets_router
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для управления состоянием приложения"""
    # Создание таблиц при запуске (в продакшене лучше использовать миграции)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    yield
    # Завершение приложения
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Database connections closed")

app = FastAPI(
    title="wallet API",
    description="Тестовое задание для упралвения кошельками",
    version="1.0.0",
    lifespan=lifespan,
)


# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(wallets_router, prefix="/api/v1", tags=["wallets"])


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Wallet API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}
