"""Tests for formatters"""

from telegrify.formatters.markdown import MarkdownFormatter
from telegrify.formatters.plain import PlainFormatter
from telegrify.utils import escape_markdown_v2


def test_plain_formatter_simple_message():
    """Test plain formatter with simple message"""
    formatter = PlainFormatter()
    result = formatter.format({"message": "Hello World"})
    assert result == "Hello World"


def test_plain_formatter_dict():
    """Test plain formatter with dictionary"""
    formatter = PlainFormatter()
    result = formatter.format({"user": "John", "status": "active"})
    assert "user: John" in result
    assert "status: active" in result


def test_markdown_formatter():
    """Test markdown formatter"""
    formatter = MarkdownFormatter()
    result = formatter.format({"title": "Alert", "message": "Test"})
    assert "*Alert*" in result


def test_markdown_formatter_with_labels():
    """Test markdown formatter with custom labels"""
    formatter = MarkdownFormatter(labels={"order_id": "🆔 Order"})
    result = formatter.format({"order_id": "123"})
    assert "🆔 Order" in result


def test_escape_markdown_v2():
    """Test MarkdownV2 escaping"""
    text = "Hello_World! Price: $99.99"
    escaped = escape_markdown_v2(text)
    assert "\\_" in escaped
    assert "\\!" in escaped
    assert "\\." in escaped
