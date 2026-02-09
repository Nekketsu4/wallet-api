from contextlib import asynccontextmanager

from loguru import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.endpoints.wallet import router as wallets_router
from app.cache.cache_redis import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для управления состоянием приложения"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.success("Соединение с БД выполнено успешно")
        logger.success("Запущена работа приложения")
        await init_redis()
    except Exception as e:
        logger.error(f"Не удалось подключиться к БД: {e}")
        raise

    yield
    logger.info("Завершена работа приложения...")
    await close_redis()
    await engine.dispose()
    logger.info("Соединение с БД закрыто")


app = FastAPI(
    title="wallet API",
    description="Тестовое задание для упралвения кошельками",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    health = {
        "status": "healthy",
        "redis": "connected" if await _check_redis() else "disconnected",
    }
    return {"status": "healthy"}


async def _check_redis() -> bool:
    """Проверка доступности Redis"""
    from app.cache.cache_redis import redis_client

    if not redis_client:
        return False
    try:
        await redis_client.ping()
        return True
    except:
        return False
