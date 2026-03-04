# Secure Messenger (ГОСТ)

Асинхронный защищённый мессенджер с криптографией по российским стандартам ГОСТ (pygost): подпись ГОСТ 34.10-2012, хеш Streebog 34.11-2012, шифрование ГОСТ 28147-89 (CTR).

## Стек

- **Backend**: Python 3.11, FastAPI (async), SQLAlchemy 2.0 (async), PostgreSQL, Alembic, WebSocket, JWT, bcrypt
- **Crypto**: pygost (GOST 34.10-2012, 34.11-2012, 28147-89). В Docker pygost ставится из GitHub (в PyPI пакета нет); при локальной установке: `pip install` из клона [mosquito/pygost](https://github.com/mosquito/pygost) (см. backend/Dockerfile).
- **Frontend**: HTML + Vanilla JS, fetch, WebSocket
- **Инфра**: Docker, docker-compose

## Запуск

1. Клонировать репозиторий и перейти в корень проекта (каталог с `docker-compose.yml`):
   ```bash
   cd RubinChat
   ```

2. Создать `.env` из примера и задать секреты:
   ```bash
   cp .env.example .env
   ```
   Обязательно задать:
   - `SECRET_KEY` — для JWT (например: `openssl rand -hex 32`)
   - `MASTER_KEY` — 64 hex-символа (32 байта) для шифрования ключей пользователей: `openssl rand -hex 32`

3. Собрать и запустить сервисы:
   ```bash
   docker-compose up --build
   ```

4. Применить миграции (в отдельном терминале, после старта postgres и backend):
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. Открыть в браузере: http://localhost:8000  
   (Frontend раздаётся тем же backend; логин/регистрация на главной, затем чат.)

## Примеры API

Базовый URL: `http://localhost:8000/api` (если без прокси).

### Регистрация
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
```

### Вход
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
# В ответе: {"access_token": "...", "token_type": "bearer"}
```

### Текущий пользователь
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/users/me
```

### Список пользователей
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/users
```

### Отправка сообщения
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"receiver_id": "<UUID_ПОЛУЧАТЕЛЯ>", "payload": "Текст сообщения"}'
```

### Получение сообщений (диалог с пользователем)
```bash
curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/messages?with_user=<UUID>"
```

### WebSocket (уведомления о новых сообщениях)
Подключение: `ws://localhost:8000/ws?token=<JWT>`. При появлении нового сообщения сервер шлёт JSON: `{"type": "new_message", "message_id": "...", "sender_id": "..."}`.

## Архитектура

- **Роуты** (`app/api/routes/`) только вызывают сервисы и валидируют ввод (Pydantic).
- **Сервисы** (`app/services/`) — бизнес-логика, работа с БД и вызовы `CryptoProvider`.
- **Крипто** (`app/crypto/`) — изолированный слой на pygost: генерация ключей, подпись/верификация (ГОСТ 34.10-2012), хеш (Streebog), шифрование/расшифровка (ГОСТ 28147-89 CTR). Тяжёлые операции выполняются в потоке через `asyncio.to_thread`.
- При регистрации для пользователя генерируются ключевая пара (подпись) и симметричный ключ (шифрование сообщений). Приватный ключ и симметричный ключ хранятся в БД в зашифрованном виде (мастер-ключ из `MASTER_KEY`).
- Сообщения хранятся только в зашифрованном виде; подпись и nonce — для целостности и защиты от повтора.

## Структура проекта

```
RubinChat/                 # корень проекта
├── backend/
│   ├── app/
│   │   ├── api/routes/   # REST и зависимости (deps)
│   │   ├── core/         # config, security (JWT, bcrypt)
│   │   ├── crypto/       # CryptoProvider (pygost)
│   │   ├── database/     # async engine, session
│   │   ├── models/       # User, Message
│   │   ├── schemas/      # Pydantic
│   │   ├── services/     # auth, user, message
│   │   ├── websocket/    # ConnectionManager, endpoint
│   │   └── main.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # index.html, chat.html, auth.js, chat.js, styles.css
├── docker-compose.yml
├── .env.example
└── README.md
```

## Alembic (миграции)

- Конфигурация: `backend/alembic.ini`, `backend/alembic/env.py` (async).
- Первая миграция: `backend/alembic/versions/001_initial.py`.
- Применить: `docker-compose exec backend alembic upgrade head`.
- Создать новую (из каталога backend): `alembic revision --autogenerate -m "описание"`.
