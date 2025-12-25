from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class NodeLike(Protocol):
    """
    DESC:
        Protocol defining the interface for logging nodes.
        Implementations handle the actual output of formatted log messages.

    Params:
        level: str, log level for the message.
        message: str, formatted message to log.
        extra: Optional[Dict[str, Any]] = None, additional metadata.

    Examples:
        ```python
        from xlog.node.base import NodeLike
        from xlog.node.logging import Logging

        # Use any node implementing NodeLike
        node: NodeLike = Logging(name="app", level="INFO")
        node.log("INFO", "Application started")
        ```
    """

    def log(
        self,
        level: str,
        message: str,
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None: ...
