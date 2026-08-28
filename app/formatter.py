from typing import Any, Dict, Optional
from app.config import settings


def get_sender_name(from_user: Optional[Dict[str, Any]], chat: Optional[Dict[str, Any]] = None) -> str:
    """Extracts a human-readable display name for the message author."""
    if from_user:
        first_name = from_user.get("first_name", "")
        last_name = from_user.get("last_name", "")
        username = from_user.get("username", "")

        full_name = f"{first_name} {last_name}".strip()
        if full_name and username:
            return f"{full_name} (@{username})"
        elif full_name:
            return full_name
        elif username:
            return f"@{username}"

    if chat:
        title = chat.get("title")
        if title:
            return title

    return "Пользователь"


def format_forward_header(message: Dict[str, Any]) -> str:
    """Extracts information if the message was forwarded from another chat/channel/user."""
    forward_origin = message.get("forward_origin")
    if forward_origin:
        origin_type = forward_origin.get("type")
        if origin_type == "user":
            user = forward_origin.get("sender_user", {})
            return f"↪️ Переслано от: {get_sender_name(user)}"
        elif origin_type == "chat":
            chat = forward_origin.get("sender_chat", {})
            return f"↪️ Переслано из: {chat.get('title', 'чата')}"
        elif origin_type == "channel":
            chat = forward_origin.get("chat", {})
            return f"↪️ Переслано из канала: {chat.get('title', 'канала')}"
        elif origin_type == "hidden_user":
            name = forward_origin.get("sender_user_name", "Скрытый пользователь")
            return f"↪️ Переслано от: {name}"

    if "forward_from" in message:
        return f"↪️ Переслано от: {get_sender_name(message['forward_from'])}"
    if "forward_from_chat" in message:
        return f"↪️ Переслано из: {message['forward_from_chat'].get('title', 'чата')}"

    return ""


def format_reply_header(reply_to: Optional[Dict[str, Any]]) -> str:
    """Formats reply quote preview if this message is a reply."""
    if not reply_to:
        return ""

    author = get_sender_name(reply_to.get("from"), reply_to.get("chat"))
    text = reply_to.get("text") or reply_to.get("caption") or "[вложение]"
    preview = text.strip().replace("\n", " ")
    if len(preview) > 50:
        preview = preview[:47] + "..."

    return f"💬 В ответ на ({author}: «{preview}»)"


def format_message_text(message: Dict[str, Any]) -> str:
    """Builds clean, clearly formatted text with bot branding and author name."""
    sender_name = get_sender_name(message.get("from"), message.get("chat"))
    forward_prefix = format_forward_header(message)
    reply_prefix = format_reply_header(message.get("reply_to_message"))

    content = (message.get("text") or message.get("caption") or "").strip()

    header_elements = []
    if settings.FORWARD_HEADER_PREFIX:
        header_elements.append(settings.FORWARD_HEADER_PREFIX)
    if settings.FORWARD_SENDER_NAME:
        header_elements.append(f"👤 {sender_name}")

    header_line = " | ".join(header_elements) if header_elements else ""

    lines = []
    if header_line:
        lines.append(header_line)

    if forward_prefix:
        lines.append(forward_prefix)

    if reply_prefix:
        lines.append(reply_prefix)

    if header_line or forward_prefix or reply_prefix:
        lines.append("──────────────────────")

    if content:
        lines.append(content)

    return "\n".join(lines)
