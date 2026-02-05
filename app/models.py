from sqlalchemy import Column, String, Numeric, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class Wallet(Base):
    """Модель кошелька пользователя"""

    __tablename__ = "wallets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )
    balance = Column(Numeric(precision=20, scale=2), nullable=False, default=0.00)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Проверка, что баланс не может быть отрицательным
    __table_args__ = (
        CheckConstraint("balance >= 0", name="non_negative_balance"),
        Index("ix_wallets_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Wallet(id={self.id}, balance={self.balance})>"


class Transaction(Base):
    """Модель транзакции для аудита операций"""

    __tablename__ = "transactions"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    wallet_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    operation_type = Column(
        String(10),
        CheckConstraint("operation_type IN ('DEPOSIT', 'WITHDRAW')"),
        nullable=False,
    )
    amount = Column(Numeric(precision=20, scale=2), nullable=False)
    previous_balance = Column(Numeric(precision=20, scale=2), nullable=False)
    new_balance = Column(Numeric(precision=20, scale=2), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Индексы для быстрого поиска транзакций по кошельку
    __table_args__ = (
        Index("ix_transactions_wallet_id_created_at", "wallet_id", "created_at"),
        Index("ix_transactions_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Transaction(wallet_id={self.wallet_id}, operation={self.operation_type}, amount={self.amount})>"
