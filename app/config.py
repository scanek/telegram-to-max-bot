from typing import Optional, Any
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_cyrillic_key(key: str) -> str:
    """Replaces common Cyrillic homoglyphs with Latin characters."""
    table = str.maketrans("АВЕКМНОРСТУХавекмнорстух", "ABEKMHOPCTYXabekmhopctyx")
    return key.translate(table)


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
        validation_alias=AliasChoices("MAX_INSTANCE_ID", "INSTANCE_ID", "ID_INSTANCE", "GREEN_API_INSTANCE_ID"),
        description="GREEN-API instance ID",
    )
    MAX_API_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("MAX_API_TOKEN", "API_TOKEN", "GREEN_API_TOKEN", "API_TOKEN_INSTANCE"),
        description="GREEN-API API token",
    )
    MAX_TARGET_CHAT_ID: str = Field(
        ...,
        validation_alias=AliasChoices(
            "MAX_TARGET_CHAT_ID",
            "МAX_TARGET_CHAT_ID",
            "TARGET_CHAT_ID",
            "CHAT_ID",
            "GREEN_API_CHAT_ID",
        ),
        description="Target chat ID in Max/GREEN-API (e.g. 79990000000@c.us or group ID)",
    )
    GREEN_API_HOST: str = Field(
        "https://api.green-api.com",
        validation_alias=AliasChoices("GREEN_API_HOST", "API_HOST", "HOST"),
        description="GREEN-API Host URL (or custom instance host)",
    )

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices(
            "TELEGRAM_BOT_TOKEN",
            "BOT_TOKEN",
            "TG_BOT_TOKEN",
            "TG_TOKEN",
            "TELEGRAM_TOKEN",
            "TOKEN",
            "TELEGRAM_API_TOKEN",
        ),
        description="Telegram bot token",
    )
    TELEGRAM_WEBHOOK_URL: str = Field(
        "",
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_URL", "WEBHOOK_URL", "WEBHOOK"),
        description="Public HTTPS URL for Telegram webhook (leave empty for Polling mode)",
    )
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_SECRET", "WEBHOOK_SECRET", "SECRET_TOKEN"),
        description="Optional secret token for validating incoming Telegram webhooks",
    )

    # Server Settings
    WEBHOOK_HOST: str = Field("0.0.0.0", description="FastAPI host")
    WEBHOOK_PORT: int = Field(8008, description="FastAPI port")

    # Forwarding styling and behavior
    FORWARD_HEADER_PREFIX: str = Field(
        "🤖 [Telegram-мост]",
        description="Prefix header for forwarded messages",
    )
    FORWARD_SENDER_NAME: bool = Field(
        True,
        description="Whether to prepend sender name to forwarded messages",
    )
    FORWARD_MEDIA: bool = Field(
        True,
        description="Whether to download and forward media attachments (photos, documents, audio)",
    )

    # Filtering (ignore own messages or specific users)
    IGNORE_USER_IDS: str = Field(
        "",
        description="Comma-separated Telegram user IDs to ignore (e.g. 12345678,98765432)",
    )
    IGNORE_USERNAMES: str = Field(
        "",
        description="Comma-separated Telegram usernames to ignore without @ (e.g. my_username,bot2)",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_env_dict(cls, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = {}
            for k, v in data.items():
                norm_k = normalize_cyrillic_key(k).upper()
                normalized[k] = v
                normalized[norm_k] = v
            return normalized
        return data

    @field_validator("MAX_TARGET_CHAT_ID", mode="before")
    @classmethod
    def format_target_chat_id(cls, v: str) -> str:
        if not v:
            return v
        return str(v).strip()

    def should_ignore_user(self, user_id: Optional[int], username: Optional[str]) -> bool:
        """Checks if the message author matches ignore filters."""
        if user_id and self.IGNORE_USER_IDS:
            ignored_ids = [i.strip() for i in self.IGNORE_USER_IDS.split(",") if i.strip()]
            if str(user_id) in ignored_ids:
                return True

        if username and self.IGNORE_USERNAMES:
            u_clean = username.lstrip("@").lower().strip()
            ignored_names = [n.lstrip("@").lower().strip() for n in self.IGNORE_USERNAMES.split(",") if n.strip()]
            if u_clean in ignored_names:
                return True

        return False


settings = Settings()
