"""Telegrify - Simple Telegram Notification Framework"""

from telegrify.__version__ import __version__
from telegrify.server.app import create_app
from telegrify.core.interfaces import IFormatter, IPlugin

__all__ = ["__version__", "create_app", "IFormatter", "IPlugin"]
