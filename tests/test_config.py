from pathlib import Path

import pytest

from app.config import ConfigError, Settings, _as_bool, _as_int


def make_settings(**overrides) -> Settings:
    values = {
        "mock_mode": True,
        "telegram_bot_token": "test-token",
        "admin_telegram_id": 123,
        "target_channel_id": -100123,
        "openai_api_key": None,
        "openai_text_model": "test-text",
        "openai_image_model": "test-image",
        "database_path": Path("data/test.db"),
        "log_level": "INFO",
    }
    values.update(overrides)
    return Settings(**values)


def test_mock_mode_does_not_require_api_key():
    make_settings().validate()


def test_real_mode_requires_api_key():
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        make_settings(mock_mode=False).validate()


def test_telegram_variables_are_required():
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        make_settings(telegram_bot_token=None).validate()


@pytest.mark.parametrize("value", ["true", "1", "да", "YES"])
def test_boolean_true_values(value):
    assert _as_bool(value) is True


def test_invalid_integer_has_russian_error():
    with pytest.raises(ConfigError, match="целым числом"):
        _as_int("ADMIN_TELEGRAM_ID", "abc")

