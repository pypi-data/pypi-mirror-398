"""Tests for link formatting in different parse modes."""

import unittest

from telegrify.utils.escape import format_link, sanitize_text


class TestLinkFormatting(unittest.TestCase):
    """Test suite for link formatting in different parse modes."""

    def test_html_link_format_preserved(self):
        """Test that HTML links are passed through as-is"""
        # HTML format uses <a href="URL">text</a>
        html_link = '<a href="https://example.com/orders/123">View Order</a>'
        result = sanitize_text(html_link, "HTML")
        # Should preserve HTML as-is
        self.assertEqual(result, html_link)

    def test_html_mixed_content_with_link(self):
        """Test HTML content with link and other formatting"""
        html_content = (
            '🌐 <a href="https://example.com/orders/123">View Order</a> - Status: <b>Pending</b>'
        )
        result = sanitize_text(html_content, "HTML")
        # Should preserve all HTML as-is
        self.assertEqual(result, html_content)

    def test_markdownv2_link_syntax(self):
        """Test that MarkdownV2 link syntax special chars are escaped correctly"""
        # In MarkdownV2, [text](url) is the link format
        # However, when used in text that needs escaping, brackets and parens are special chars
        # The issue is that literal brackets should be escaped as \[ and \]
        # But when part of a [text](url) link, they should NOT be escaped

        # Test 1: Plain text with brackets (should escape)
        text_with_brackets = "Order [#123]"
        result = sanitize_text(text_with_brackets, "MarkdownV2")
        # Brackets should be escaped
        self.assertEqual(result, "Order \\[\\#123\\]")

    def test_markdownv2_link_in_template(self):
        """Test MarkdownV2 links when used in Jinja2 templates"""
        # This test documents expected behavior:
        # When using MarkdownV2, links should be in format [text](url)
        # The template should render the link syntax directly without escaping
        # because links need to be part of the final formatted message

        # If someone passes "[View Order](https://example.com)" as text to sanitize_text,
        # it WILL escape the brackets, which is correct behavior for raw text
        markdown_link = "[View Order](https://example.com/orders/123)"
        result = sanitize_text(markdown_link, "MarkdownV2")
        # This will escape brackets because sanitize_text treats it as raw text
        expected = "\\[View Order\\]\\(https://example\\.com/orders/123\\)"
        self.assertEqual(result, expected)

    def test_plain_text_link_no_escape(self):
        """Test that plain text mode doesn't escape anything"""
        link_text = "[View Order](https://example.com/orders/123)"
        result = sanitize_text(link_text, None)
        # Plain text should not escape
        self.assertEqual(result, link_text)

    def test_markdown_v2_url_escaping(self):
        """Test that URLs in MarkdownV2 have their special chars escaped"""
        # When building a link manually, need to escape special chars in URL
        url = "https://example.com/orders/ABC_123"
        result = sanitize_text(url, "MarkdownV2")
        # Underscores and dots should be escaped
        expected = "https://example\\.com/orders/ABC\\_123"
        self.assertEqual(result, expected)


class TestFormatLink(unittest.TestCase):
    """Test suite for the format_link utility function."""

    def test_html_link_format(self):
        """Test HTML link formatting"""
        result = format_link("View Order", "https://example.com/orders/123", "HTML")
        expected = '<a href="https://example.com/orders/123">View Order</a>'
        self.assertEqual(result, expected)

    def test_markdownv2_link_format(self):
        """Test MarkdownV2 link formatting"""
        result = format_link("View Order", "https://example.com/orders/123", "MarkdownV2")
        expected = "[View Order](https://example.com/orders/123)"
        self.assertEqual(result, expected)

    def test_markdown_link_format(self):
        """Test Markdown (legacy) link formatting"""
        result = format_link("View Order", "https://example.com/orders/123", "Markdown")
        expected = "[View Order](https://example.com/orders/123)"
        self.assertEqual(result, expected)

    def test_plain_text_link_format(self):
        """Test plain text link formatting"""
        result = format_link("View Order", "https://example.com/orders/123", None)
        expected = "View Order (https://example.com/orders/123)"
        self.assertEqual(result, expected)

    def test_empty_text(self):
        """Test with empty text"""
        result = format_link("", "https://example.com", "HTML")
        self.assertEqual(result, "")

    def test_empty_url(self):
        """Test with empty URL - should return text only"""
        result = format_link("View Order", "", "HTML")
        self.assertEqual(result, "View Order")

    def test_html_link_with_emoji(self):
        """Test HTML link with emoji"""
        result = format_link("🌐 View Order", "https://example.com/orders/123", "HTML")
        expected = '<a href="https://example.com/orders/123">🌐 View Order</a>'
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
