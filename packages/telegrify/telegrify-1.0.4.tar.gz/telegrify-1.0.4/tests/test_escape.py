"""Tests for Telegram message escaping utilities."""

import unittest

from telegrify.utils.escape import escape_markdown, escape_markdown_v2, sanitize_text


class TestEscapeMarkdownV2(unittest.TestCase):
    """Test suite for MarkdownV2 escaping function."""

    def test_escape_all_special_characters(self):
        """Test escaping all MarkdownV2 special characters"""
        text = "_*[]()~`>#+-=|{}.!"
        expected = "\\_\\*\\[\\]\\(\\)\\~\\`\\>\\#\\+\\-\\=\\|\\{\\}\\.\\!"
        actual_output = escape_markdown_v2(text)
        self.assertEqual(actual_output, expected)

    def test_text_with_no_special_characters(self):
        """Test that non-special characters remain unchanged"""
        text = "This is a simple text."
        expected = "This is a simple text\\."
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_text_with_mixed_characters(self):
        """Test realistic text with mixed characters"""
        text = "Order #123. Total: $10.00!"
        expected = "Order \\#123\\. Total: $10\\.00\\!"
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_empty_string(self):
        """Test that empty strings are handled"""
        text = ""
        self.assertEqual(escape_markdown_v2(text), "")

    def test_real_order_notification(self):
        """Test with a real-world order notification example"""
        text = "New Order #36F39592"
        expected = "New Order \\#36F39592"
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_phone_number(self):
        """Test phone numbers with + and -"""
        text = "+251963333668"
        expected = "\\+251963333668"
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_telegram_username(self):
        """Test telegram username with @"""
        text = "@scorpydev"
        expected = "@scorpydev"  # @ is not a special char in MarkdownV2
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_bullet_points(self):
        """Test bullet point lists"""
        text = "• Item 1\n• Item 2"
        expected = "• Item 1\n• Item 2"  # • is not special
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_escapes_asterisks(self):
        """Test that asterisks are escaped"""
        text = "*bold text*"
        expected = "\\*bold text\\*"
        self.assertEqual(escape_markdown_v2(text), expected)

    def test_none_input(self):
        """Test that None input is handled gracefully"""
        result = escape_markdown_v2(None)
        self.assertEqual(result, "")

    def test_numeric_input(self):
        """Test that numeric values are converted to strings"""
        result = escape_markdown_v2(123.45)
        self.assertEqual(result, "123\\.45")


class TestEscapeMarkdown(unittest.TestCase):
    """Test suite for legacy Markdown escaping function."""

    def test_basic_markdown_escape(self):
        """Test basic Markdown (non-V2) escaping"""
        text = "_*`["
        expected = "\\_\\*\\`\\["
        self.assertEqual(escape_markdown(text), expected)

    def test_markdown_preserves_other_chars(self):
        """Test that Markdown mode doesn't escape unnecessary chars"""
        text = "Order #123. Total: $10.00!"
        expected = "Order #123. Total: $10.00!"
        self.assertEqual(escape_markdown(text), expected)

    def test_none_input(self):
        """Test that None input returns empty string"""
        result = escape_markdown(None)
        self.assertEqual(result, "")

    def test_numeric_input(self):
        """Test that numeric values are converted to strings"""
        result = escape_markdown(42)
        self.assertEqual(result, "42")


class TestSanitizeText(unittest.TestCase):
    """Test suite for the sanitize_text convenience function."""

    def test_html_mode_no_escaping(self):
        """Test that HTML mode doesn't escape HTML tags"""
        text = "<b>Bold</b> <code>code</code> <i>italic</i>"
        result = sanitize_text(text, "HTML")
        # Should return text as-is, no escaping
        self.assertEqual(result, text)

    def test_html_with_special_chars(self):
        """Test HTML mode preserves all content including special chars"""
        text = "<b>Order #123</b> - Price: $99.99!"
        result = sanitize_text(text, "HTML")
        self.assertEqual(result, text)

    def test_markdownv2_mode_escapes(self):
        """Test MarkdownV2 mode escapes special characters"""
        text = "Order #123"
        result = sanitize_text(text, "MarkdownV2")
        self.assertEqual(result, "Order \\#123")

    def test_markdown_mode_escapes(self):
        """Test Markdown mode escapes special characters"""
        text = "Hello *world*"
        result = sanitize_text(text, "Markdown")
        self.assertEqual(result, "Hello \\*world\\*")

    def test_plain_text_no_escaping(self):
        """Test plain text mode (None) doesn't escape"""
        text = "Order #123 with *asterisks* and _underscores_"
        result = sanitize_text(text, None)
        self.assertEqual(result, text)

    def test_invalid_parse_mode(self):
        """Test that invalid parse mode returns text as-is with warning"""
        text = "test"
        result = sanitize_text(text, "InvalidMode")
        # Should return text as-is instead of raising error
        self.assertEqual(result, text)

    def test_none_input(self):
        """Test that None input returns empty string"""
        result = sanitize_text(None, "MarkdownV2")
        self.assertEqual(result, "")

    def test_numeric_input_with_markdownv2(self):
        """Test numeric input with MarkdownV2 mode"""
        result = sanitize_text(99.99, "MarkdownV2")
        self.assertEqual(result, "99\\.99")


if __name__ == "__main__":
    unittest.main()
