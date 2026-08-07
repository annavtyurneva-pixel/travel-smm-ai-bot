from types import SimpleNamespace

import pytest
from aiogram.types import TelegramObject

from app.handlers.content import _valid
from app.middleware import AdminOnlyMiddleware


@pytest.mark.parametrize("value", [None, "", " ", "a", "x" * 201])
def test_invalid_brief_input_is_rejected(value):
    assert _valid(value) is None


def test_valid_brief_input_is_trimmed():
    assert _valid("  Казань  ") == "Казань"


@pytest.mark.asyncio
async def test_admin_is_allowed():
    called = False

    async def handler(event, data):
        nonlocal called
        called = True
        return "ok"

    middleware = AdminOnlyMiddleware(42)
    result = await middleware(handler, TelegramObject(), {"event_from_user": SimpleNamespace(id=42)})
    assert called is True
    assert result == "ok"


@pytest.mark.asyncio
async def test_outsider_is_blocked_before_handler():
    called = False

    async def handler(event, data):
        nonlocal called
        called = True

    middleware = AdminOnlyMiddleware(42)
    result = await middleware(handler, TelegramObject(), {"event_from_user": SimpleNamespace(id=99)})
    assert called is False
    assert result is None

