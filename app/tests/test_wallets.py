import pytest
from httpx import AsyncClient
import uuid

from app.main import app


@pytest.mark.asyncio
class TestWalletAPI:
    """Тесты для API кошельков"""

    async def test_create_wallet(self, db_session):
        """Тест создания кошелька"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/wallets/")

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["balance"] == "0.00"
            assert "created_at" in data
            assert "updated_at" in data

    async def test_get_existing_wallet(self, db_session):
        """Тест получения существующего кошелька"""
        # Сначала создаем кошелек
        async with AsyncClient(app=app, base_url="http://test") as client:
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            # Получаем кошелек
            get_response = await client.get(f"/api/v1/wallets/{wallet_id}")

            assert get_response.status_code == 200
            data = get_response.json()
            assert data["id"] == str(wallet_id)
            assert data["balance"] == "0.00"

    async def test_get_nonexistent_wallet(self, db_session):
        """Тест получения несуществующего кошелька"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            non_existent_id = uuid.uuid4()
            response = await client.get(f"/api/v1/wallets/{non_existent_id}")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    async def test_deposit_operation(self, db_session):
        """Тест операции пополнения"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Создаем кошелек
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            # Пополняем на 1000
            operation_data = {"operation_type": "DEPOSIT", "amount": 1000.00}

            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation", json=operation_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["wallet_id"] == str(wallet_id)
            assert data["new_balance"] == "1000.00"

            # Проверяем, что баланс изменился
            get_response = await client.get(f"/api/v1/wallets/{wallet_id}")
            wallet_data = get_response.json()
            assert wallet_data["balance"] == "1000.00"

    async def test_withdraw_operation_success(self, db_session):
        """Тест успешного списания средств"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Создаем кошелек с балансом
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            # Пополняем
            await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": 1000.00},
            )

            # Списание 500
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": 500.00},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["new_balance"] == "500.00"

    async def test_withdraw_operation_insufficient_funds(self, db_session):
        """Тест списания при недостатке средств"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Создаем кошелек с балансом 100
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": 100.00},
            )

            # Пытаемся списать 200
            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": 200.00},
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Недостаточно средств" in data["detail"]

    async def test_concurrent_deposits(self, db_session):
        """Тест конкурентных пополнений одного кошелька"""
        import asyncio

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Создаем кошелек
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            # Функция для пополнения
            async def make_deposit(amount):
                response = await client.post(
                    f"/api/v1/wallets/{wallet_id}/operation",
                    json={"operation_type": "DEPOSIT", "amount": float(amount)},
                )
                return response.json()["new_balance"]

            # Создаем 10 конкурентных запросов на пополнение
            amounts = [10.00] * 10
            tasks = [make_deposit(amount) for amount in amounts]
            results = await asyncio.gather(*tasks)

            # Все запросы должны были выполниться успешно
            # Финальный баланс должен быть 100.00 (10 * 10)
            final_balance_response = await client.get(f"/api/v1/wallets/{wallet_id}")
            final_balance = final_balance_response.json()["balance"]

            assert final_balance == "100.00"

    async def test_invalid_operation_type(self, db_session):
        """Тест неверного типа операции"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            # вводим несуществующий тип операции
            operation_data = {"operation_type": "INVALID", "amount": 100.00}

            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation", json=operation_data
            )

            assert response.status_code == 422  # Ошибка валидации

    async def test_negative_amount(self, db_session):
        """Тест отрицательной суммы"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            operation_data = {"operation_type": "DEPOSIT", "amount": -100.00}

            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation", json=operation_data
            )

            assert response.status_code == 422  # Ошибка валидации

    async def test_zero_amount(self, db_session):
        """Тест нулевой суммы"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            create_response = await client.post("/api/v1/wallets/")
            wallet_id = create_response.json()["id"]

            operation_data = {"operation_type": "DEPOSIT", "amount": 0.00}

            response = await client.post(
                f"/api/v1/wallets/{wallet_id}/operation", json=operation_data
            )

            assert response.status_code == 422  # Ошибка валидации
