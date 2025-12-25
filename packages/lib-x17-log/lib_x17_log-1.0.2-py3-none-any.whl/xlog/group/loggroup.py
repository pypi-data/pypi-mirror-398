from __future__ import annotations

from typing import Optional

from xlog.group.base import BaseGroup


class LogGroup(BaseGroup):
    """
    DESC:
        Simple no-op logging group that extends BaseGroup.
        Receives and stores events without additional processing.

    Params:
        id: Optional[str] = None, unique identifier for the group.
        name: Optional[str] = None, name of the group.
        store: bool = True, whether to store events in memory.
        async_: bool = False, whether to process events asynchronously.
        max_queue: int = 1000, maximum queue size for async processing.
        max_len: Optional[int] = 100_000, maximum events to store per stream.

    Examples:
        ```python
        from xlog.group.loggroup import LogGroup

        # Create a simple logging group
        group = LogGroup(name="my-group", store=True)
        ```
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        async_: bool = False,
        max_queue: int = 1000,
        max_len: Optional[int] = 100_000,
    ):
        super().__init__(
            id=id,
            name=name,
            store=True,
            async_=async_,
            max_queue=max_queue,
            max_len=max_len,
        )
