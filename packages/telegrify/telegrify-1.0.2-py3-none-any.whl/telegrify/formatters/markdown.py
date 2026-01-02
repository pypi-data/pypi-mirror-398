"""Markdown formatter for Telegram"""

from typing import Any

from telegrify.formatters.base import BaseFormatter
from telegrify. utils.escape import escape_markdown_v2


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter - converts payload to Telegram Markdown format"""

    def format(self, payload: dict[str, Any]) -> str:
        lines = []

        for key, value in payload.items():
            label = self._get_label(key)
            if key. lower() in ["title", "heading", "header"]:
                lines.append(f"*{escape_markdown_v2(value)}*")
            elif isinstance(value, dict):
                lines.append(f"*{escape_markdown_v2(label)}: *")
                for k, v in value.items():
                    k_label = self._get_label(k)
                    lines. append(f"  {escape_markdown_v2(k_label)}: {escape_markdown_v2(v)}")
            elif isinstance(value, list):
                lines.append(f"*{escape_markdown_v2(label)}:*")
                for item in value:
                    lines.append(f"  • {escape_markdown_v2(item)}")
            else:
                lines.append(f"{escape_markdown_v2(label)}: {escape_markdown_v2(value)}")

        return "\n".join(lines)
