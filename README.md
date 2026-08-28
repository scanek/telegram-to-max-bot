# Telegram to Max Forwarder Bot (`telegram-to-max-bot`)

Сервис-мост для автоматической пересылки сообщений и медиафайлов (фото, документы, голосовые/аудио) из Telegram-чатов в российский мессенджер **Макс** через шлюз **GREEN-API**.

---

## 🚀 Основные возможности

- **Автоматическая пересылка сообщений из Telegram в Макс**:
  - Текстовые сообщения.
  - Фотографии (в исходном/высоком качестве с сохранением подписи).
  - Документы и файлы (PDF, DOCX, архивы и т.д.).
  - Голосовые и аудиосообщения.
- **Интеллектуальное форматирование**:
  - Отображение автора сообщения (Имя, Фамилия, `@username`).
  - Поддержка цитат и ответов (Replies) с кратким превью исходного сообщения.
  - Поддержка пересланных сообщений (Forwarded from channel / user).
- **Автоматическая регистрация Webhook**:
  - При запуске сервис сам вызывает `setWebhook` в Telegram Bot API.
- **Прямой REST API (`POST /api/send`)**:
  - Позволяет отправлять сообщения в Макс напрямую из других ваших скриптов или ботов (например, из `mailru-to-telegrambot`) без прохождения через Telegram.
- **Готов к Docker**:
  - В комплекте `Dockerfile` и `docker-compose.yml`.

---

## 📋 Требования к Telegram-боту

Чтобы бот видел сообщения всех участников в групповом командном чате:

1. Откройте в Telegram диалог с **[@BotFather](https://t.me/BotFather)**.
2. Введите `/setprivacy`.
3. Выберите вашего бота (`@...`).
4. Нажмите **Disable** (это позволит боту получать все сообщения из групп, а не только адресованные ему через `/` или `@`).
5. Добавьте бота в ваш командный Telegram-чат и выдайте ему права администратора.

> **Обратите внимание:** Telegram Bot API изолирует ботов друг от друга внутри одной группы. Если в вашем чате пишет другой бот (например, почтовый сервис), настройте отправку из него напрямую через эндпоинт `POST /api/send` этого сервиса.

---

## ⚙️ Настройка окружения (`.env`)

Создайте файл `.env` (на основе `.env.example`):

```ini
# === Данные GREEN-API (для отправки в Max) ===
MAX_INSTANCE_ID=your_instance_id_here
MAX_API_TOKEN=your_api_token_here
MAX_TARGET_CHAT_ID=your_target_chat_id_here
GREEN_API_HOST=https://api.green-api.com

# === Данные Telegram-бота ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=

# === Настройки сервера ===
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8008

# === Параметры пересылки ===
FORWARD_SENDER_NAME=True
FORWARD_MEDIA=True
```

---

## 🐳 Запуск через Docker Compose

```bash
# Клонирование и переход в папку
cd telegram-to-max-bot

# Сборка и запуск в фоновом режиме
docker compose up -d --build

# Просмотр логов
docker compose logs -f
```

---

## 🌐 Пример конфигурации Nginx (Reverse Proxy + SSL)

Для домена `your-domain.com`:

```nginx
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    # SSL-сертификаты (Let's Encrypt / Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
}
```

---

## 📡 REST API Эндпоинты

### 1. Проверка работоспособности
`GET /health`
```json
{
  "status": "ok",
  "instance_id": "...",
  "target_chat_id": "..."
}
```

### 2. Прямая отправка в Макс (из любых внешних скриптов)
`POST /api/send`
```json
{
  "message": "Новое уведомление от внутренней системы",
  "chat_id": "..." // опционально, по умолчанию берется MAX_TARGET_CHAT_ID
}
```

### 3. Вебхук для Telegram
`POST /telegram/webhook` — принимает `Update` от Telegram Bot API.
