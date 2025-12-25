from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional


class LogComponent:
    """
    DESC:
        Base component class for logging infrastructure providing common functionality
        for ID generation, name resolution, level validation, and data serialization.

    Params:
        id: Optional[str] = None, unique identifier (auto-generated if not provided).
        name: Optional[str] = None, component name (defaults to id if not provided).

    Examples:
        ```python
        from xlog.base.component import LogComponent

        # Create component with auto-generated ID
        component = LogComponent(name="my-component")

        # Create component with custom ID
        component = LogComponent(id="custom-id", name="my-component")
        ```
    """

    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "UNKNOWN"]

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.id = self._resolve_id(id)
        self.name = self._resolve_name(name)

    @staticmethod
    def ensure_serialisable(value: Any) -> Any:
        natives = (str, int, float, bool, type(None))
        dts = (datetime, date, time)
        durs = (timedelta,)
        if isinstance(value, natives):
            return value
        if isinstance(value, dts):
            return value.isoformat()
        if isinstance(value, durs):
            return str(value)
        if isinstance(value, dict):
            return {str(k): LogComponent.ensure_serialisable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [LogComponent.ensure_serialisable(v) for v in value]
        return str(value)

    def _resolve_id(
        self,
        id: Optional[str],
    ) -> str:
        if id:
            return id
        else:
            return str(uuid.uuid4())[:10]

    def _resolve_name(
        self,
        name: Optional[str],
    ) -> str:
        return str(self.id) if not name else name.lower()

    def _resolve_level(
        self,
        level: Optional[str],
    ) -> str:
        if not level:
            return "INFO"
        else:
            level = level.upper()
            return level if level in self.LEVELS else "INFO"

    def _resolve_struct(
        self,
        value: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return LogComponent.ensure_serialisable(value or {})

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
