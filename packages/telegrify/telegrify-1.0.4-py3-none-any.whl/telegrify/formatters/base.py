"""Base formatter implementation"""

from typing import Any

from telegrify.core.interfaces import IFormatter


class BaseFormatter(IFormatter):
    """Base class for formatters"""

    def __init__(self, labels: dict[str, str] | None = None):
        self.labels = labels or {}

    def format(self, payload: dict[str, Any]) -> str:
        return self._dict_to_string(payload)

    def _get_label(self, key: str) -> str:
        return self.labels.get(key, key)

    def _dict_to_string(self, data: dict[str, Any], indent: int = 0) -> str:
        lines = []
        for key, value in data.items():
            label = self._get_label(key)
            if isinstance(value, dict):
                lines.append(f"{' ' * indent}{label}:")
                lines.append(self._dict_to_string(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{' ' * indent}{label}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._dict_to_string(item, indent + 2))
                    else:
                        lines.append(f"{' ' * (indent + 2)}- {item}")
            else:
                lines.append(f"{' ' * indent}{label}: {value}")
        return "\n".join(lines)
