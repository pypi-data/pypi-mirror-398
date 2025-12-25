from __future__ import annotations

import queue
import threading
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from xlog.base.component import LogComponent
from xlog.event.base import EventLike


@runtime_checkable
class GroupLike(Protocol):
    """
    DESC:
        Protocol defining the interface for event groups (sinks).
        Implementations receive, store, and process events from streams.

    Params:
        stream: str, name of the stream sending the event.
        event: EventLike, the event to receive and process.
        timeout: Optional[float] = None, timeout for close operations.

    Examples:
        ```python
        from xlog.group.base import GroupLike
        from xlog.group.loggroup import LogGroup
        from xlog.event.logging import Log

        # Use any group implementing GroupLike
        group: GroupLike = LogGroup(name="my-group")
        event = Log(message="Test", level="INFO")
        group.receive("stream1", event)
        group.close()
        ```
    """

    def receive(
        self,
        stream: str,
        event: EventLike,
    ) -> None: ...

    def flush(
        self,
    ) -> None: ...

    def close(
        self,
        timeout: Optional[float] = None,
    ) -> None: ...

    def list_streams(
        self,
    ) -> List[str]: ...

    def list_events(
        self,
        stream: Optional[str] = None,
    ) -> List[EventLike]: ...

    def describe(
        self,
    ) -> Dict[str, Any]: ...

    def to_dict(
        self,
    ) -> Dict[str, Any]: ...


class BaseGroup(LogComponent):
    """
    DESC:
        Base group class for event collection with sync/async processing.
        Groups receive events from streams and optionally store them.
        Supports both synchronous and asynchronous event consumption.

    Params:
        id: Optional[str] = None, unique identifier for the group (auto-generated if not provided).
        name: Optional[str] = None, name of the group (defaults to id if not provided).
        store: bool = True, whether to store events in memory.
        async_: bool = False, whether to process events asynchronously.
        max_queue: int = 1000, maximum queue size for async processing.
        max_len: Optional[int] = 100_000, maximum events to store per stream.

    Examples:
        ```python
        from xlog.group.base import BaseGroup

        # Synchronous group
        group = BaseGroup(name="sync-group", async_=False)

        # Asynchronous group with custom queue
        group = BaseGroup(name="async-group", async_=True, max_queue=5000)
        ```
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        store: bool = True,
        async_: bool = False,
        max_queue: int = 1000,
        max_len: Optional[int] = 100_000,
    ):
        super().__init__(
            id=id,
            name=name,
        )
        self.store = bool(store)
        self._async = bool(async_)
        self._stop = threading.Event()
        self._events = defaultdict(lambda: deque(maxlen=max_len))
        if self._async:
            self.max_len = max_len
            self._queue = queue.Queue(maxsize=max_queue)
            self._worker = threading.Thread(
                target=self._run,
                daemon=True,
                name=f"xlog-group:{self.name}",
            )
            self._worker.start()
        else:
            self.max_len = None
            self._queue = None
            self._worker = None

    def alive(self) -> Optional[bool]:
        if not self._async:
            return None
        return self._worker.is_alive()

    # ---------- producer API ----------
    def receive(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        if not self._async:
            if self.store:
                self._store(stream, event)
            self._consume(stream, event)
            return
        else:
            if self._stop.is_set():
                self._on_drop(stream, event)
                return
            try:
                self._queue.put_nowait((stream, event))
            except queue.Full:
                dropped = None
                try:  # drop oldest
                    dropped = self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    pass
                if dropped is not None:
                    old_stream, old_event = dropped
                    self._on_drop(old_stream, old_event)

                try:  # retry insert
                    self._queue.put_nowait((stream, event))
                except queue.Full:
                    self._on_drop(stream, event)
            finally:
                return

    def flush(self) -> None:
        if self._async and self._queue:
            self._queue.join()
        return

    def close(
        self,
        timeout: Optional[float] = None,
    ) -> None:
        if self._async:
            self._stop.set()
            self.flush()
            self._worker.join(timeout=timeout)
        return

    # ---------- internal logic ----------
    def list_streams(self) -> List[str]:
        return list(self._events.keys())

    def list_events(
        self,
        stream: Optional[str] = None,
    ) -> List[EventLike]:
        if stream:
            return list(self._events.get(stream, []))
        else:
            events: List[EventLike] = []
            for deq in self._events.values():
                events.extend(deq)
            return events

    def describe(self) -> Dict[str, Any]:
        qsize = self._queue.qsize() if self._queue else 0
        maxq = self._queue.maxsize if self._queue else 0
        return {
            "id": self.id,
            "name": self.name,
            "max_queue": maxq,
            "max_len": self.max_len,
            "store": self.store,
            "streams": self.list_streams(),
            "queue_size": qsize,
            "alive": self.alive(),
        }

    def to_dict(self) -> Dict[str, Any]:
        streams = {}
        for stream, deq in self._events.items():
            streams[stream] = [event.to_dict() for event in deq]

        qsize = self._queue.qsize() if self._queue else 0
        maxq = self._queue.maxsize if self._queue else 0
        return {
            "id": self.id,
            "name": self.name,
            "max_queue": maxq,
            "max_len": self.max_len,
            "store": self.store,
            "streams": streams,
            "queue_size": qsize,
            "alive": self.alive(),
        }

    # ---------- consumer loop ----------
    def _run(self) -> None:
        assert self._queue is not None
        while not self._stop.is_set() or not self._queue.empty():
            try:
                stream, event = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                try:
                    if self.store:
                        self._store(stream, event)
                    self._consume(stream, event)
                except Exception as e:
                    self._on_error(stream, event, e)
            finally:
                self._queue.task_done()
        self._on_close()

    def _store(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        self._events[stream].append(event)

    # ---------- overridable hooks ----------
    def _consume(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        return

    def _on_drop(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        pass

    def _on_close(self) -> None:
        pass

    def _on_error(
        self,
        stream: str,
        event: EventLike,
        error: Exception,
    ) -> None:
        pass
