from __future__ import annotations

from typing import Protocol, runtime_checkable

from xlog.event.base import EventLike


@runtime_checkable
class FormatLike(Protocol):
    """
    DESC:
        Protocol defining the interface for event formatters.
        Implementations convert EventLike objects to formatted strings.

    Params:
        event: EventLike, the event to format.

    Examples:
        ```python
        from xlog.format.base import FormatLike
        from xlog.event.logging import Log
        from xlog.format.json import Json

        # Use any formatter implementing FormatLike
        formatter: FormatLike = Json()
        event = Log(message="Test", level="INFO")
        output = formatter.format(event)
        ```
    """

    def format(
        self,
        event: EventLike,
    ) -> str:
        raise NotImplementedError(
            "Subclasses must implement the format method.",
        )
