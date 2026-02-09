import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Transaction


class TransactionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Transaction

    async def create(
        self,
        wallet_id: uuid.UUID,
        operation_type: str,
        amount: Decimal,
        previous_balance: Decimal,
        new_balance: Decimal,
    ):
        transaction = Transaction(
            wallet_id=wallet_id,
            operation_type=operation_type,
            amount=amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def refresh_transaction(self, transaction: Transaction) -> None:
        """Обновление объекта транзакции из БД"""
        await self.session.refresh(transaction)

    async def get_list_transactions(self, wallet_id: uuid.UUID, skip: int, limit: int):
        """Получение истории транзакций кошелька"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()
