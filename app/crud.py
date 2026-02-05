from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
import uuid
from typing import Optional

from app.models import Wallet, Transaction
from app.schemas import OperationType
from app.exceptions import InsufficientFundsError, WalletNotFoundError


async def get_wallet(db: AsyncSession, wallet_id: uuid.UUID) -> Optional[Wallet]:
    """Получение кошелька по ID"""
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    return result.scalar_one_or_none()


async def create_wallet(db: AsyncSession) -> Wallet:
    """Создание нового кошелька"""
    wallet = Wallet()
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def perform_operation(
    db: AsyncSession, wallet_id: uuid.UUID, operation_type: str, amount: Decimal
) -> tuple[Wallet, Transaction]:
    """
    Выполнение операции над кошельком с использованием пессимистической блокировки
    для предотвращения race conditions
    """
    # Начинаем транзакцию с блокировкой строки
    async with db.begin_nested():
        # Получаем кошелек с блокировкой FOR UPDATE
        result = await db.execute(
            select(Wallet).where(Wallet.id == wallet_id).with_for_update()
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
        db.add(transaction)

        # Обновляем updated_at через триггер в БД или здесь
        await db.execute(
            update(Wallet).where(Wallet.id == wallet_id).values(updated_at=func.now())
        )

    await db.commit()

    # Обновляем объекты в сессии
    await db.refresh(wallet)
    await db.refresh(transaction)

    return wallet, transaction


async def get_wallet_transactions(
    db: AsyncSession, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Transaction]:
    """Получение истории транзакций кошелька"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
