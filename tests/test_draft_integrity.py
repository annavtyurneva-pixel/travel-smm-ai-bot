import pytest

from app.services.storage import Draft, DraftStorage


@pytest.mark.asyncio
async def test_replacing_text_preserves_image(tmp_path):
    storage = DraftStorage(tmp_path / "db.sqlite")
    await storage.initialize()
    draft = Draft(user_id=1, text="old", image=b"image")
    await storage.save(draft)
    draft.text = "new"
    await storage.save(draft)
    restored = await storage.get(1)
    assert restored.text == "new"
    assert restored.image == b"image"


@pytest.mark.asyncio
async def test_replacing_image_preserves_text(tmp_path):
    storage = DraftStorage(tmp_path / "db.sqlite")
    await storage.initialize()
    draft = Draft(user_id=1, text="post", image=b"old")
    await storage.save(draft)
    draft.image = b"new"
    await storage.save(draft)
    restored = await storage.get(1)
    assert restored.text == "post"
    assert restored.image == b"new"

