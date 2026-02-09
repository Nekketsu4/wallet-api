from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
import uuid


class TransactionResponse(BaseModel):
    """Схема ответа для транзакции"""

    id: uuid.UUID
    wallet_id: uuid.UUID
    operation_type: str
    amount: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
