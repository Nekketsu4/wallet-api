import uuid
from decimal import Decimal

from loguru import logger

from app.exceptions import InsufficientFundsError
from app.schemas.wallet import OperationType


def calculate_new_balance(
    wallet_id: uuid.UUID,
    current_balance: Decimal,
    operation_type: str,
    amount: Decimal,
) -> Decimal:
    """Вычисление нового баланса с валидацией"""
    if operation_type == OperationType.DEPOSIT:
        return current_balance + amount

    elif operation_type == OperationType.WITHDRAW:
        if current_balance < amount:
            raise InsufficientFundsError(
                wallet_id=wallet_id,
                current_balance=current_balance,
                requested_amount=amount,
            )
        withdraw = current_balance - amount
        logger.debug(f"Списание средств выполнено успешно")
        return withdraw

    else:
        logger.error(f"Неизвестный тип операции: {operation_type}")
        raise ValueError(f"Неизвестный тип операции: {operation_type}")
