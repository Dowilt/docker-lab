# Docker Lab - User Management Application

Полноценное веб-приложение для управления пользователями, развёрнутое с помощью Docker Compose.

## Архитектура

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────>│   Backend    │────>│  PostgreSQL   │
│  (nginx:80)  │     │ (Flask:5000) │     │   (:5432)     │
│  port: 8080  │     │  port: 5000  │     │               │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │    Redis     │
                     │   (:6379)    │
                     └──────────────┘
```

**Сервисы:**
- **Frontend** — HTML-страница на Nginx с проксированием API-запросов к Backend
- **Backend** — Flask REST API (Python 3.11)
- **PostgreSQL** — база данных для хранения пользователей
- **Redis** — кэш для хранения статистики запросов

## Требования

- Docker Engine 20.10+
- Docker Compose v2+

## Быстрый старт

```bash
# 1. Перейти в директорию проекта
cd project

# 2. Запустить все сервисы одной командой
docker-compose up -d --build

# 3. Дождаться запуска (10-20 секунд)
docker-compose ps
```

Приложение доступно по адресу: **http://localhost:8080**

## API Endpoints

| Метод | URL           | Описание                          |
|-------|---------------|-----------------------------------|
| GET   | `/`           | Информация о приложении           |
| GET   | `/users`      | Список всех пользователей из БД   |
| POST  | `/users`      | Создание нового пользователя      |
| GET   | `/stats`      | Статистика запросов из Redis       |
| GET   | `/health`     | Проверка здоровья всех сервисов    |

## Примеры использования API

```bash
# Информация о приложении
curl http://localhost:5000/

# Получить список пользователей
curl http://localhost:5000/users

# Создать пользователя
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Oleg", "email": "oleg@example.com"}'

# Посмотреть статистику
curl http://localhost:5000/stats

# Проверка здоровья
curl http://localhost:5000/health
```

## Конфигурация

Все настройки вынесены в файл `.env`:

| Переменная     | Значение по умолчанию | Описание                |
|----------------|-----------------------|-------------------------|
| DB_NAME        | appdb                 | Имя базы данных         |
| DB_USER        | postgres              | Пользователь БД         |
| DB_PASSWORD    | secret                | Пароль БД               |
| DB_PORT        | 5432                  | Порт PostgreSQL         |
| REDIS_PORT     | 6379                  | Порт Redis              |
| BACKEND_PORT   | 5000                  | Порт Backend API        |
| FRONTEND_PORT  | 8080                  | Порт Frontend (Nginx)   |

## Управление

```bash
# Посмотреть статус сервисов
docker-compose ps

# Посмотреть логи всех сервисов
docker-compose logs

# Посмотреть логи конкретного сервиса
docker-compose logs -f backend

# Перезапустить сервисы
docker-compose restart

# Остановить все сервисы
docker-compose down

# Остановить и удалить все данные (volumes)
docker-compose down -v
```

## Персистентность данных

Данные сохраняются между перезапусками контейнеров благодаря Docker Volumes:
- `postgres_data` — данные PostgreSQL
- `redis_data` — данные Redis

Для проверки: создайте пользователя, выполните `docker-compose down && docker-compose up -d` — пользователь останется в базе.

## Структура проекта

```
project/
├── docker-compose.yml    # Оркестрация всех сервисов
├── .env                  # Переменные окружения
├── README.md             # Документация
├── backend/
│   ├── Dockerfile        # Образ для Backend
│   ├── requirements.txt  # Python-зависимости
│   └── app.py            # Flask приложение
├── frontend/
│   ├── Dockerfile        # Образ для Frontend
│   ├── nginx.conf        # Конфигурация Nginx
│   └── index.html        # HTML-страница
└── db/
    └── init.sql          # Инициализация БД (таблица users)
