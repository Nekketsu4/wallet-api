import uuid
from decimal import Decimal
from typing import Optional

from loguru import logger

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet


class WalletRepository:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Wallet

    async def add(self, instance):
        try:
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Ошибка базы данных во время работы: {e}", exc_info=True)
            await self.session.rollback()
            raise

    async def find_one_or_none_by_id(self, wallet_id: uuid.UUID):
        query = select(self.model).filter_by(id=wallet_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_lock(self, wallet_id: uuid.UUID) -> Optional[Wallet]:
        query = select(self.model).filter_by(id=wallet_id).with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_balance(self, wallet_id: uuid.UUID) -> None:
        try:
            await self.session.execute(
                update(self.model)
                .where(self.model.id == wallet_id)
                .values(updated_at=func.now()),
            )
        except SQLAlchemyError as e:
            logger.error(f"Ошибка базы данных во время работы: {e}", exc_info=True)
            await self.session.rollback()
            raise

    async def refresh_wallet(self, wallet: Wallet) -> None:
        """Обновление объекта кошелька из БД"""
        await self.session.refresh(wallet)
