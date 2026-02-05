from decimal import Decimal
import uuid


class WalletError(Exception):
    """Базовый класс для ошибок кошелька"""

    pass


class WalletNotFoundError(WalletError):
    """Ошибка: кошелек не найден"""

    def __init__(self, wallet_id: uuid.UUID):
        self.wallet_id = wallet_id
        super().__init__(f"Кошелек с ID {wallet_id} не найден")


class InsufficientFundsError(WalletError):
    """Ошибка: недостаточно средств"""

    def __init__(
        self, wallet_id: uuid.UUID, current_balance: Decimal, requested_amount: Decimal
    ):
        self.wallet_id = wallet_id
        self.current_balance = current_balance
        self.requested_amount = requested_amount
        super().__init__(
            f"Недостаточно средств на кошельке {wallet_id}. "
            f"Текущий баланс: {current_balance}, запрошено: {requested_amount}"
        )
