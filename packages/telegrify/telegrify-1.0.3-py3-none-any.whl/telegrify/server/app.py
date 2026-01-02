"""FastAPI application factory"""

import logging
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from telegrify.core.bot import TelegramBot
from telegrify.core.config import AppConfig
from telegrify.core.registry import PluginRegistry
from telegrify.formatters import MarkdownFormatter, PlainFormatter
from telegrify.server.routes import setup_routes

logger = logging.getLogger(__name__)


def create_app(config_path: str = "config.yaml") -> FastAPI:
    """Create and configure FastAPI application"""
    config = load_config(config_path)

    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format,
    )

    app = FastAPI(
        title="Telegrify",
        description="Simple Telegram notification framework",
        version="1.0.3",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    bot = TelegramBot(token=config.bot.token, test_mode=config.bot.test_mode)

    registry = PluginRegistry()
    registry.register_formatter("plain", PlainFormatter())
    registry.register_formatter("markdown", MarkdownFormatter())

    plugins_dir = Path.cwd() / "plugins"
    if plugins_dir.exists():
        logger.info("Discovering plugins...")
        registry.discover_plugins(str(plugins_dir))
        logger.info(f"Loaded formatters: {', '.join(registry.list_formatters())}")

    # Store in app state
    app.state.config = config
    app.state.bot = bot
    app.state.registry = registry
    app.state.templates = config.templates

    setup_routes(app)

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Telegrify",
            "version": "1.0.0",
            "description": "Simple Telegram notification framework",
            "status": "healthy",
            "endpoints": len(config.endpoints),
            "formatters": registry.list_formatters(),
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "endpoints": len(config.endpoints),
            "formatters": registry.list_formatters(),
        }

    logger.info(f"Telegrify server initialized with {len(config.endpoints)} endpoints")

    return app


def load_config(config_path: str) -> AppConfig:
    """Load and validate configuration from YAML file"""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    return AppConfig(**config_data)
