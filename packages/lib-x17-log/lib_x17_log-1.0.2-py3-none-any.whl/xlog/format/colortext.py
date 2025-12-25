from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Optional

from colorlog import ColoredFormatter

from xlog.event.base import EventLike


class ColorText:
    """
    DESC:
        Colored text formatter using colorlog for terminal output.
        Applies colors based on log level for improved readability.

    Params:
        timeformat: Optional[str] = None, strftime format for timestamp.
        textformat: Optional[str] = None, format string with colorlog placeholders.
        colors: Optional[Dict[str, str]] = None, custom color mapping for log levels.

    Examples:
        ```python
        from xlog.format.colortext import ColorText
        from xlog.event.logging import Log

        # Create colored formatter
        formatter = ColorText()
        event = Log(message="Test", level="INFO")
        formatted = formatter.format(event)
        ```
    """

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FORMAT = "%(log_color)s[%(asctime)s][%(levelname)s]%(reset)s %(message)s"
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
        timeformat: Optional[str] = None,
        textformat: Optional[str] = None,
        colors: Optional[Dict[str, str]] = None,
    ):
        self.timeformat = timeformat or self.TIME_FORMAT
        self.textformat = textformat or self.FORMAT
        self.colors = colors or self.COLORS
        self._formatter = ColoredFormatter(
            self.textformat,
            datefmt=self.timeformat,
            log_colors=self.colors,
        )

    def format(
        self,
        event: EventLike,
    ) -> str:
        if not isinstance(event, EventLike):
            return ""

        elevel = getattr(event, "level", "INFO").upper()
        elevelno = getattr(logging, elevel, logging.INFO)
        record = logging.LogRecord(
            name=event.name,
            level=elevelno,
            levelname=elevel,
            pathname="",
            msg=event.message,
            args=(),
            lineno=0,
            exc_info=None,
        )
        dt = getattr(event, "time", None)
        if isinstance(dt, datetime):
            record.created = dt.timestamp()
            record.msecs = dt.microsecond / 1000.0
        return self._formatter.format(record)
