from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import uuid

from app import crud, schemas
from app.database import get_session
from app.exceptions import InsufficientFundsError, WalletNotFoundError

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get(
    "/{wallet_id}",
    response_model=schemas.WalletResponse,
    summary="Получить баланс кошелька",
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Кошелек не найден"}
    },
)
async def get_wallet_balance(
    wallet_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    """
    Получение текущего баланса кошелька по его UUID.
    """
    wallet = await crud.get_wallet(db, wallet_id)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кошелек с ID {wallet_id} не найден",
        )

    return wallet


@router.post(
    "/{wallet_id}/operation",
    response_model=schemas.OperationResponse,
    summary="Выполнить операцию над кошельком",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": schemas.ErrorResponse, "description": "Неверный запрос"},
        404: {"model": schemas.ErrorResponse, "description": "Кошелек не найден"},
        422: {"model": schemas.ErrorResponse, "description": "Ошибка валидации"},
    },
)
async def perform_wallet_operation(
    wallet_id: uuid.UUID,
    operation_request: schemas.OperationRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Выполнение операции пополнения (DEPOSIT) или списания (WITHDRAW) средств с кошелька.

    - **DEPOSIT**: увеличение баланса на указанную сумму
    - **WITHDRAW**: уменьшение баланса на указанную сумму (если достаточно средств)
    """
    try:
        wallet, transaction = await crud.perform_operation(
            db=db,
            wallet_id=wallet_id,
            operation_type=operation_request.operation_type,
            amount=operation_request.amount,
        )

        return schemas.OperationResponse(
            success=True,
            message=f"Операция {operation_request.operation_type} успешно выполнена",
            wallet_id=wallet_id,
            new_balance=wallet.balance,
            transaction_id=transaction.id,
        )

    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Логирование ошибки в production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.post(
    "/",
    response_model=schemas.WalletResponse,
    summary="Создать новый кошелек",
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(db: AsyncSession = Depends(get_session)):
    """
    Создание нового кошелька с нулевым балансом.
    """
    wallet = await crud.create_wallet(db)
    return wallet
