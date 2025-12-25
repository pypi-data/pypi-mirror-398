from __future__ import annotations

import json
from typing import Dict, Optional

from rich.console import Console

from xlog.event.base import EventLike
from xlog.format.base import FormatLike


class ColorJson(FormatLike):
    """
    DESC:
        Colored JSON formatter using rich library for terminal output.
        Applies colors based on log level for JSON-formatted events.

    Params:
        indent: Optional[int] = None, indentation level for JSON.
        ensure_ascii: bool = False, whether to escape non-ASCII characters.
        sort: bool = True, whether to sort keys alphabetically.
        all_fields: bool = False, whether to include empty fields.
        width: Optional[int] = None, console width for output.
        colors: Optional[Dict[str, str]] = None, custom color mapping for log levels.
        prefix_timeformat: Optional[str] = None, strftime format for prefix timestamp (default: "%Y-%m-%d %H:%M:%S").
        prefix_format: Optional[str] = None, format string for prefix with {time}, {level} placeholders.
        prefix_on: Optional[bool] = True, whether to include prefix in output.

    Examples:
        ```python
        from xlog.format.colorjson import ColorJson
        from xlog.event.logging import Log

        # Create colored JSON formatter
        formatter = ColorJson(indent=2)
        event = Log(message="Test", level="INFO")
        formatted = formatter.format(event)
        ```
    """

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FORMAT = "[{time}][{level}] {message}"
    COLORS = {
        "INFO": "green",
        "DEBUG": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
        "UNKNOWN": "purple",
    }

    def __init__(
        self,
        indent: Optional[int] = None,
        ensure_ascii: bool = False,
        sort: bool = True,
        width: Optional[int] = None,
        all_fields: bool = False,
        colors: Optional[Dict[str, str]] = None,
        prefix_timeformat: Optional[str] = None,
        prefix_format: Optional[str] = None,
        prefix_on: Optional[bool] = True,
    ):
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort = sort
        self.all_fields = all_fields
        self.width = width
        self.colors = colors or self.COLORS
        self.prefix_timeformat = self._resolve_timeformat(prefix_timeformat)
        self.prefix_format = self._resolve_format(prefix_format)
        self.prefix_on = self._resolve_prefix(prefix_on)

    def _resolve_timeformat(
        self,
        value: Optional[str],
    ) -> str:
        return value if value is not None else self.TIME_FORMAT

    def _resolve_format(
        self,
        value: Optional[str],
    ) -> str:
        return value if value is not None else self.FORMAT

    def _resolve_prefix(
        self,
        value: Optional[bool],
    ) -> bool:
        return value if value is not None else True

    def _pick_style(self, event: EventLike) -> str:
        lvl = getattr(event, "level", None)
        lvl = str(lvl).upper() if lvl else "INFO"
        return self.colors.get(lvl, self.colors.get("UNKNOWN", "magenta"))

    def format(self, event: EventLike) -> str:
        console = Console(
            record=True,
            width=self.width,
            soft_wrap=True,
        )
        if not isinstance(event, EventLike):
            return ""

        payload = event.describe()
        if not self.all_fields:
            payload = {k: v for k, v in payload.items() if v}

        raw = json.dumps(
            payload,
            ensure_ascii=self.ensure_ascii,
            sort_keys=self.sort,
            indent=self.indent,
        )
        if self.prefix_on:
            raw = self.prefix_format.format(
                time=event.time.strftime(self.prefix_timeformat),
                level=event.level,
                message=raw,
            )

        style = self._pick_style(event)
        console.begin_capture()
        console.print(raw, style=style, highlight=False)
        return console.end_capture().rstrip()
