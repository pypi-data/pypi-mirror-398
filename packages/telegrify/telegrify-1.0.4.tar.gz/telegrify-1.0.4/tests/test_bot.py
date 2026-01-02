"""Tests for Telegram bot"""

import pytest

from telegrify.core.bot import TelegramBot


@pytest.mark.asyncio
async def test_bot_test_mode():
    """Test bot in test mode (no actual sending)"""
    bot = TelegramBot(token="test_token", test_mode=True)
    result = await bot.send_message(chat_id="123", text="Test message")

    assert result["ok"] is True
    assert "result" in result


@pytest.mark.asyncio
async def test_bot_send_photo_test_mode():
    """Test sending photo in test mode"""
    bot = TelegramBot(token="test_token", test_mode=True)
    result = await bot.send_photo(
        chat_id="123", photo_url="https://example.com/photo.jpg", caption="Test"
    )

    assert result["ok"] is True
