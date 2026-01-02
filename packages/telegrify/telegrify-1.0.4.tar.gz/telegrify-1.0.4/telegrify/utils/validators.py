"""
Input validation utilities for Telegrify.

This module provides validation functions for various input types including
chat IDs, parse modes, and payload data.
"""

from typing import Any


def validate_chat_id(chat_id: str) -> bool:
    """
    Validate Telegram chat ID format.

    Telegram chat IDs can be:
    - A numeric string (positive for users, negative for groups/channels)
    - A username starting with @ (for public channels)

    Args:
        chat_id: The chat ID to validate.

    Returns:
        True if the chat ID is valid, False otherwise.

    Examples:
        >>> validate_chat_id("123456789")
        True

        >>> validate_chat_id("@mychannel")
        True

        >>> validate_chat_id("invalid")
        False
    """
    # Check if it's a username (starts with @)
    if chat_id.startswith("@"):
        # Username must have at least one character after @
        # and contain only alphanumeric characters and underscores
        return len(chat_id) > 1 and chat_id[1:].replace("_", "").isalnum()

    # Check if it's a numeric ID
    try:
        int(chat_id)
        return True
    except ValueError:
        return False


def validate_parse_mode(parse_mode: str) -> bool:
    """
    Validate Telegram parse mode.

    Args:
        parse_mode: The parse mode to validate.

    Returns:
        True if the parse mode is supported, False otherwise.

    Note:
        Supported parse modes:
        - "Markdown":  Legacy Markdown (not recommended)
        - "MarkdownV2": Improved Markdown with more features
        - "HTML": HTML formatting
    """
    return parse_mode in ["Markdown", "MarkdownV2", "HTML"]


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Remove None values and empty strings from payload dictionary.

    This is useful for cleaning API request payloads before sending
    them to Telegram.

    Args:
        payload: The payload dictionary to sanitize.

    Returns:
        A new dictionary with None and empty string values removed.

    Examples:
        >>> sanitize_payload({"a": 1, "b": None, "c": "", "d": "valid"})
        {'a': 1, 'd': 'valid'}
    """
    return {key: value for key, value in payload.items() if value is not None and value != ""}


# Export public API
__all__ = [
    "validate_chat_id",
    "validate_parse_mode",
    "sanitize_payload",
]
