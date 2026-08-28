from typing import Optional
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # GREEN-API Settings (Max messenger)
    MAX_INSTANCE_ID: str = Field(
        ...,
        validation_alias=AliasChoices("MAX_INSTANCE_ID", "INSTANCE_ID"),
        description="GREEN-API instance ID",
    )
    MAX_API_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("MAX_API_TOKEN", "API_TOKEN", "GREEN_API_TOKEN"),
        description="GREEN-API API token",
    )
    MAX_TARGET_CHAT_ID: str = Field(
        ...,
        validation_alias=AliasChoices(
            "MAX_TARGET_CHAT_ID",  # Latin M
            "МAX_TARGET_CHAT_ID",  # Cyrillic М
            "TARGET_CHAT_ID",
        ),
        description="Target chat ID in Max/GREEN-API (e.g. 79990000000@c.us or group ID)",
    )
    GREEN_API_HOST: str = Field(
        "https://api.green-api.com",
        validation_alias=AliasChoices("GREEN_API_HOST", "API_HOST"),
        description="GREEN-API Host URL (or custom instance host)",
    )

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN"),
        description="Telegram bot token",
    )
    TELEGRAM_WEBHOOK_URL: str = Field(
        "",
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_URL", "WEBHOOK_URL"),
        description="Public HTTPS URL for Telegram webhook (e.g. https://your-domain.com/telegram/webhook)",
    )
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_SECRET", "WEBHOOK_SECRET"),
        description="Optional secret token for validating incoming Telegram webhooks",
    )

    # Server Settings
    WEBHOOK_HOST: str = Field("0.0.0.0", description="FastAPI host")
    WEBHOOK_PORT: int = Field(8008, description="FastAPI port")

    # Forwarding behavior
    FORWARD_SENDER_NAME: bool = Field(
        True,
        description="Whether to prepend sender name to forwarded messages",
    )
    FORWARD_MEDIA: bool = Field(
        True,
        description="Whether to download and forward media attachments (photos, documents, audio)",
    )

    @field_validator("MAX_TARGET_CHAT_ID", mode="before")
    @classmethod
    def format_target_chat_id(cls, v: str) -> str:
        if not v:
            return v
        return str(v).strip()


settings = Settings()
