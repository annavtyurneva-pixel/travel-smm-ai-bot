import pytest

from app.services.storage import Draft, DraftStorage


@pytest.mark.asyncio
async def test_draft_survives_new_storage_instance(tmp_path):
    path = tmp_path / "drafts.db"
    first = DraftStorage(path)
    await first.initialize()
    expected = Draft(
        user_id=42, destination="Алтай", audience="семьи", post_format="гид",
        tone="живой", goal="сохранения", topic="летний маршрут",
        text="Текст", image_prompt="Промпт", image=b"png",
    )
    await first.save(expected)

    restored = await DraftStorage(path).get(42)
    assert restored == expected


@pytest.mark.asyncio
async def test_delete_removes_draft(tmp_path):
    storage = DraftStorage(tmp_path / "drafts.db")
    await storage.initialize()
    await storage.save(Draft(user_id=7, text="draft"))
    await storage.delete(7)
    assert await storage.get(7) is None

