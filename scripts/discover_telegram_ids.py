"""Безопасно показывает ID администратора и каналов из Telegram getUpdates."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Ошибка: добавьте TELEGRAM_BOT_TOKEN в локальный файл .env.")
        return 1

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/getUpdates",
        headers={"User-Agent": "Travel-SMM-AI-Assistant/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            print("Ошибка: Telegram отклонил токен. Проверьте значение в .env.")
        else:
            print(f"Ошибка Telegram API: HTTP {exc.code}.")
        return 1
    except (urllib.error.URLError, TimeoutError):
        print("Ошибка: не удалось подключиться к Telegram API. Проверьте интернет.")
        return 1

    users: dict[int, str] = {}
    channels: dict[int, str] = {}
    for update in payload.get("result", []):
        message = update.get("message") or update.get("edited_message")
        if message and message.get("chat", {}).get("type") == "private":
            chat = message["chat"]
            users[chat["id"]] = chat.get("username") or chat.get("first_name") or "без имени"
        channel_post = update.get("channel_post") or update.get("edited_channel_post")
        if channel_post:
            chat = channel_post.get("chat", {})
            if chat.get("id"):
                channels[chat["id"]] = chat.get("title", "без названия")

    if users:
        print("Найдены личные Telegram ID:")
        for identifier, name in users.items():
            print(f"  ADMIN_TELEGRAM_ID={identifier}  ({name})")
    else:
        print("Личный ID не найден: ещё раз отправьте боту /start и повторите команду.")

    if channels:
        print("Найдены Telegram-каналы:")
        for identifier, title in channels.items():
            print(f"  TARGET_CHANNEL_ID={identifier}  ({title})")
    else:
        print("ID канала не найден: опубликуйте новое сообщение после добавления бота администратором.")
    return 0 if users and channels else 2


if __name__ == "__main__":
    sys.exit(main())

