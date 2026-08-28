import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel
import httpx
import uvicorn

from app.config import settings
from app.formatter import format_message_text
from app.green_api import green_api_client

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telegram-to-max")


class DirectSendRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None


async def telegram_api_call(method: str, json_data: Optional[Dict[str, Any]] = None) -> dict:
    """Helper to perform requests to Telegram Bot API."""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=json_data or {})
        response.raise_for_status()
        return response.json()


async def download_telegram_file(file_id: str) -> tuple[bytes, str]:
    """Retrieves file metadata from Telegram and downloads file bytes."""
    file_info = await telegram_api_call("getFile", {"file_id": file_id})
    file_path = file_info.get("result", {}).get("file_path")
    if not file_path:
        raise ValueError(f"Could not get file_path for file_id {file_id}")

    download_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
    file_name = file_path.split("/")[-1]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(download_url)
        resp.raise_for_status()
        return resp.content, file_name


async def register_telegram_webhook():
    """Configures Telegram Webhook on startup if URL is specified."""
    if not settings.TELEGRAM_WEBHOOK_URL:
        logger.warning("TELEGRAM_WEBHOOK_URL is not set. Webhook registration skipped.")
        return

    logger.info(f"Setting Telegram webhook to: {settings.TELEGRAM_WEBHOOK_URL}")
    payload = {
        "url": settings.TELEGRAM_WEBHOOK_URL,
        "allowed_updates": ["message", "edited_message", "channel_post"],
        "drop_pending_updates": False,
    }
    if settings.TELEGRAM_WEBHOOK_SECRET:
        payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET

    try:
        result = await telegram_api_call("setWebhook", payload)
        logger.info(f"Telegram webhook set result: {result}")
    except Exception as e:
        logger.error(f"Failed to set Telegram webhook: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Telegram -> Max forwarder service...")
    try:
        me = await telegram_api_call("getMe")
        bot_info = me.get("result", {})
        logger.info(
            f"Telegram Bot connected: @{bot_info.get('username')} (ID: {bot_info.get('id')})"
        )
    except Exception as e:
        logger.error(f"Failed to connect to Telegram Bot API with token: {e}")

    await register_telegram_webhook()
    yield
    # Shutdown
    logger.info("Shutting down service...")


app = FastAPI(
    title="Telegram to Max Forwarder",
    description="Bridge forwarding Telegram messages to Max messenger via GREEN-API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "instance_id": settings.MAX_INSTANCE_ID,
        "target_chat_id": settings.MAX_TARGET_CHAT_ID,
    }


@app.post("/api/send")
async def direct_send(req: DirectSendRequest):
    """Direct API endpoint to send a message to Max without going through Telegram."""
    target_chat = req.chat_id or settings.MAX_TARGET_CHAT_ID
    try:
        result = await green_api_client.send_message(target_chat, req.message)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


async def process_telegram_message(message: Dict[str, Any]):
    """Main routing logic for forwarding message content to GREEN-API."""
    target_chat = settings.MAX_TARGET_CHAT_ID
    formatted_text = format_message_text(message)

    # 1. Check for Photo
    if "photo" in message and settings.FORWARD_MEDIA:
        # Highest resolution photo is the last element
        photo = message["photo"][-1]
        file_id = photo.get("file_id")
        try:
            file_bytes, file_name = await download_telegram_file(file_id)
            if not file_name.endswith((".jpg", ".jpeg", ".png")):
                file_name += ".jpg"
            await green_api_client.send_file_by_upload(
                chat_id=target_chat,
                file_bytes=file_bytes,
                file_name=file_name,
                caption=formatted_text or None,
            )
            return
        except Exception as e:
            logger.error(f"Error forwarding photo: {e}")
            # Fallback to sending text if media fails
            if formatted_text:
                await green_api_client.send_message(target_chat, f"{formatted_text}\n[Ошибка загрузки фото]")
            return

    # 2. Check for Document
    if "document" in message and settings.FORWARD_MEDIA:
        doc = message["document"]
        file_id = doc.get("file_id")
        orig_name = doc.get("file_name", "document")
        try:
            file_bytes, _ = await download_telegram_file(file_id)
            await green_api_client.send_file_by_upload(
                chat_id=target_chat,
                file_bytes=file_bytes,
                file_name=orig_name,
                caption=formatted_text or None,
            )
            return
        except Exception as e:
            logger.error(f"Error forwarding document: {e}")
            if formatted_text:
                await green_api_client.send_message(target_chat, f"{formatted_text}\n[Ошибка загрузки файла {orig_name}]")
            return

    # 3. Check for Voice or Audio
    if ("voice" in message or "audio" in message) and settings.FORWARD_MEDIA:
        audio_item = message.get("voice") or message.get("audio")
        file_id = audio_item.get("file_id")
        file_name = audio_item.get("file_name", "audio.ogg" if "voice" in message else "audio.mp3")
        try:
            file_bytes, _ = await download_telegram_file(file_id)
            await green_api_client.send_file_by_upload(
                chat_id=target_chat,
                file_bytes=file_bytes,
                file_name=file_name,
                caption=formatted_text or None,
            )
            return
        except Exception as e:
            logger.error(f"Error forwarding audio/voice: {e}")
            if formatted_text:
                await green_api_client.send_message(target_chat, f"{formatted_text}\n[Голосовое сообщение/Аудио]")
            return

    # 4. Standard Text message or unsupported media fallback
    if formatted_text:
        await green_api_client.send_message(target_chat, formatted_text)
    else:
        logger.info("Message had no text or supported forwardable media. Skipped.")


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    # Validate secret token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Rejected webhook request with invalid secret token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret token"
            )

    update: Dict[str, Any] = await request.json()
    logger.info(f"Received Telegram Update ID: {update.get('update_id')}")

    message = (
        update.get("message")
        or update.get("edited_message")
        or update.get("channel_post")
    )

    if message:
        # Schedule message processing in background so webhook responds immediately to Telegram
        asyncio.create_task(process_telegram_message(message))

    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEBHOOK_HOST,
        port=settings.WEBHOOK_PORT,
        reload=False,
    )