```

## Health Checks

Все сервисы имеют настроенные health checks:
- **PostgreSQL** — `pg_isready`
- **Redis** — `redis-cli ping`
- Backend запускается только после того, как БД и Redis будут готовы (`depends_on: condition: service_healthy`)

## Демонстрация работы

### 1. Запуск проекта

```
$ docker-compose up -d --build

 ✔ Network project_backend   Created
 ✔ Network project_frontend  Created
 ✔ Volume project_postgres_data  Created
 ✔ Volume project_redis_data     Created
 ✔ Container project-redis-1     Healthy
 ✔ Container project-db-1        Healthy
 ✔ Container project-backend-1   Started
 ✔ Container project-frontend-1  Started
```

### 2. Статус сервисов

```
$ docker-compose ps

NAME                 IMAGE                STATUS                    PORTS
project-backend-1    project-backend      Up (healthy deps)         0.0.0.0:5000->5000/tcp
project-db-1         postgres:15-alpine   Up (healthy)              0.0.0.0:5432->5432/tcp
project-frontend-1   project-frontend     Up                        0.0.0.0:8080->80/tcp
project-redis-1      redis:7-alpine       Up (healthy)              0.0.0.0:6379->6379/tcp
```

### 3. GET / — Информация о приложении

```
$ curl http://localhost:5000/

{
  "application": "Docker Lab - User Management API",
  "version": "1.0.0",
  "endpoints": {
    "GET /": "Application info",
    "GET /users": "List all users",
    "POST /users": "Create a new user (JSON: name, email)",
    "GET /stats": "Request statistics from Redis"
  }
}
```

### 4. GET /users — Список пользователей

```
$ curl http://localhost:5000/users

{
  "count": 2,
  "users": [
    {"id": 1, "name": "Admin", "email": "admin@example.com", "created_at": "2026-03-24T12:38:11"},
    {"id": 2, "name": "Test User", "email": "test@example.com", "created_at": "2026-03-24T12:38:11"}
  ]
}
```

### 5. POST /users — Создание пользователя

```
$ curl -X POST http://localhost:5000/users \
    -H "Content-Type: application/json" \
    -d '{"name": "Oleg", "email": "oleg@example.com"}'

{
  "message": "User created",
  "user": {
    "id": 3,
    "name": "Oleg",
    "email": "oleg@example.com",
    "created_at": "2026-03-24T12:40:53"
  }
}
```

### 6. GET /stats — Статистика из Redis

```
$ curl http://localhost:5000/stats

{
  "total_requests": 4,
  "get_users_requests": 1,
  "create_user_requests": 1,
  "stats_requests": 1
}
```

### 7. GET /health — Проверка здоровья сервисов

```
$ curl http://localhost:5000/health

{
  "backend": "ok",
  "database": "ok",
  "redis": "ok"
}
```

### 8. Проверка персистентности данных

```
$ docker-compose down
 ✔ Container project-frontend-1  Removed
 ✔ Container project-backend-1   Removed
 ✔ Container project-redis-1     Removed
 ✔ Container project-db-1        Removed

$ docker-compose up -d
 ✔ Container project-db-1        Healthy
 ✔ Container project-redis-1     Healthy
 ✔ Container project-backend-1   Started
 ✔ Container project-frontend-1  Started

$ curl http://localhost:5000/users

{
  "count": 3,
  "users": [
    {"id": 3, "name": "Oleg", "email": "oleg@example.com", "created_at": "2026-03-24T12:40:53"},
    {"id": 1, "name": "Admin", "email": "admin@example.com", "created_at": "2026-03-24T12:38:11"},
    {"id": 2, "name": "Test User", "email": "test@example.com", "created_at": "2026-03-24T12:38:11"}
  ]
}
```

Данные сохранились после полного перезапуска контейнеров.

### 9. Веб-интерфейс

Откройте **http://localhost:8080** в браузере — доступна HTML-страница с:
- Формой создания нового пользователя (имя + email)
- Кнопками для вызова всех API-эндпоинтов
- Таблицей пользователей из базы данных
- Панелью с JSON-ответами от API
