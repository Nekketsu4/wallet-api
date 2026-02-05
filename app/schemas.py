from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime
import uuid


class WalletBase(BaseModel):
    """Базовая схема кошелька"""

    id: uuid.UUID
    balance: Decimal = Field(..., ge=0, description="Баланс кошелька")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletResponse(WalletBase):
    """Схема ответа для получения кошелька"""

    pass


class OperationType:
    """Типы операций"""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    """Схема запроса для операции над кошельком"""

    operation_type: str = Field(..., description="Тип операции: DEPOSIT или WITHDRAW")
    amount: Decimal = Field(..., gt=0, description="Сумма операции")

    @field_validator("operation_type")
    def validate_operation_type(cls, v):
        if v not in [OperationType.DEPOSIT, OperationType.WITHDRAW]:
            raise ValueError("operation_type должен быть DEPOSIT или WITHDRAW")
        return v

    @field_validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("amount должен быть больше 0")
        return v

    class Config:
        json_schema_extra = {
            "example": {"operation_type": "DEPOSIT", "amount": 1000.00}
        }


class OperationResponse(BaseModel):
    """Схема ответа для операции"""

    success: bool
    message: str
    wallet_id: uuid.UUID
    new_balance: Decimal
    transaction_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Схема ответа для транзакции"""

    id: uuid.UUID
    wallet_id: uuid.UUID
    operation_type: str
    amount: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Схема ответа об ошибке"""

    detail: str
    error_code: Optional[str] = None
