sudo docker compose exec app pytest app/tests/ -v
### Тестовое задание управление кошельком

Приложение имеет несколько эндпоинтов, которые:
* Создает кошелек
* Показывает баланс кошелька
* Выполняет операции списания и пополнения баланса
* Показывает историю операций

### Зависимости
* Python 3.12
* dbeaver(графический клиент для удобства работы c БД)
* docker 28.5.1 и выше
* docker-compose v2.40.2 и выше


### Установка и запуск
в .env флаг DEBUG должен быть False
1. Клонируем репозиторий
```commandline
git clone https://github.com/Nekketsu4/wallet-api.git
```
2. Переходим в папку приложения
```commandline
cd wallet-api
```
3. Создаем виртуальное окружение
```commandline
python3 -m venv venv
```
4. Активируем виртуальное окружение
```commandline
source venv/bin activate для Linux
venv\Scripts\activate для Windows
```
5. Подгружаем зависимости из requirements.txt
```commandline
pip install -r requirements.txt
```
### Запуск приложения
* Запуск БД, redis и сервиса кошелька
```commandline
sudo docker-compose -f docker-compose.yml up -d
```
* Остановка всех сервисов
```commandline
sudo docker-compose -f docker-compose.yml down
```
* Пересборка и запуск
```commandline
sudo docker-compose -f docker-compose.yml up -d --build
```
* Просмотр логов
```commandline
sudo docker-compose -f docker-compose.yml logs 
```
7. Применение миграций
```commandline
docker-compose exec app alembic upgrade head
```
* Откат миграции
```commandline
docker-compose exec app alembic downgrade
```
* Чтобы воспользоваться интерактивной документацией swagger перейдите по адресу
http://0.0.0.0:8000/docs

### Запуск тестов
в .env флаг DEBUG должен быть True
* Запуск тестовой БД и redis
```commandline
sudo docker-compose -f docker-compose-test.yml up -d
```
* Запуск тестов
```commandline
pytest -v
```
* Запуск тестов с логами
```commandline
pytest -v -s
```
* Остановка всех сервисов
```commandline
sudo docker-compose -f docker-compose-test.yml down
```
* Пересборка и запуск
```commandline
sudo docker-compose -f docker-compose-test.yml up -d --build
```
* Просмотр логов
```commandline
sudo docker-compose -f docker-compose-test.yml logs 
```

### Сценарии тестов
* test_create_wallet - создаем кошелек с нулевым балансов
* test_get_existing_wallet - делаем запрос на существующий кошелек
* test_get_nonexistent_wallet - делаем запрос на НЕ существующий кошелек
* test_deposit_operation - делаем запрос на пополнение баланса кошелька
* test_withdraw_operation_success - проверка удачного списания средств с баланса
* test_withdraw_operation_insufficient_funds - проверка, что нельзя списать деньги больше чем есть на балансе кошелька
* test_concurrent_deposits - проверка конкурентного пополнения кошелька
* test_invalid_operation_type - проверка что указан доступный тип операции(DEPOSIT, WITHDRAW)
* test_negative_amount - проверка что недопустимо запрашивать отрицательную сумму 
* test_zero_amount - проверка что недопустимо запрашивать нулевую сумму
* test_show_wallet_transactions - делаем запрос на получение списка транзакций кошелька


### Добавлены улучшения
1. Кэширование и инавлидирование эндпоинтов
2. Логирование эндпоинтов сервисов и репозиториев
3. Используется пессимистическая блокировка для операций с балансом (SELECT ... FOR UPDATE)