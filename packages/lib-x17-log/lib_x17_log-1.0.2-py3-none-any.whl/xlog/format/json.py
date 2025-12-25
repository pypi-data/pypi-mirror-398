from __future__ import annotations

import json
from typing import Optional

from xlog.event.base import EventLike
from xlog.format.base import FormatLike


class Json(FormatLike):
    """
    DESC:
        JSON formatter that converts events to JSON strings.
        Supports indentation, field filtering, and sorting.

    Params:
        indent: Optional[int] = None, indentation level for pretty printing.
        ensure_ascii: bool = False, whether to escape non-ASCII characters.
        sort: bool = True, whether to sort keys alphabetically.
        all_fields: bool = False, whether to include empty fields.

    Examples:
        ```python
        from xlog.format.json import Json
        from xlog.event.logging import Log

        # Create formatter
        formatter = Json(indent=2, sort=True)
        event = Log(message="Test", level="INFO")
        formatted = formatter.format(event)
        ```
    """

    def __init__(
        self,
        indent: Optional[int] = None,
        ensure_ascii: bool = False,
        sort: bool = True,
        all_fields: bool = False,
    ):
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort = sort
        self.all_fields = all_fields

    def format(
        self,
        event: EventLike,
    ) -> str:
        if not isinstance(event, EventLike):
            return ""

        payload = event.describe()
        if not self.all_fields:
            payload = {k: v for k, v in payload.items() if v}

        return json.dumps(
            payload,
            ensure_ascii=self.ensure_ascii,
            indent=self.indent,
            sort_keys=self.sort,
        )
