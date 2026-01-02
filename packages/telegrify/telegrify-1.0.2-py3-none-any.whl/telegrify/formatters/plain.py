"""Plain text formatter"""

from typing import Any

from telegrify.formatters.base import BaseFormatter


class PlainFormatter(BaseFormatter):
    """Plain text formatter - converts payload to key: value format"""

    def format(self, payload: dict[str, Any]) -> str:
        if "message" in payload and len(payload) == 1:
            return str(payload["message"])
        return self._dict_to_string(payload)
