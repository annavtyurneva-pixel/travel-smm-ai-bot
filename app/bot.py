"""Точка входа. Telegram-сценарии подключаются на Этапе 3."""

from __future__ import annotations

import asyncio
import logging

from app.config import ConfigError, load_settings
from app.handlers import router
from app.middleware import AdminOnlyMiddleware
from app.services.image_service import build_image_service
from app.services.llm_service import build_llm_service
from app.services.publisher import TelegramPublisher
from app.services.storage import DraftStorage


async def main() -> None:
    settings = load_settings()
    settings.validate(require_telegram=True)
    logging.basicConfig(level=settings.log_level)
    # Импорты отложены, чтобы конфигурацию можно было тестировать отдельно.
    from aiogram import Bot, Dispatcher

    bot = Bot(token=settings.telegram_bot_token or "")
    storage = DraftStorage(settings.database_path)
    await storage.initialize()
    llm = build_llm_service(
        mock_mode=settings.mock_mode,
        api_key=settings.openai_api_key,
        model=settings.openai_text_model,
    )
    image_service = build_image_service(
        mock_mode=settings.mock_mode,
        api_key=settings.openai_api_key,
        model=settings.openai_image_model,
    )
    dispatcher = Dispatcher()
    router.message.outer_middleware(AdminOnlyMiddleware(settings.admin_telegram_id or 0))
    router.callback_query.outer_middleware(AdminOnlyMiddleware(settings.admin_telegram_id or 0))
    dispatcher.include_router(router)
    logging.getLogger(__name__).info("Travel SMM AI Assistant запущен")
    await dispatcher.start_polling(
        bot,
        storage=storage,
        llm=llm,
        image_service=image_service,
        publisher=TelegramPublisher(bot, settings.target_channel_id or 0),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ConfigError as error:
        raise SystemExit(f"Ошибка конфигурации: {error}") from error
