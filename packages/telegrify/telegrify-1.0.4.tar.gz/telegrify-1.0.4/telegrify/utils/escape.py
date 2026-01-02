"""
Telegram message escaping utilities for MarkdownV2 and HTML parse modes.

This module provides robust escaping functions to ensure messages are properly
formatted according to Telegram Bot API specifications.

References:
    - https://core.telegram.org/bots/api#markdownv2-style
    - https://core.telegram.org/bots/api#html-style
"""

import re
from typing import Optional, Union

# Type alias for text input
TextInput = Optional[Union[str, int, float]]


def escape_markdown_v2(text: TextInput) -> str:
    """
    Escape special characters for Telegram MarkdownV2 parse mode.

    Escapes ALL special characters.  Formatting must be added explicitly
    in templates after escaping variable values.

    Args:
        text: The text to escape.  Can be str, int, float, or None.

    Returns:
        The escaped text with all special characters preceded by backslashes.
        Returns empty string if input is None or empty.

    Examples:
        >>> escape_markdown_v2("Order #123")
        'Order \\#123'

        >>> escape_markdown_v2(None)
        ''

    Note:
        Special characters that are escaped:
        _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    # Handle None or empty input
    if text is None:
        return ""

    # Convert non-string types to string
    if not isinstance(text, str):
        text = str(text)

    # Return empty string for empty input
    if not text:
        return ""

    # Escape all special characters for MarkdownV2
    # Note: - must be escaped as \- in the regex character class
    escape_chars = r"([_*\[\]()~`>#+\-=|{}.!])"
    escaped_text = re.sub(escape_chars, r"\\\1", text)

    return escaped_text


def escape_markdown(text: TextInput) -> str:
    """
    Escape special characters for Telegram Markdown (legacy) parse mode.

    Args:
        text: The text to escape. Can be str, int, float, or None.

    Returns:
        The escaped text with markdown special characters preceded by backslashes.
        Returns empty string if input is None or empty.

    Examples:
        >>> escape_markdown("Hello *world*")
        'Hello \\*world\\*'

        >>> escape_markdown(None)
        ''

    Note:
        Special characters that are escaped:  _ * ` [

        Telegram recommends using MarkdownV2 instead of Markdown for new bots.
    """
    # Handle None or empty input
    if text is None:
        return ""

    # Convert non-string types to string
    if not isinstance(text, str):
        text = str(text)

    # Return empty string for empty input
    if not text:
        return ""

    # Escape Markdown special characters
    escape_chars = r"([_*`\[])"
    return re.sub(escape_chars, r"\\\1", text)


def sanitize_text(text: TextInput, parse_mode: Optional[str] = None) -> str:
    """
    Sanitize text based on the specified parse mode.

    This is a convenience function that automatically chooses the appropriate
    escaping strategy based on the Telegram parse mode.

    Args:
        text: The text to sanitize. Can be str, int, float, or None.
        parse_mode: The Telegram parse mode.  Can be:
                   - "MarkdownV2" (recommended): Escapes special chars
                   - "Markdown" (legacy): Escapes basic markdown chars
                   - "HTML": Returns text as-is (Telegram expects raw HTML)
                   - None: No escaping for plain text mode

    Returns:
        The sanitized text appropriate for the specified parse mode.
        Returns empty string if input is None or empty.

    Examples:
        >>> sanitize_text("Order #123", "MarkdownV2")
        'Order \\#123'

        >>> sanitize_text("<b>Bold</b>", "HTML")
        '<b>Bold</b>'

        >>> sanitize_text("Plain text", None)
        'Plain text'

    Note:
        For HTML mode, this function returns text unchanged because Telegram
        expects raw HTML tags like <b>, <code>, <i>, etc.
    """
    # Handle None or empty input
    if text is None:
        return ""

    # Convert non-string types to string
    if not isinstance(text, str):
        text = str(text)

    # Return empty string for empty input
    if not text:
        return ""

    # Choose escaping function based on parse mode
    if parse_mode == "MarkdownV2":
        return escape_markdown_v2(text)
    elif parse_mode == "Markdown":
        return escape_markdown(text)
    elif parse_mode == "HTML":
        # For HTML mode, return text as-is
        # Telegram expects raw HTML tags like <b>, <code>, <i>
        return text
    elif parse_mode is None:
        # No escaping for plain text mode
        return text
    else:
        # For unknown parse modes, return as-is (don't break)
        import logging

        logging.getLogger(__name__).warning(
            f"Unknown parse_mode '{parse_mode}', returning text as-is"
        )
        return text


def format_link(text: str, url: str, parse_mode: Optional[str] = None) -> str:
    """
    Format a clickable link for the specified Telegram parse mode.

    Args:
        text: The link text to display
        url: The URL to link to
        parse_mode: The Telegram parse mode ("HTML", "MarkdownV2", "Markdown", or None)

    Returns:
        A properly formatted link string for the specified parse mode.

    Examples:
        >>> format_link("Click here", "https://example.com", "HTML")
        '<a href="https://example.com">Click here</a>'

        >>> format_link("Click here", "https://example.com", "MarkdownV2")
        '[Click here](https://example.com)'

        >>> format_link("Click here", "https://example.com", None)
        'Click here (https://example.com)'

    Note:
        - For HTML mode: Returns <a href="URL">text</a>
        - For MarkdownV2/Markdown: Returns [text](URL)
        - For None (plain text): Returns "text (URL)"
        - The text and URL are NOT escaped by this function. If you need
          to escape user input, do so before calling this function.
    """
    if not text or not url:
        return text or ""

    if parse_mode == "HTML":
        return f'<a href="{url}">{text}</a>'
    elif parse_mode in ("MarkdownV2", "Markdown"):
        return f"[{text}]({url})"
    else:
        # Plain text mode - just show both
        return f"{text} ({url})"


# Export public API
__all__ = [
    "escape_markdown_v2",
    "escape_markdown",
    "sanitize_text",
    "format_link",
]
