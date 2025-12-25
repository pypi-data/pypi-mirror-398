# xlog/group/file.py
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from xlog.event.base import EventLike
from xlog.group.base import BaseGroup


class FileGroup(BaseGroup):
    """
    DESC:
        File-based logging group that writes events to JSONL format.
        Each event is written as one JSON line. File name is {name}.log.

    Params:
        path: str | Path, directory path where log file will be created.
        id: Optional[str] = None, unique identifier for the group.
        name: Optional[str] = None, name of the group (used for filename).
        encoding: str = "utf-8", file encoding.
        ensure_ascii: bool = False, whether to escape non-ASCII characters.
        store: bool = True, whether to store events in memory.
        async_: bool = False, whether to process events asynchronously.
        max_queue: int = 1000, maximum queue size for async processing.
        max_len: Optional[int] = 100_000, maximum events to store per stream.

    Examples:
        ```python
        from xlog.group.filegroup import FileGroup

        # Write logs to file
        group = FileGroup(path="/tmp/logs", name="app", async_=True)
        ```
    """

    def __init__(
        self,
        path: str | Path,
        id: Optional[str] = None,
        name: Optional[str] = None,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        store: bool = True,
        async_: bool = False,
        max_queue: int = 1000,
        max_len: Optional[int] = 100_000,
    ):
        super().__init__(
            id=id,
            name=name,
            store=store,
            async_=async_,
            max_queue=max_queue,
            max_len=max_len,
        )
        self.path = self._resolve_path(path)
        self.encoding = encoding
        self.ensure_ascii = ensure_ascii
        self._lock = threading.RLock()
        self._cursor = open(
            self.path / f"{self.name}.log",
            "a",
            encoding=self.encoding,
        )

    def _resolve_path(
        self,
        value: str | Path,
    ) -> Path:
        path = Path(value).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ---------- overridable hooks ----------
    def _consume(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        payload = event.to_dict()
        line = json.dumps(
            payload,
            ensure_ascii=self.ensure_ascii,
            sort_keys=True,
        )
        with self._lock:
            self._cursor.write(line + "\n")

    def flush(self) -> None:
        super().flush()
        with self._lock:
            if not self._cursor.closed:
                self._cursor.flush()

    def _on_close(self) -> None:
        with self._lock:
            try:
                if not self._cursor.closed:
                    self._cursor.flush()
                    self._cursor.close()
            finally:
                pass
