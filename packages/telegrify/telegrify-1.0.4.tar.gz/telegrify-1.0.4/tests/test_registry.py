"""Tests for plugin registry"""

from telegrify.core.registry import PluginRegistry
from telegrify.formatters.plain import PlainFormatter


def test_register_and_get_formatter():
    """Test formatter registration and retrieval"""
    registry = PluginRegistry()
    formatter = PlainFormatter()

    registry.register_formatter("test", formatter)
    retrieved = registry.get_formatter("test")

    assert retrieved is formatter


def test_list_formatters():
    """Test listing all formatters"""
    registry = PluginRegistry()
    registry.register_formatter("plain", PlainFormatter())
    registry.register_formatter("custom", PlainFormatter())

    formatters = registry.list_formatters()
    assert "plain" in formatters
    assert "custom" in formatters
    assert len(formatters) == 2
