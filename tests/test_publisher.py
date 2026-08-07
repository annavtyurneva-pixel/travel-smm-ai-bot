import pytest

from app.services.publisher import CAPTION_LIMIT, PublishError, TelegramPublisher, short_caption, split_text


class FakeBot:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def send_photo(self, channel, photo, caption):
        if self.fail:
            raise RuntimeError("telegram unavailable")
        self.calls.append(("photo", channel, caption))

    async def send_message(self, channel, text):
        if self.fail:
            raise RuntimeError("telegram unavailable")
        self.calls.append(("message", channel, text))


def test_split_text_preserves_content():
    original = "Первый абзац\n" + "слово " * 1000
    chunks = split_text(original, limit=120)
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert "".join(" ".join(chunks).split()) == "".join(original.split())


@pytest.mark.asyncio
async def test_short_post_is_single_photo_caption():
    bot = FakeBot()
    await TelegramPublisher(bot, -1001).publish("Короткий пост", b"image")
    assert bot.calls == [("photo", -1001, "Короткий пост")]


@pytest.mark.asyncio
async def test_long_post_uses_short_caption_and_messages():
    bot = FakeBot()
    text = "Заголовок\n" + "а" * (CAPTION_LIMIT + 10)
    await TelegramPublisher(bot, -1001).publish(text, b"image")
    assert bot.calls[0] == ("photo", -1001, "Заголовок")
    assert bot.calls[1][0] == "message"
    assert bot.calls[1][2] == text


@pytest.mark.asyncio
async def test_publish_error_is_safe():
    with pytest.raises(PublishError, match="права бота"):
        await TelegramPublisher(FakeBot(fail=True), -1001).publish("Пост", None)


def test_short_caption_does_not_exceed_limit():
    assert len(short_caption("а" * 500, limit=30)) == 30

