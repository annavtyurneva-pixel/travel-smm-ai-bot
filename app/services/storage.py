from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import aiosqlite


@dataclass(slots=True)
class Draft:
    user_id: int
    destination: str = ""
    audience: str = ""
    post_format: str = ""
    tone: str = ""
    goal: str = ""
    topic: str = ""
    text: str = ""
    image_prompt: str = ""
    image: bytes | None = None


class DraftStorage:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    async def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    user_id INTEGER PRIMARY KEY,
                    destination TEXT NOT NULL DEFAULT '', audience TEXT NOT NULL DEFAULT '',
                    post_format TEXT NOT NULL DEFAULT '', tone TEXT NOT NULL DEFAULT '',
                    goal TEXT NOT NULL DEFAULT '', topic TEXT NOT NULL DEFAULT '',
                    text TEXT NOT NULL DEFAULT '', image_prompt TEXT NOT NULL DEFAULT '',
                    image BLOB, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def save(self, draft: Draft) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO drafts (
                    user_id, destination, audience, post_format, tone, goal,
                    topic, text, image_prompt, image, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    destination=excluded.destination, audience=excluded.audience,
                    post_format=excluded.post_format, tone=excluded.tone, goal=excluded.goal,
                    topic=excluded.topic, text=excluded.text,
                    image_prompt=excluded.image_prompt, image=excluded.image,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                draft.user_id, draft.destination, draft.audience, draft.post_format,
                draft.tone, draft.goal, draft.topic, draft.text,
                draft.image_prompt, draft.image,
            ))
            await db.commit()

    async def get(self, user_id: int) -> Draft | None:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM drafts WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
        if not row:
            return None
        return Draft(**{field: row[field] for field in Draft.__dataclass_fields__})

    async def delete(self, user_id: int) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("DELETE FROM drafts WHERE user_id = ?", (user_id,))
            await db.commit()

