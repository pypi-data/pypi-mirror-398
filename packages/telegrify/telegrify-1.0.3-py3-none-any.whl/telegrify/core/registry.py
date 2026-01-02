"""Plugin registry for discovering and managing formatters"""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Union

from telegrify.core.interfaces import IFormatter, IPlugin


class PluginRegistry:
    """Registry for managing formatters and plugins"""

    def __init__(self):
        self._formatters: dict[str, Union[IFormatter, IPlugin]] = {}

    def register_formatter(self, name: str, formatter: Union[IFormatter, IPlugin]) -> None:
        """Register a formatter or plugin"""
        self._formatters[name] = formatter

    def get_formatter(self, name: str) -> Union[IFormatter, IPlugin] | None:
        """Get formatter by name"""
        return self._formatters.get(name)

    def discover_plugins(self, plugins_dir: str = "plugins") -> None:
        """Auto-discover plugins from plugins directory"""
        plugins_path = Path(plugins_dir)

        if not plugins_path.exists():
            return

        if str(plugins_path.parent) not in sys.path:
            sys.path.insert(0, str(plugins_path.parent))

        for file_path in plugins_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            module_name = f"{plugins_path.name}.{file_path.stem}"

            try:
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj in (IFormatter, IPlugin):
                        continue

                    if issubclass(obj, (IFormatter, IPlugin)):
                        instance = obj()
                        plugin_name = instance.name if hasattr(instance, "name") else name.lower()
                        self.register_formatter(plugin_name, instance)

            except Exception as e:
                print(f"Warning: Failed to load plugin from {file_path}: {e}")

    def list_formatters(self) -> list[str]:
        """List all registered formatters"""
        return list(self._formatters.keys())


registry = PluginRegistry()
