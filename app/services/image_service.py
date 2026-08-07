from __future__ import annotations

import asyncio
import base64
import struct
import zlib
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.services.llm_service import AIServiceError


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def _make_mock_png(width: int = 512, height: int = 512) -> bytes:
    """Создаёт без Pillow корректную цветную PNG-заглушку для Telegram."""
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    # Тёплый бирюзовый фон; один фильтр-байт на строку.
    row = b"\x00" + bytes((38, 166, 154)) * width
    pixels = zlib.compress(row * height, level=9)
    return signature + _png_chunk(b"IHDR", header) + _png_chunk(b"IDAT", pixels) + _png_chunk(b"IEND", b"")


_MOCK_PNG = _make_mock_png()


class ImageService(Protocol):
    async def generate(self, prompt: str) -> bytes: ...


class MockImageService:
    async def generate(self, prompt: str) -> bytes:
        if not prompt.strip():
            raise AIServiceError("Промпт изображения не может быть пустым.")
        return _MOCK_PNG


class OpenAIImageService:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, timeout=90.0, max_retries=2)
        self.model = model

    async def generate(self, prompt: str) -> bytes:
        try:
            response = await asyncio.wait_for(
                self.client.images.generate(model=self.model, prompt=prompt, size="1024x1024"),
                timeout=120,
            )
            encoded = response.data[0].b64_json if response.data else None
        except Exception as exc:
            raise AIServiceError("Сервис изображений временно недоступен. Попробуйте ещё раз.") from exc
        if not encoded:
            raise AIServiceError("Генератор не вернул изображение.")
        return base64.b64decode(encoded)


def build_image_service(*, mock_mode: bool, api_key: str | None, model: str) -> ImageService:
    if mock_mode:
        return MockImageService()
    if not api_key:
        raise AIServiceError("Для реального режима не задан OPENAI_API_KEY.")
    return OpenAIImageService(api_key, model)


def save_image(data: bytes, directory: str | Path = "data/generated") -> Path:
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4().hex}.png"
    path.write_bytes(data)
    return path
