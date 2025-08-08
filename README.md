# Приложение для отправки заявок на транспорт

## Документация

Описание и схема БД находятся в users/myrequests/core `models.py`

## Старт проекта

Создать `.env` файл ключами 'DB_NAME','DB_USER','DB_PASSWORD','DB_HOST','DB_PORT'и заполнить их необходимыми значениями.

Установить библиотеки:
`pip install -r requirements.txt`

Активировать виртуальное окружения:
`python -m venv venv`
`cmd`
`cd venv/Scripts && activate && cd ../../ `

Накатить миграции:
`python manage.py migrate`

Создать суперпользователя для доступа к админке:
`python manage.py createsuperuser`

Запуск приложения:
`python manage.py runserver`

## Запуск тестов

## Панель администратора

`http://localhost:8000/admin/`
