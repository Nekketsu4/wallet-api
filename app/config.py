import os
from loguru import logger

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # БД
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int

    # Путь к тестоовому БД
    TEST_DB_URL: str

    # Логирование
    FORMAT_LOG: str
    LOG_ROTATION: str

    # Настройки безопасности
    SECRET_KEY: str
    ALGORITHM: str

    # Настройки приложения
    DEBUG: bool
    PROJECT_NAME: str
    VERSION: str

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DECODE_RESPONSE: bool

    @property
    def get_db(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )


settings = Settings()


# Настройка логирования
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs.log.txt")
logger.add(
    log_file_path,
    format=settings.FORMAT_LOG,
    level="INFO",
    rotation=settings.LOG_ROTATION,
)
