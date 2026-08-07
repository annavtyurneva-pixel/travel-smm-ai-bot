from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int) -> None:
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and user.id == self.admin_id:
            return await handler(event, data)
        if isinstance(event, Message):
            await event.answer("⛔ Доступ к боту разрешён только администратору.")
        elif isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещён", show_alert=True)
        return None

