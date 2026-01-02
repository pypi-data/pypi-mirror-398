"""Telegram bot sender with retry logic"""

import asyncio
import logging

import aiohttp

from telegrify.utils.escape import sanitize_text

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for sending messages"""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, token: str, test_mode: bool = False):
        self.token = token
        self.test_mode = test_mode
        self.base_url = f"{self.BASE_URL}{token}/"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict | None = None,
        max_retries: int = 3,
    ) -> dict:
        """Send text message to Telegram"""
        if self.test_mode:
            logger.info(f"TEST MODE - Would send to {chat_id}: {text}")
            return {"ok": True, "result": {"message_id": 0}}

        escaped_text = sanitize_text(text, parse_mode)

        payload = {"chat_id": chat_id, "text": escaped_text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        return await self._send_with_retry("sendMessage", payload, max_retries)

    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: str | None = None,
        parse_mode: str | None = None,
        max_retries: int = 3,
    ) -> dict:
        """Send photo to Telegram"""
        if self.test_mode:
            logger.info(f"TEST MODE - Would send photo to {chat_id}: {photo_url}")
            return {"ok": True, "result": {"message_id": 0}}

        payload = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            escaped_caption = sanitize_text(caption, parse_mode)
            payload["caption"] = escaped_caption
        if parse_mode:
            payload["parse_mode"] = parse_mode

        return await self._send_with_retry("sendPhoto", payload, max_retries)

    async def send_media_group(
        self,
        chat_id: str,
        photo_urls: list[str],
        caption: str | None = None,
        parse_mode: str | None = None,
        max_retries: int = 3,
    ) -> dict:
        """Send multiple photos as media group"""
        if self.test_mode:
            logger.info(f"TEST MODE - Would send {len(photo_urls)} photos to {chat_id}")
            return {"ok": True, "result": [{"message_id": 0}]}

        media = []
        for i, url in enumerate(photo_urls[:10]):  # Telegram limit: 10
            item = {"type": "photo", "media": url}
            if i == 0 and caption:
                escaped_caption = sanitize_text(caption, parse_mode)
                item["caption"] = escaped_caption
                if parse_mode:
                    item["parse_mode"] = parse_mode
            media.append(item)

        payload = {"chat_id": chat_id, "media": media}
        return await self._send_with_retry("sendMediaGroup", payload, max_retries)

    async def _send_with_retry(self, method: str, payload: dict, max_retries: int) -> dict:
        """Send request with exponential backoff retry"""
        url = f"{self.base_url}{method}"

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as response:
                        result = await response.json()

                        if response.status == 200:
                            return result

                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 1))
                            logger.warning(f"Rate limited. Retrying after {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue

                        error_msg = result.get("description", "Unknown error")
                        logger.error(f"Telegram API error: {error_msg}")

                        if attempt < max_retries - 1:
                            wait_time = 2**attempt
                            logger.info(f"Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise Exception(f"Failed after {max_retries} attempts: {error_msg}")

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    raise

        raise Exception(f"Failed to send message after {max_retries} attempts")

    async def set_webhook(self, url: str) -> dict:
        """Set webhook URL for receiving updates"""
        payload = {"url": url}
        return await self._send_with_retry("setWebhook", payload, 1)

    async def delete_webhook(self) -> dict:
        """Delete webhook"""
        return await self._send_with_retry("deleteWebhook", {}, 1)

    async def get_webhook_info(self) -> dict:
        """Get current webhook info"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}getWebhookInfo") as response:
                return await response.json()

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict:
        """Answer callback query from inline keyboard"""
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        payload["show_alert"] = show_alert
        return await self._send_with_retry("answerCallbackQuery", payload, 1)
