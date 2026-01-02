"""Tests for configuration loading and validation"""

from telegrify.core.config import AppConfig, BotConfig, EndpointConfig


def test_bot_config_valid():
    """Test valid bot configuration"""
    config = BotConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    assert config.token
    assert config.test_mode is False


def test_endpoint_config_path_normalization():
    """Test path normalization adds leading slash"""
    config = EndpointConfig(path="notify/test", chat_id="123")
    assert config.path == "/notify/test"


def test_app_config_loading(sample_config):
    """Test full configuration loading"""
    config = AppConfig(**sample_config)
    assert config.bot.token
    assert len(config.endpoints) == 1
    assert config.server.port == 8000
    assert "test_template" in config.templates
