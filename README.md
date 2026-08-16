# Foodgram

[![Foodgram workflow](https://github.com/mraksdev/foodgram/actions/workflows/foodgram_cd.yml/badge.svg)](https://github.com/mraksdev/foodgram/actions/workflows/foodgram_cd.yml)

## Описание

**Foodgram** — сервис для публикации рецептов. Проект позволяет:

- регистрироваться и авторизовываться пользователям;
- публиковать рецепты с фотографиями, тегами и списком ингредиентов;
- добавлять рецепты в избранное и в список покупок;
- подписываться на авторов и просматривать их рецепты;
- скачивать список покупок в виде текстового файла;
- делиться короткими ссылками на рецепты.

Приложение развёрнуто в Docker-контейнерах: бэкенд на Django, фронтенд на
React, Nginx выступает в роли gateway. Сборка образов, тестирование и деплой
на сервер автоматизированы с помощью GitHub Actions.

## Стек технологий

| Технология | Роль в проекте | Документация |
|---|---|---|
| Python 3.12 | Язык программирования бэкенда | [python.org](https://www.python.org/) |
| Django 5.1 | Основной фреймворк бэкенда | [djangoproject.com](https://www.djangoproject.com/) |
| Django REST Framework 3.15 | Создание API | [django-rest-framework.org](https://www.django-rest-framework.org/) |
| Djoser 2.3 | Регистрация и авторизация пользователей | [djoser.readthedocs.io](https://djoser.readthedocs.io/) |
| PostgreSQL 13 | База данных | [postgresql.org](https://www.postgresql.org/) |
| React 17 | Библиотека для создания пользовательского интерфейса | [reactjs.org](https://reactjs.org/) |
| React Router 5 | Маршрутизация во фронтенде | [reactrouter.com](https://reactrouter.com/) |
| Nginx | Веб-сервер и проксирование запросов | [nginx.org](https://nginx.org/) |
| Gunicorn | WSGI-сервер бэкенда | [gunicorn.org](https://gunicorn.org/) |
| Docker / Docker Compose | Контейнеризация приложения | [docker.com](https://www.docker.com/) |
| GitHub Actions | CI/CD: тестирование, сборка образов, деплой | [docs.github.com](https://docs.github.com/actions) |

## Установка

### Локальный запуск в контейнерах (Docker Compose)

1. Клонируйте репозиторий:

```bash
git clone git@github.com:mraksdev/foodgram.git
cd foodgram
```

2. Создайте файл `.env` в папке `infra` по образцу `infra/.env.example`:

```bash
cp infra/.env.example infra/.env
```

3. Заполните переменные окружения в `infra/.env` (обязательно смените
`SECRET_KEY` и `POSTGRES_PASSWORD`, для работы вне Docker также задайте
`ALLOWED_HOSTS`).

4. Соберите и запустите контейнеры из папки `infra`:

```bash
cd infra
docker compose up -d
```

5. Выполните миграции и загрузите теги и ингредиенты:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py import_tags
docker compose exec backend python manage.py import_ingredients
```

6. Создайте суперпользователя для админ-панели:

```bash
docker compose exec backend python manage.py createsuperuser
```

7. Приложение будет доступно по адресу `http://localhost:8080`.

### Локальный запуск без Docker

1. Установите зависимости бэкенда:

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

2. Выполните миграции и загрузите данные:

```bash
python backend/manage.py migrate
python backend/manage.py import_tags
python backend/manage.py import_ingredients
```

3. Установите зависимости фронтенда:

```bash
cd frontend
npm install
```

4. Запустите бэкенд:

```bash
cd backend
python manage.py runserver
```

5. Запустите фронтенд:

```bash
cd frontend
npm start
```

## Примеры запросов к API

Базовый URL: `https://mraksdev-foodgram.duckdns.org/api`

### Регистрация пользователя

`POST /api/users/`

```json
{
    "email": "user@example.com",
    "username": "food_lover",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "super-secret-pass"
}
```

### Получение токена авторизации

`POST /api/auth/token/login/`

```json
{
    "email": "user@example.com",
    "password": "super-secret-pass"
}
```

Ответ:

```json
{
    "auth_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

Токен передаётся в заголовке `Authorization: Token <токен>`.

### Получение списка рецептов

`GET /api/recipes/`

Пример ответа:

```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "tags": [
                {
                    "id": 1,
                    "name": "Завтрак",
                    "slug": "breakfast"
                }
            ],
            "author": {
                "id": 1,
                "username": "food_lover",
                "first_name": "Иван",
                "last_name": "Иванов",
                "email": "user@example.com",
                "is_subscribed": false,
                "avatar": null
            },
            "ingredients": [
                {
                    "id": 1123,
                    "name": "овощи",
                    "measurement_unit": "г",
                    "amount": 10
                }
            ],
            "is_favorited": false,
            "is_in_shopping_cart": false,
            "name": "Салат",
            "image": "http://localhost:8080/media/recipes/salad.jpg",
            "text": "Простой и вкусный салат",
            "cooking_time": 10
        }
    ]
}
```

### Публикация рецепта

`POST /api/recipes/`

```json
{
    "name": "Салат",
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/...",
    "text": "Простой и вкусный салат",
    "cooking_time": 10,
    "tags": [1, 2],
    "ingredients": [
        {
            "id": 1123,
            "amount": 200
        },
        {
            "id": 220,
            "amount": 2
        }
    ]
}
```

### Добавление рецепта в избранное

`POST /api/recipes/{id}/favorite/`

Удаление — `DELETE /api/recipes/{id}/favorite/`.

### Добавление рецепта в список покупок

`POST /api/recipes/{id}/shopping_cart/`

Удаление — `DELETE /api/recipes/{id}/shopping_cart/`.

### Скачивание списка покупок

`GET /api/recipes/download_shopping_cart/`

Возвращает текстовый файл `shopping_list.txt` со списком ингредиентов.

### Подписка на автора

`POST /api/users/{id}/subscribe/`

### Получение списка подписок

`GET /api/users/subscriptions/`

### Поиск ингредиентов

`GET /api/ingredients/?name=кар`

### Получение короткой ссылки на рецепт

`GET /api/recipes/{id}/get-link/`

Ответ:

```json
{
    "short-link": "http://mraksdev-foodgram.duckdns.org/s/45568d7f/"
}
```

## Автор

**Александр Крылов** — [github.com/mraksdev](https://github.com/mraksdev)
