from typing import Sequence

from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
import uuid

from app.models import Wallet, Transaction
from app.schemas import OperationType
from app.exceptions import InsufficientFundsError, WalletNotFoundError
from app.base import BaseDAO


class WalletDAO(BaseDAO[Wallet]):
    model = Wallet

    async def create_new_wallet(self):

        # logger.info(f"Добавление записи {self.model.__name__} с параметрами: {values_dict}")
        """Создание нового кошелька"""
        try:
            new_wallet = Wallet()
            self._session.add(new_wallet)
            # logger.info(f"Запись {self.model.__name__} успешно добавлена.")
            await self._session.commit()
            await self._session.refresh(new_wallet)
            return new_wallet
        except SQLAlchemyError as e:
            # logger.error(f"Ошибка при добавлении записи: {e}")
            raise

    async def perform_operation(
        self, wallet_id: uuid.UUID, operation_type: str, amount: Decimal
    ) -> tuple[Wallet, Transaction]:
        """
        Выполнение операции над кошельком с использованием пессимистической блокировки
        для предотвращения race conditions
        """
        # Начинаем транзакцию с блокировкой строки
        async with self._session.begin_nested():
            # Получаем кошелек с блокировкой FOR UPDATE
            result = await self._session.execute(
                select(self.model).filter_by(id=wallet_id).with_for_update()
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                raise WalletNotFoundError(wallet_id=wallet_id)

            previous_balance = wallet.balance

            if operation_type == OperationType.DEPOSIT:
                new_balance = previous_balance + amount
            elif operation_type == OperationType.WITHDRAW:
                if previous_balance < amount:
                    raise InsufficientFundsError(
                        wallet_id=wallet_id,
                        current_balance=previous_balance,
                        requested_amount=amount,
                    )
                new_balance = previous_balance - amount
            else:
                raise ValueError(f"Неизвестный тип операции: {operation_type}")

            # Обновляем баланс кошелька
            wallet.balance = new_balance

            # Создаем запись о транзакции для аудита
            transaction = Transaction(
                wallet_id=wallet_id,
                operation_type=operation_type,
                amount=amount,
                previous_balance=previous_balance,
                new_balance=new_balance,
            )
            self._session.add(transaction)

            # Обновляем updated_at через триггер в БД или здесь
            await self._session.execute(
                update(Wallet)
                .where(Wallet.id == wallet_id)
                .values(updated_at=func.now())
            )

        await self._session.commit()

        # Обновляем объекты в сессии
        await self._session.refresh(wallet)
        await self._session.refresh(transaction)

        return wallet, transaction

    async def get_wallet_transactions(
        self, wallet_id: uuid.UUID, skip: int, limit: int
    ):
        """Получение истории транзакций кошелька"""
        result = await self._session.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()
