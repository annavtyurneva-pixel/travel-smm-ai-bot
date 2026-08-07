from __future__ import annotations

from typing import Protocol

from aiogram.types import BufferedInputFile


CAPTION_LIMIT = 1024
MESSAGE_LIMIT = 4096


class PublishError(RuntimeError):
    pass


def split_text(text: str, limit: int = MESSAGE_LIMIT) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    while len(text) > limit:
        position = text.rfind("\n", 0, limit + 1)
        if position < limit // 2:
            position = text.rfind(" ", 0, limit + 1)
        if position < limit // 2:
            position = limit
        chunks.append(text[:position].strip())
        text = text[position:].strip()
    if text:
        chunks.append(text)
    return chunks


def short_caption(text: str, limit: int = 220) -> str:
    heading = text.strip().splitlines()[0] if text.strip() else "Новая публикация"
    return heading if len(heading) <= limit else heading[: limit - 1].rstrip() + "…"


class TelegramPublisher:
    def __init__(self, bot, channel_id: int) -> None:
        self.bot = bot
        self.channel_id = channel_id

    async def publish(self, text: str, image: bytes | None) -> None:
        if not text.strip():
            raise PublishError("Нельзя опубликовать пустой текст.")
        try:
            if image and len(text) <= CAPTION_LIMIT:
                await self.bot.send_photo(
                    self.channel_id, BufferedInputFile(image, filename="travel-post.png"),
                    caption=text,
                )
            elif image:
                await self.bot.send_photo(
                    self.channel_id, BufferedInputFile(image, filename="travel-post.png"),
                    caption=short_caption(text),
                )
                for chunk in split_text(text):
                    await self.bot.send_message(self.channel_id, chunk)
            else:
                for chunk in split_text(text):
                    await self.bot.send_message(self.channel_id, chunk)
        except Exception as exc:
            raise PublishError(
                "Не удалось опубликовать пост. Проверьте права бота в канале и повторите попытку."
            ) from exc

