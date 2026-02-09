import json
import uuid
from typing import Optional
from functools import wraps
import redis.asyncio as redis
from loguru import logger

# Глобальный клиент Redis
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Инициализация Redis"""
    global redis_client
    try:
        redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
        await redis_client.ping()
        logger.info("Соединение с Redis выполнено успешно")
    except Exception as e:
        logger.warning(f"Redis не доступен: {e}")
        redis_client = None


async def close_redis():
    """Закрытие соединения с Redis"""
    if redis_client:
        await redis_client.close()


def cached(ttl: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)

            # Для GET /{wallet_id} - используем только wallet_id
            # wallet_id будет первым аргументом после self (если есть)
            wallet_id = None

            # Ищем wallet_id в аргументах
            for arg in args:
                if isinstance(arg, uuid.UUID):
                    wallet_id = arg
                    break

            # Если не нашли в позиционных аргументах, ищем в именованных
            if not wallet_id:
                wallet_id = kwargs.get("wallet_id")

            if not wallet_id:
                # Если не можем найти wallet_id, не кэшируем
                return await func(*args, **kwargs)

            cache_key = f"cache:wallet:{wallet_id}"

            # Проверяем кэш
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Используется кэш: {cache_key}")
                return json.loads(cached)

            # Выполняем и кэшируем
            result = await func(*args, **kwargs)

            # Сериализуем результат перед кэшированием
            if hasattr(result, "dict"):
                # Для Pydantic моделей
                serialized = result.dict()
            elif hasattr(result, "__dict__"):
                # Для обычных объектов
                serialized = vars(result)
            else:
                serialized = result

            logger.debug(f"Создаем новый кэш: {cache_key}")
            await redis_client.setex(
                cache_key, ttl, json.dumps(serialized, default=str)
            )
            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Декоратор для инвалидации кэша
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Выполняем функцию
            result = await func(*args, **kwargs)
            # Удаляем кэш по паттерну
            if redis_client:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    logger.debug(f"Кэш инвалидирован: {pattern}")
            return result

        return wrapper

    return decorator
