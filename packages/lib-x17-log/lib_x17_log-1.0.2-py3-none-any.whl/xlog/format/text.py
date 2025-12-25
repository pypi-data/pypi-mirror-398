from __future__ import annotations

from typing import Optional

from xlog.event.base import EventLike
from xlog.format.base import FormatLike


class Text(FormatLike):
    """
    DESC:
        Plain text formatter with customizable format string.
        Outputs events as human-readable text with timestamp, level, and message.

    Params:
        timeformat: Optional[str] = None, strftime format for timestamp (default: "%Y-%m-%d %H:%M:%S").
        format: Optional[str] = None, format string with {time}, {level}, {message} placeholders.

    Examples:
        ```python
        from xlog.format.text import Text
        from xlog.event.logging import Log

        # Create text formatter
        formatter = Text(format="[{level}] {message}")
        event = Log(message="Test", level="INFO")
        formatted = formatter.format(event)
        ```
    """

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FORMAT = "[{time}][{level}] {message}"

    def __init__(
        self,
        timeformat: Optional[str] = None,
        format: Optional[str] = None,
    ):
        self.timeformat = timeformat or self.TIME_FORMAT
        self.format_str = format or self.FORMAT

    def format(
        self,
        event: EventLike,
    ) -> str:
        if not isinstance(event, EventLike):
            return ""

        return self.format_str.format(
            time=event.time.strftime(self.timeformat),
            level=event.level,
            message=event.message,
        )
