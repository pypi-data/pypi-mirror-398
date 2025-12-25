from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable

import pytz

from xlog.base.component import LogComponent


@runtime_checkable
class EventLike(Protocol):
    """
    DESC:
        Protocol defining the interface for event-like objects in the logging system.
        Used for type checking and ensuring consistent event structure across implementations.

    Params:
        message: str, the log message.
        id: str, unique identifier for the event.
        name: str, name of the event.
        time: Optional[datetime], timestamp of the event (timezone-aware).
        tz: Optional[str], timezone information.
        level: Optional[str], log level (DEBUG, INFO, WARNING, ERROR, UNKNOWN).
        code: Optional[int], numeric code (e.g., HTTP status, exit code).
        context: Dict[str, Any], additional context data as key-value pairs.
        tags: Dict[str, Any], tags for categorization and filtering.
        metrics: Dict[str, Any], performance or operational metrics.
        extra: Dict[str, Any], any additional metadata.

    Examples:
        ```python
        from xlog.event.base import EventLike
        from xlog.event.logging import Log

        # Any class implementing EventLike protocol
        def process_event(event: EventLike):
            print(event.message)

        event = Log(message="Test", level="INFO")
        process_event(event)
        ```
    """

    message: str
    id: str
    name: str
    time: Optional[datetime]
    tz: Optional[str]
    level: Optional[str]
    code: Optional[int]
    context: Dict[str, Any]
    tags: Dict[str, Any]
    metrics: Dict[str, Any]
    extra: Dict[str, Any]

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any] | "EventLike",
    ) -> "EventLike": ...

    def describe(
        self,
    ) -> Dict[str, Any]: ...

    def to_dict(
        self,
    ) -> Dict[str, Any]: ...


class BaseEvent(LogComponent):
    """
    DESC:
        Base event class for structured logging with automatic identifier generation,
        timezone handling, and serialization support. Provides comprehensive event
        tracking with message, level, timestamp, and contextual metadata.

    Params:
        message: str, the log message (required).
        id: Optional[str] = None, unique identifier (auto-generated if not provided).
        name: Optional[str] = None, event name (defaults to id if not provided).
        time: Optional[datetime] = None, event timestamp (defaults to current time).
        tz: Optional[str] = None, timezone (defaults to UTC).
        level: Optional[str] = None, log level (defaults to INFO).
        code: Optional[int] = None, numeric code (e.g., HTTP status, exit code).
        context: Optional[Dict[str, str]] = None, additional context data.
        tags: Optional[Dict[str, str]] = None, tags for filtering and categorization.
        metrics: Optional[Dict[str, str]] = None, performance or operational metrics.
        extra: Optional[Dict[str, str]] = None, any additional metadata.

    Examples:
        ```python
        from xlog.event.base import BaseEvent
        from datetime import datetime
        import pytz

        # Create basic event
        event = BaseEvent(message="Application started", level="INFO")

        # Create event with context
        event = BaseEvent(
            message="User login",
            level="INFO",
            context={"user_id": "123", "ip": "192.168.1.1"}
        )
        ```
    """

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any] | "EventLike",
    ) -> "EventLike":
        if isinstance(data, cls):
            return data
        return cls(
            id=data.get("id"),
            message=data.get("message"),
            name=data.get("name"),
            time=data.get("time"),
            tz=data.get("tz"),
            level=data.get("level"),
            context=data.get("context"),
            code=data.get("code"),
            tags=data.get("tags"),
            metrics=data.get("metrics"),
            extra=data.get("extra"),
        )

    def __init__(
        self,
        message: str,
        id: Optional[str] = None,
        name: Optional[str] = None,
        time: Optional[datetime] = None,
        tz: Optional[str] = None,
        level: Optional[str] = None,
        code: Optional[int] = None,
        context: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            id=id,
            name=name,
        )
        self.level = self._resolve_level(level)
        self.message = self._resolve_message(message)
        self.tz = self._resolve_tz(tz)
        self.time = self._resolve_time(time)
        self.code = self._resolve_code(code)
        self.context = self._resolve_struct(context)
        self.tags = self._resolve_struct(tags)
        self.metrics = self._resolve_struct(metrics)
        self.extra = self._resolve_struct(extra)
        self.identifier = self._resolve_identifier()

    def _resolve_message(
        self,
        value: Optional[str],
    ) -> str:
        return "" if not value else value.strip()

    def _resolve_code(
        self,
        value: Optional[int],
    ) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _resolve_tz(
        self,
        tz: Optional[str | pytz.BaseTzInfo],
    ) -> Optional[pytz.BaseTzInfo]:
        if isinstance(tz, str):
            try:
                return pytz.timezone(tz)
            except pytz.UnknownTimeZoneError:
                return None
        elif isinstance(tz, pytz.BaseTzInfo):
            return tz
        else:
            return None

    def _resolve_now(self) -> datetime:
        if self.tz:
            return datetime.now(self.tz)
        else:
            return datetime.now(pytz.UTC)

    def _resolve_time(
        self,
        time: Optional[datetime | str],
    ) -> datetime:
        if time is None:
            return self._resolve_now()

        if isinstance(time, str):
            try:
                time = datetime.fromisoformat(time)
            except ValueError:
                if self.tz:
                    return self._resolve_now()

        if not isinstance(time, datetime):
            return self._resolve_now()

        is_aware = time.tzinfo is not None and time.tzinfo.utcoffset(time) is not None
        if is_aware:
            if self.tz:
                return time.astimezone(self.tz)
            else:
                return time

        utc = pytz.UTC.localize(time)
        if self.tz:
            return utc.astimezone(self.tz)
        return utc

    def _resolve_identifier(self) -> str:
        raw = json.dumps(
            {
                "name": self.name,
                "time": self.time.isoformat(),
                "level": self.level,
                "message": self.message,
                "context": self.context,
                "code": self.code,
                "tags": self.tags,
                "metrics": self.metrics,
                "extra": self.extra,
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def __eq__(
        self,
        other: Any,
    ) -> bool:
        if isinstance(other, BaseEvent):
            return self.identifier == other.identifier
        if isinstance(other, Dict):
            other_event = BaseEvent.from_dict(other)
            return self.identifier == other_event.identifier
        if isinstance(other, str):
            return self.identifier == other
        return False

    def __ne__(
        self,
        value: Any,
    ) -> bool:
        return not self.__eq__(value)

    def __hash__(self):
        return hash(self.identifier)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return getattr(self, key, default)

    def describe(self) -> Dict[str, Any]:
        time = self.time.isoformat() if self.time else None
        return self.ensure_serialisable(
            {
                "message": self.message,
                "time": time,
                "level": self.level,
                "code": self.code,
                "context": self.context,
                "tags": self.tags,
                "metrics": self.metrics,
                "extra": self.extra,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        time = self.time.isoformat() if self.time else None
        zone = self.tz.zone if self.tz else None
        return self.ensure_serialisable(
            {
                "id": self.id,
                "name": self.name,
                "message": self.message,
                "time": time,
                "tz": zone,
                "level": self.level,
                "code": self.code,
                "context": self.context,
                "tags": self.tags,
                "metrics": self.metrics,
                "extra": self.extra,
            }
        )
