"""Core interfaces for Telegrify plugin system"""

from abc import ABC, abstractmethod
from typing import Any


class IFormatter(ABC):
    """Interface for message formatters"""

    @abstractmethod
    def format(self, payload: dict[str, Any]) -> str:
        """Convert payload dict to message string"""
        pass


class IPlugin(ABC):
    """Interface for custom plugins with configuration support"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier"""
        pass

    @abstractmethod
    def format(self, payload: dict[str, Any], config: dict[str, Any]) -> str:
        """Format payload with plugin-specific configuration"""
        pass
