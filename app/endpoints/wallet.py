import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from loguru import logger

from app import schemas
from app.database import get_async_db_session
from app.models.wallet import Transaction
from app.exceptions import InsufficientFundsError, WalletNotFoundError
from app.services.wallet import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post(
    "/",
    response_model=schemas.WalletResponse,
    summary="Создать новый кошелек",
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(db: AsyncSession = Depends(get_async_db_session)):
    """
    Создание нового кошелька с нулевым балансом.
    """
    logger.info("Создается новый кошелек")
    try:
        wallet_service: WalletService = WalletService(db)
        wallet = await wallet_service.create_new_wallet()
        logger.info(f"Кошелек с ID {wallet.id} создан успешно")
        return wallet
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Не удалось создать кошелек: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать кошелек",
        )


@router.get(
    "/{wallet_id}",
    response_model=schemas.WalletResponse,
    summary="Получить баланс кошелька",
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Кошелек не найден"}
    },
)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db_session),
):
    """
    Получение текущего баланса кошелька по его UUID.
    """
    logger.debug("Выполняется запрос на получение баланса кошелька")
    wallet_service: WalletService = WalletService(db)
    wallet = await wallet_service.get_wallet_by_id(wallet_id)
    if not wallet:
        logger.warning(f"Кошелек с ID {wallet_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кошелек с ID {wallet_id} не найден",
        )
    logger.info(f"Кошелек {wallet_id} получен. Баланс кошелька {wallet.balance}")
    return wallet


@router.get(
    "/{wallet_id}/wallet_transactions",
    response_model=list[schemas.TransactionResponse],
    summary="Показать историю операций",
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Кошелек не найден"},
    },
)
async def show_wallet_transactions(
    wallet_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_db_session),
):
    """
    Отобразить выполненные операции в текущем кошельке
    """
    wallet_service: WalletService = WalletService(session)
    wallet = await wallet_service.get_wallet_by_id(wallet_id)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кошелек с ID {wallet_id} не найден",
        )
    result: list[Transaction] = await wallet_service.get_wallet_transactions(
        wallet_id, skip, limit
    )
    if not result:
        return {"message": f"У кошелька не было выполнено еще ни одной транзакций"}

    return [
        schemas.TransactionResponse(
            id=res.id,
            wallet_id=wallet_id,
            operation_type=res.operation_type,
            amount=res.amount,
            previous_balance=res.previous_balance,
            new_balance=res.new_balance,
            created_at=res.created_at,
        )
        for res in result
    ]


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
    db: AsyncSession = Depends(get_async_db_session),
):
    """
    Выполнение операции пополнения (DEPOSIT) или списания (WITHDRAW) средств с кошелька.

    - **DEPOSIT**: увеличение баланса на указанную сумму
    - **WITHDRAW**: уменьшение баланса на указанную сумму (если достаточно средств)
    """

    logger.info(
        f"Тип операции: {operation_request.operation_type}, запрашиваемая сумма: {operation_request.amount}"
    )
    try:
        wallet_service: WalletService = WalletService(db)
        wallet, transaction = await wallet_service.perform_operation(
            wallet_id=wallet_id,
            operation_type=operation_request.operation_type,
            amount=operation_request.amount,
        )

        logger.info(
            f"Операция выполнена успешно. "
            f"Кошелек: {wallet_id}, Транзакция: {transaction.id}, "
            f"Новый баланс: {wallet.balance}"
        )
        return schemas.OperationResponse(
            success=True,
            message=f"Операция {operation_request.operation_type} успешно выполнена",
            wallet_id=wallet_id,
            new_balance=wallet.balance,
            transaction_id=transaction.id,
        )

    except WalletNotFoundError as e:
        logger.warning(f"Во время операции кошелек с ID {wallet_id} не был найден")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        logger.warning(f"Недостаточно средств для проведения операции: {wallet_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"Ошибка проверки входных данных: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Непредвиденная ошибка во время работы: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )
