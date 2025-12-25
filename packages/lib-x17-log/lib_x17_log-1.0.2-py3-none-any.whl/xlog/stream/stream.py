from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, List, Optional

from xlog.base.component import LogComponent
from xlog.event.base import BaseEvent, EventLike
from xlog.format.base import FormatLike
from xlog.format.json import Json
from xlog.group.base import GroupLike
from xlog.node.base import NodeLike
from xlog.node.logging import Logging


class LogStream(LogComponent):
    """
    DESC:
        Log stream that sends events to multiple groups (sinks) and a logging node.
        Supports local event storage, formatting, and distribution to multiple destinations.

    Params:
        id: Optional[str] = None, unique identifier for the stream.
        name: Optional[str] = None, name of the stream.
        level: Optional[str] = None, default log level (DEBUG, INFO, WARNING, ERROR).
        verbose: Optional[bool] = False, whether to enable verbose logging.
        format: Optional[FormatLike] = None, formatter for events (defaults to Json).
        node: Optional[NodeLike] = None, logging node (defaults to Logging).
        local: Optional[bool] = None, whether to store events locally.
        max_local: Optional[int] = None, maximum local events to store (default 10,000).
        events: Optional[Deque[EventLike]] = None, initial events to load.
        groups: Optional[List[GroupLike]] = None, list of groups to send events to.

    Examples:
        ```python
        from xlog.stream.stream import LogStream
        from xlog.group.filegroup import FileGroup

        # Create stream with file group
        group = FileGroup(path="/tmp/logs", name="app")
        stream = LogStream(name="main", level="INFO", groups=[group])
        stream.log("Application started")
        ```
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        level: Optional[str] = None,
        verbose: Optional[bool] = False,
        format: Optional[FormatLike] = None,
        node: Optional[NodeLike] = None,
        local: Optional[bool] = None,
        max_local: Optional[int] = None,
        events: Optional[Deque[EventLike]] = None,
        groups: Optional[List[GroupLike]] = None,
    ):
        super().__init__(
            id=id,
            name=name,
        )
        self.level = self._resolve_level(level)
        self.verbose = self._resolve_verbose(verbose)
        self.format = self._resolve_format(format)
        self.node = self._resolve_node(node)
        self.local = self._resolve_local(local)
        self.max_local = self._resolve_max_local(max_local)
        self.groups = self._resolve_groups(groups)
        self.events = self._resolve_events(events)
        self.event_count = len(events or [])

    def _resolve_verbose(
        self,
        verbose: Optional[bool],
    ) -> bool:
        return bool(verbose) if verbose is not None else False

    def _resolve_format(
        self,
        format: Optional[FormatLike],
    ) -> FormatLike:
        return format or Json()

    def _resolve_node(
        self,
        node: Optional[NodeLike] = None,
    ) -> NodeLike:
        if node is not None:
            return node
        else:
            return Logging(
                name=self.name,
                level=self.level,
                propagate=False,
                verbose=self.verbose,
            )

    def _resolve_local(
        self,
        value: Optional[bool],
    ) -> bool:
        return bool(value) if value is not None else False

    def _resolve_max_local(
        self,
        value: Optional[int],
    ) -> int:
        return 10_000 if value is None or value < 1 else int(value)

    def _resolve_events(
        self,
        events: Optional[Deque[EventLike]],
    ) -> Deque[EventLike]:
        if self.local:
            resolved = deque(maxlen=self.max_local)
        else:
            resolved = deque()

        for ev in events or []:
            if not isinstance(ev, EventLike):
                ev = BaseEvent.from_dict(ev)
            if self.local:
                resolved.append(ev)
        return resolved

    def _resolve_groups(
        self,
        groups: Optional[List[GroupLike]],
    ) -> List[GroupLike]:
        resolved: List[GroupLike] = []
        for grp in groups or []:
            if isinstance(grp, GroupLike):
                resolved.append(grp)
        return resolved

    def event(
        self,
        event: EventLike,
    ) -> EventLike:
        self._add_event(event)
        self._log(event)
        return event

    def log(
        self,
        message: str,
        **kwargs: Dict[str, Any],
    ) -> EventLike:
        event = BaseEvent(message=message, **kwargs)
        self._add_event(event)
        self._log(event)
        return event

    def _add_event(
        self,
        event: EventLike,
    ) -> None:
        self.event_count += 1
        if self.groups:
            for group in self.groups:
                try:
                    group.receive(self.name, event)
                except Exception:
                    continue
        if self.local:
            self.events.append(event)

    def _log(
        self,
        event: EventLike,
    ) -> None:
        if not isinstance(self.node, NodeLike):
            return
        level = getattr(event, "level", self.level) or "INFO"
        rendered = self.format.format(event)
        try:
            self.node.log(level, rendered)
        except Exception:
            pass

    def add_group(
        self,
        group: GroupLike,
    ) -> None:
        if group not in self.groups:
            self.groups.append(group)

    def remove_group(
        self,
        group: GroupLike,
    ) -> None:
        if group in self.groups:
            self.groups.remove(group)

    def set_level(
        self,
        level: str,
    ) -> None:
        self.level = self._resolve_level(level)
        if hasattr(self.node, "set_level"):
            self.node.set_level(self.level)

    def list_events(self) -> List[EventLike]:
        return list(self.events)

    def describe(self) -> Dict[str, Any]:
        return self.ensure_serialisable(
            {
                "id": self.id,
                "name": self.name,
                "level": self.level,
                "verbose": self.verbose,
                "local": self.local,
                "max_local": self.max_local,
                "event_count": self.event_count,
                "events": [getattr(event, "message", "") for event in self.events],
                "groups": [getattr(group, "name", "") for group in self.groups],
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.ensure_serialisable(
            {
                "id": self.id,
                "name": self.name,
                "level": self.level,
                "verbose": self.verbose,
                "local": self.local,
                "max_local": self.max_local,
                "event_count": self.event_count,
                "events": [event.to_dict() for event in self.events],
                "groups": [group.to_dict() for group in self.groups],
            }
        )
