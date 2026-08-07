"""Загрузка и проверка конфигурации без вывода секретов в логи."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Понятная пользователю ошибка конфигурации."""


def _as_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "да"}:
        return True
    if normalized in {"0", "false", "no", "нет"}:
        return False
    raise ConfigError("MOCK_MODE должен быть true или false.")


def _as_int(name: str, value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} должен быть целым числом.") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    mock_mode: bool
    telegram_bot_token: str | None
    admin_telegram_id: int | None
    target_channel_id: int | None
    openai_api_key: str | None
    openai_text_model: str
    openai_image_model: str
    database_path: Path
    log_level: str

    def validate(self, *, require_telegram: bool = True) -> None:
        if not self.mock_mode and not self.openai_api_key:
            raise ConfigError("Для реального режима заполните OPENAI_API_KEY в .env.")
        if require_telegram:
            missing = []
            if not self.telegram_bot_token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if self.admin_telegram_id is None:
                missing.append("ADMIN_TELEGRAM_ID")
            if self.target_channel_id is None:
                missing.append("TARGET_CHANNEL_ID")
            if missing:
                raise ConfigError(
                    "Заполните обязательные переменные в .env: " + ", ".join(missing)
                )


def load_settings(env_file: str | Path = ".env") -> Settings:
    load_dotenv(env_file, override=False)
    return Settings(
        mock_mode=_as_bool(os.getenv("MOCK_MODE"), default=True),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        admin_telegram_id=_as_int("ADMIN_TELEGRAM_ID", os.getenv("ADMIN_TELEGRAM_ID")),
        target_channel_id=_as_int("TARGET_CHANNEL_ID", os.getenv("TARGET_CHANNEL_ID")),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        database_path=Path(os.getenv("DATABASE_PATH", "data/travel_smm.db")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

