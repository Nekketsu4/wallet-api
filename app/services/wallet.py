import uuid
from decimal import Decimal

from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import WalletNotFoundError
from app.repository.wallet import WalletRepository
from app.repository.transaction import TransactionRepository
from app.models.wallet import Wallet, Transaction
from app.utils.wallet import calculate_new_balance


class WalletService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_repo: WalletRepository = WalletRepository(session)
        self.transaction_repo: TransactionRepository = TransactionRepository(session)

    async def create_new_wallet(self):
        new_wallet = Wallet()
        return await self.wallet_repo.add(new_wallet)

    async def get_wallet_by_id(self, wallet_id: uuid.UUID):
        wallet = await self.wallet_repo.find_one_or_none_by_id(wallet_id)
        return wallet

    async def perform_operation(
        self, wallet_id: uuid.UUID, operation_type: str, amount: Decimal
    ) -> tuple[Wallet, Transaction]:
        """
        Выполнение операции над кошельком с использованием пессимистической блокировки
        для предотвращения race conditions
        """
        async with self.session.begin():
            # Получаем кошелек с блокировкой FOR UPDATE
            wallet = await self.wallet_repo.get_with_lock(wallet_id)

            if not wallet:
                raise WalletNotFoundError(wallet_id=wallet_id)

            # Обновляем баланс в БД
            logger.debug(f"Обновляем баланс кошелька с ID {wallet_id}")
            new_balance = calculate_new_balance(
                wallet_id, wallet.balance, operation_type, amount
            )

            await self.wallet_repo.update_balance(wallet_id)

            # Создаем запись о транзакции
            transaction = await self.transaction_repo.create(
                wallet_id=wallet_id,
                operation_type=operation_type,
                amount=amount,
                previous_balance=wallet.balance,
                new_balance=new_balance,
            )

            # Обновляем объекты в сессии
            await self.wallet_repo.refresh_wallet(wallet)
            await self.transaction_repo.refresh_transaction(transaction)

            # Обновляем баланс кошелька
            logger.debug(
                f"Кошелек: {wallet_id}, Запрошенная сумма: {amount}, "
                f"Предыдущий баланс: {wallet.balance}, "
                f"Текущий баланс: {new_balance}"
            )
            wallet.balance = new_balance

        return wallet, transaction

    async def get_wallet_transactions(
        self,
        wallet_id: uuid.UUID,
        skip: int,
        limit: int,
    ):
        """
        Получить список транзакций
        """
        transactions = await self.transaction_repo.get_list_transactions(
            wallet_id=wallet_id, skip=skip, limit=limit
        )
        return transactions
