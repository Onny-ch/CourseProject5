# Habits Tracker Backend

Backend часть SPA-приложения для отслеживания полезных привычек, реализованная на Django REST Framework.

## 📋 Содержание

- [Основные возможности](#основные-возможности)
- [Технологический стек](#технологический-стек)
- [Установка и настройка](#установка-и-настройка)
- [Запуск проекта](#запуск-проекта)
  - [Локальный запуск (без Docker)](#локальный-запуск-без-docker)
  - [Запуск с Docker](#запуск-с-docker)
- [Запуск Celery Worker и Beat](#запуск-celery-worker-и-beat)
- [API Эндпоинты](#api-эндпоинты)
- [Интеграция для фронтенд разработчиков](#интеграция-для-фронтенд-разработчиков)
- [Тестирование](#тестирование)
- [CI/CD и Деплой](#cicd-и-деплой)
- [Документация API](#документация-api)

## 🚀 Основные возможности

### Управление привычками
- ✅ CRUD-операции с привычками текущего пользователя
- ✅ Публичный каталог привычек для вдохновения
- ✅ Валидация бизнес-правил:
  - Нельзя одновременно указывать вознаграждение и связанную привычку
  - Связанной может быть только приятная привычка
  - Приятная привычка не может иметь вознаграждение или связь
  - Связанная привычка должна принадлежать пользователю

### Управление уведомлениями
- ✅ Создание уведомлений для привычек с указанием времени и периодичности
- ✅ Автоматическая отправка напоминаний через Telegram
- ✅ Поддержка различных часовых поясов
- ✅ Настройка периодичности отправки (от 1 до 7 дней)

### Аутентификация и авторизация
- ✅ Регистрация новых пользователей (через `/api/v1/auth/register/`)
- ✅ Аутентификация по токену с использованием email
- ✅ Управление профилем пользователя
- ✅ Настройка часового пояса для корректной работы уведомлений

### Интеграция с Telegram
- ✅ Отправка напоминаний через Telegram Bot API
- ✅ Автоматическая отправка уведомлений по расписанию через Celery Beat

## 🛠 Технологический стек

- **Django 5.2.8** - веб-фреймворк
- **Django REST Framework 3.16.1** - REST API
- **Celery 5.5.3** - асинхронные задачи
- **django-celery-beat 2.8.1** - планировщик задач для Celery Beat (хранение расписания в БД)
- **Redis** - брокер сообщений для Celery
- **PostgreSQL** - база данных (опционально, по умолчанию SQLite)
- **drf-yasg** - документация API (Swagger/ReDoc)
- **pytest** - тестирование

## 📦 Установка и настройка

### Требования

- Python 3.11+
- Redis (для работы Celery)
- PostgreSQL (опционально)

### Шаги установки

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Onny-ch/CourseProject5.git
cd CourseProject5
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
```

3. **Активируйте виртуальное окружение:**

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

5. **Создайте файл `.env` на основе `env.example`:**
```bash
cp env.example .env
```

6. **Настройте переменные окружения в `.env`:**
```env
# Django настройки
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# База данных (опционально, по умолчанию используется SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=habits_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# CORS (для фронтенда)
CORS_ALLOW_ALL_ORIGINS=True
# или
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

7. **Настройте базу данных PostgreSQL (опционально):**

   Если вы используете PostgreSQL, создайте базу данных:
   ```bash
   python services/create_db.py
   ```
   
   Проверьте подключение:
   ```bash
   python services/check_db.py
   ```

8. **Примените миграции:**
```bash
python manage.py migrate
```

   **Примечание:** Миграции создадут таблицы для `django-celery-beat`, которые используются для хранения расписания периодических задач в базе данных.

9. **Создайте суперпользователя (опционально):**
Данные для входа находятся по пути "users/management/commands/csu.py"
```bash
python manage.py csu
```

## 🏃 Запуск проекта

### Локальный запуск (без Docker)

#### Запуск Django сервера

```bash
python manage.py runserver
```

Сервер будет доступен по адресу: `http://localhost:8000`

#### Запуск Redis

**Windows:**
- Скачайте Redis для Windows или используйте WSL
- Запустите Redis сервер

**Linux:**
```bash
sudo systemctl start redis
# или
redis-server
```

**Mac (через Homebrew):**
```bash
brew services start redis
```

## 🔄 Запуск Celery Worker и Beat

**Примечание:** Проект использует `django-celery-beat` для хранения расписания периодических задач в базе данных. Это позволяет управлять расписанием через Django админку без перезапуска Celery Beat.

### Windows

**Важно:** На Windows Celery требует использования `--pool=solo` из-за ограничений multiprocessing.

**Worker:**
```bash
celery -A config worker --pool=solo -l info
```

**Beat (планировщик):**
```bash
celery -A config beat -l info
```

**Или запустите оба в отдельных терминалах:**
```bash
# Терминал 1 - Worker
celery -A config worker --pool=solo -l info

# Терминал 2 - Beat
celery -A config beat -l info
```

### Linux/Mac

**Worker:**
```bash
celery -A config worker -l info
```

**Beat (планировщик):**
```bash
celery -A config beat -l info
```

**Или используйте systemd для автозапуска (Linux):**

Создайте файл `/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.service

[Service]
Type=forking
User=your-user
Group=your-group
WorkingDirectory=/path/to/CourseProject5
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A config worker --loglevel=info --logfile=/var/log/celery/worker.log
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Создайте файл `/etc/systemd/system/celery-beat.service`:
```ini
[Unit]
Description=Celery Beat Service
After=network.target redis.service

[Service]
Type=simple
User=your-user
Group=your-group
WorkingDirectory=/path/to/CourseProject5
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A config beat --loglevel=info --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat
sudo systemctl start celery-worker
sudo systemctl start celery-beat
```

### Запуск с Docker

Проект полностью контейнеризирован с использованием Docker и Docker Compose. Это самый простой способ запустить все сервисы проекта.

#### Требования

- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)

#### Быстрый старт

1. **Создайте файл `.env`** на основе `env.example` и заполните необходимые переменные:

```bash
cp env.example .env
```

Убедитесь, что в `.env` указаны:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=habits_db
DB_USER=postgres
DB_PASSWORD=postgres
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

2. **Запустите все сервисы:**

```bash
docker-compose up -d
```

Эта команда запустит:
- **PostgreSQL** - база данных
- **Redis** - брокер для Celery
- **Django** - веб-приложение (Gunicorn)
- **Celery Worker** - обработчик асинхронных задач
- **Celery Beat** - планировщик задач
- **Nginx** - веб-сервер и reverse proxy

3. **Примените миграции и создайте суперпользователя:**

```bash
# Применить миграции
docker-compose exec web python manage.py migrate

# Создать суперпользователя
docker-compose exec web python manage.py csu
```

4. **Проверьте статус сервисов:**

```bash
docker-compose ps
```

#### Доступ к сервисам

- **API**: `http://localhost` (через Nginx)
- **Django Admin**: `http://localhost/admin/`
- **Swagger UI**: `http://localhost/api/docs/`
- **ReDoc**: `http://localhost/api/redoc/`

#### Полезные команды

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f celery-beat

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes (БД будет очищена!)
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache

# Выполнение команд в контейнере
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser

# Перезапуск конкретного сервиса
docker-compose restart web
docker-compose restart celery
```

#### Структура Docker контейнеров

- **web** - Django приложение (Gunicorn)
- **db** - PostgreSQL база данных
- **redis** - Redis для Celery
- **celery** - Celery Worker
- **celery-beat** - Celery Beat планировщик
- **nginx** - Nginx reverse proxy

#### Переменные окружения для Docker

Все переменные окружения читаются из файла `.env`. Docker Compose автоматически передает их в контейнеры.

#### Production режим

Для production используйте `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Production конфигурация включает:
- Больше воркеров для Gunicorn
- Оптимизированные настройки
- Отключенный DEBUG режим

## 📡 API Эндпоинты

### Базовый URL
```
http://localhost:8000/api/v1/
```

### Аутентификация

Все защищенные эндпоинты требуют токен аутентификации. Токен передается в заголовке:
```
Authorization: Token <your-token>
```

#### Регистрация пользователя
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

#### Вход (получение токена)
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

**Важно:** Авторизация выполняется по `email`, а не по `username`, так как в модели `User` используется `USERNAME_FIELD = "email"`.

### Привычки (Habits)

#### Список привычек текущего пользователя
```http
GET /api/v1/habits/
Authorization: Token <token>
```

**Ответ:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "place": "Дом",
      "action": "Зарядка",
      "is_pleasant": false,
      "related_habit": null,
      "reward": "Завтрак",
      "is_public": false,
      "created_at": "2024-01-01T09:00:00Z",
      "updated_at": "2024-01-01T09:00:00Z"
    }
  ]
}
```

#### Получение привычки
```http
GET /api/v1/habits/{id}/
Authorization: Token <token>
```

#### Создание привычки
```http
POST /api/v1/habits/
Authorization: Token <token>
Content-Type: application/json

{
  "place": "Дом",
  "action": "Зарядка",
  "is_pleasant": false,
  "reward": "Завтрак",
  "is_public": false
}
```

**Поля:**
- `place` (string, required) - место выполнения
- `action` (string, required) - действие
- `is_pleasant` (boolean, default: false) - признак приятной привычки
- `related_habit` (integer, optional) - ID связанной привычки
- `reward` (string, optional) - вознаграждение
- `is_public` (boolean, default: false) - признак публичности

**Валидация:**
- Нельзя одновременно указывать `reward` и `related_habit`
- `related_habit` должна быть приятной привычкой и принадлежать пользователю
- Приятная привычка не может иметь `reward` или `related_habit`

#### Обновление привычки
```http
PATCH /api/v1/habits/{id}/
Authorization: Token <token>
Content-Type: application/json

{
  "action": "Утренняя зарядка"
}
```

#### Удаление привычки
```http
DELETE /api/v1/habits/{id}/
Authorization: Token <token>
```

### Публичные привычки

#### Список публичных привычек
```http
GET /api/v1/public-habits/
```

**Доступно без аутентификации**

#### Получение публичной привычки
```http
GET /api/v1/public-habits/{id}/
```

### Пользователи (Users)

#### Получение профиля текущего пользователя
```http
GET /api/v1/users/me/
Authorization: Token <token>
```

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "first_name": "",
  "last_name": "",
  "avatar": null,
  "phone_number": null,
  "country": null,
  "tg_chat_id": null,
  "timezone": "UTC",
  "is_active": true,
  "date_joined": "2024-01-01T09:00:00Z",
  "last_login": null
}
```

#### Обновление профиля
```http
PATCH /api/v1/users/me/
Authorization: Token <token>
Content-Type: application/json

{
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone_number": "+79001234567",
  "country": "Россия",
  "tg_chat_id": 123456789,
  "timezone": "Europe/Moscow"
}
```

**Поля:**
- `first_name` (string, optional)
- `last_name` (string, optional)
- `phone_number` (string, optional)
- `country` (string, optional)
- `tg_chat_id` (integer, optional) - ID чата в Telegram для получения уведомлений
- `timezone` (string, optional) - часовой пояс (например, "Europe/Moscow", "UTC")

#### Полное обновление профиля
```http
PUT /api/v1/users/me/
Authorization: Token <token>
Content-Type: application/json

{
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone_number": "+79001234567",
  "country": "Россия",
  "tg_chat_id": 123456789,
  "timezone": "Europe/Moscow"
}
```

### Уведомления (Notifications)

#### Список уведомлений текущего пользователя
```http
GET /api/v1/notifications/
Authorization: Token <token>
```

**Ответ:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "habit": 1,
      "time": "09:00:00",
      "periodicity": 1,
      "execution_time": 10,
      "created_at": "2024-01-01T09:00:00Z",
      "sent_at": null,
      "is_sent": false
    }
  ]
}
```

#### Получение уведомления
```http
GET /api/v1/notifications/{id}/
Authorization: Token <token>
```

#### Создание уведомления
```http
POST /api/v1/notifications/
Authorization: Token <token>
Content-Type: application/json

{
  "habit": 1,
  "time": "09:00:00",
  "periodicity": 1,
  "execution_time": 10
}
```

**Поля:**
- `habit` (integer, required) - ID привычки (можно выбрать свою или публичную)
- `time` (time, required, format: "HH:MM:SS") - время отправки уведомления
- `periodicity` (integer, required, 1-7) - периодичность в днях (не реже 1 раза в неделю)
- `execution_time` (integer, optional, max: 120) - время для начала выполнения в секундах

**Валидация:**
- `periodicity` должна быть от 1 до 7 дней
- `execution_time` не может превышать 120 секунд
- Можно выбрать только свои привычки или публичные

#### Обновление уведомления
```http
PATCH /api/v1/notifications/{id}/
Authorization: Token <token>
Content-Type: application/json

{
  "time": "10:00:00",
  "periodicity": 2
}
```

#### Удаление уведомления
```http
DELETE /api/v1/notifications/{id}/
Authorization: Token <token>
```

#### Отправка сообщения для привычки
```http
POST /api/v1/habits/{habit_id}/send-message/
Authorization: Token <token>
```

**Требования:**
- У пользователя должен быть указан `tg_chat_id`
- Для привычки должно быть создано уведомление

**Ответ:**
```json
{
  "message": "Уведомление отправлено успешно",
  "notification_id": 1
}
```

#### Отправка уведомления
```http
POST /api/v1/notifications/{notification_id}/send/
Authorization: Token <token>
```

**Ответ:**
```json
{
  "message": "Уведомление отправлено успешно"
}
```

## 💻 Интеграция для фронтенд разработчиков

### Настройка CORS

Для работы с фронтендом убедитесь, что в `.env` настроен CORS:

```env
# Разрешить все источники (только для разработки!)
CORS_ALLOW_ALL_ORIGINS=True

# Или укажите конкретные домены
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Формат сообщений Telegram

При создании уведомления сообщение будет отправляться в формате:
```
Я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]
```

Например:
```
Я буду Зарядка в 09:00 в Дом
```

### Настройка Telegram бота

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Добавьте токен в `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   ```
4. Получите `chat_id` пользователя (можно использовать [@userinfobot](https://t.me/userinfobot))
5. Укажите `tg_chat_id` в профиле пользователя через API

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=apps --cov-report=term-missing

# С HTML отчетом
pytest --cov=apps --cov-report=html
```

Текущее покрытие: **93%**

### Структура тестов

- `apps/habits/tests.py` - тесты для привычек
- `apps/notifications/tests.py` - тесты для уведомлений
- `apps/users/tests.py` - тесты для пользователей

### Запуск тестов в Docker

```bash
# Запуск тестов в контейнере
docker-compose exec web pytest

# С покрытием кода
docker-compose exec web pytest --cov=apps --cov-report=term-missing
```

## 🚀 CI/CD и Деплой

Проект использует GitHub Actions для автоматизации CI/CD процесса.

### Настройка CI/CD

CI/CD pipeline настроен в файле `.github/workflows/ci-cd.yml` и выполняет следующие этапы:

1. **Lint and Test** - проверка кода и запуск тестов
   - Проверка кода с помощью `flake8`
   - Проверка форматирования с помощью `isort` и `black`
   - Запуск тестов с покрытием кода
   - Загрузка отчета о покрытии в Codecov

2. **Build Docker Images** - сборка Docker образов
   - Проверка возможности сборки Docker образа
   - Валидация `docker-compose.yml`

3. **Deploy** - автоматический деплой на сервер (только для веток `main`/`master`)
   - Подключение к серверу по SSH
   - Обновление кода из репозитория
   - Пересборка и перезапуск контейнеров
   - Применение миграций
   - Сбор статических файлов

### Настройка GitHub Secrets

Для работы деплоя необходимо настроить следующие секреты в настройках GitHub репозитория:

1. Перейдите в **Settings** → **Secrets and variables** → **Actions**
2. Добавьте следующие секреты:

| Secret | Описание | Пример |
|--------|----------|--------|
| `SSH_HOST` | IP адрес или домен сервера | `192.168.1.100` или `example.com` |
| `SSH_USER` | Имя пользователя для SSH | `deploy` |
| `SSH_PRIVATE_KEY` | Приватный SSH ключ | Содержимое `~/.ssh/id_rsa` |
| `SSH_PORT` | Порт SSH (опционально) | `22` |
| `DEPLOY_PATH` | Путь к проекту на сервере | `/var/www/habits-tracker` |
| `DEPLOY_URL` | URL развернутого приложения | `https://api.example.com` |

### Генерация SSH ключа для деплоя

```bash
# На локальной машине
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions_deploy

# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@your-server.com

# Добавьте приватный ключ в GitHub Secrets
cat ~/.ssh/github_actions_deploy
```

### Настройка сервера для деплоя

1. **Установите Docker и Docker Compose на сервере:**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

2. **Клонируйте репозиторий на сервер:**

```bash
cd /var/www
git clone https://github.com/Onny-ch/CourseProject5.git habits-tracker
cd habits-tracker
```

3. **Создайте файл `.env` на сервере:**

```bash
cp env.example .env
nano .env  # Заполните все необходимые переменные
```

4. **Настройте права доступа:**

```bash
sudo chown -R $USER:$USER /var/www/habits-tracker
```

5. **Настройте firewall (если используется):**

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Ручной деплой

Если автоматический деплой не настроен, можно выполнить деплой вручную:

```bash
# На сервере
cd /var/www/habits-tracker
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Мониторинг деплоя

Проверьте статус деплоя в GitHub:
- Перейдите в **Actions** в репозитории
- Выберите последний workflow run
- Просмотрите логи каждого этапа

### Откат изменений

В случае проблем после деплоя:

```bash
# На сервере
cd /var/www/habits-tracker
git checkout <previous-commit-hash>
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Документация API

### Swagger UI
```
http://localhost:8000/api/docs/
```

### ReDoc
```
http://localhost:8000/api/redoc/
```

### JSON Schema
```
http://localhost:8000/api/schema/
```

## 🔧 Дополнительные команды

### Создание миграций
```bash
python manage.py makemigrations
```

### Применение миграций
```bash
python manage.py migrate
```

### Создание суперпользователя
```bash
python manage.py createsuperuser
```

### Создание пользователя через команду
```bash
python manage.py csu
```

### Запуск Django shell
```bash
python manage.py shell
```

### Работа с базой данных PostgreSQL

**Проверка подключения к базе данных:**
```bash
python services/check_db.py
```

**Создание базы данных:**
```bash
python services/create_db.py
```

Эти скрипты автоматически проверяют настройки в `.env` и помогают настроить PostgreSQL для проекта.

## 📝 Структура проекта

```
CourseProject5/
├── apps/
│   ├── habits/          # Приложение привычек
│   │   ├── urls.py     # URL маршруты привычек
│   │   ├── views.py    # ViewSet и представления
│   │   ├── models.py   # Модели данных
│   │   ├── serializers.py  # Сериализаторы
│   │   └── tests.py    # Тесты
│   ├── notifications/   # Приложение уведомлений
│   │   ├── urls.py     # URL маршруты уведомлений
│   │   ├── views.py    # ViewSet и представления
│   │   ├── models.py   # Модели данных
│   │   ├── serializers.py  # Сериализаторы
│   │   ├── tasks.py    # Celery задачи
│   │   └── tests.py    # Тесты
│   └── users/           # Приложение пользователей
│       ├── urls.py     # URL маршруты пользователей (включая /auth/register/ и /auth/login/)
│       ├── views.py    # ViewSet, RegisterView и LoginView
│       ├── models.py   # Модели данных
│       ├── serializers.py  # Сериализаторы (включая UserLoginSerializer)
│       └── tests.py    # Тесты
├── config/              # Настройки проекта
│   ├── settings.py     # Основные настройки
│   ├── urls.py         # Главная URL конфигурация (подключает urls.py из приложений)
│   └── celery.py       # Конфигурация Celery
├── services/            # Сервисные утилиты
│   ├── check_db.py    # Скрипт проверки подключения к БД
│   └── create_db.py   # Скрипт создания базы данных
├── nginx/              # Конфигурация Nginx
│   ├── nginx.conf     # Основной конфиг Nginx
│   └── conf.d/         # Дополнительные конфигурации
│       └── default.conf # Конфигурация для Django
├── .github/            # GitHub Actions workflows
│   └── workflows/
│       └── ci-cd.yml  # CI/CD pipeline
├── manage.py           # Django management script
├── Dockerfile          # Docker образ для Django приложения
├── docker-compose.yml  # Docker Compose для разработки
├── docker-compose.prod.yml  # Docker Compose для production
├── .dockerignore       # Исключения для Docker build
├── requirements.txt    # Зависимости проекта
└── .env               # Переменные окружения (создать на основе env.example)
```

**Архитектура URL:**
- Каждое приложение имеет свой `urls.py` с маршрутами
- Главный `config/urls.py` подключает URL из всех приложений через `include()`
- Эндпоинты аутентификации (`/auth/register/`, `/auth/login/`) находятся в приложении `users`
- Это обеспечивает модульность и масштабируемость проекта

## ⚠️ Важные замечания

1. **Windows и Celery**: На Windows обязательно используйте `--pool=solo` для worker
2. **Redis**: Убедитесь, что Redis запущен перед запуском Celery
3. **django-celery-beat**: После установки зависимостей выполните миграции для создания таблиц планировщика: `python manage.py migrate`
4. **Telegram Bot**: Для работы уведомлений необходимо настроить Telegram бота
5. **CORS**: В продакшене не используйте `CORS_ALLOW_ALL_ORIGINS=True`, укажите конкретные домены
6. **Авторизация**: Авторизация выполняется по `email`, а не по `username`. Используйте `/api/v1/auth/login/` с полями `email` и `password`
7. **Регистрация**: Регистрация доступна только через `/api/v1/auth/register/`. Создание пользователей через `UserViewSet` запрещено

## 📄 Лицензия

Проект создан в рамках курсового проекта.
