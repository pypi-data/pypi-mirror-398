from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from xlog.event.base import BaseEvent


class Log(BaseEvent):
    def __init__(
        self,
        message: str,
        id: Optional[str] = None,
        name: Optional[str] = None,
        time: Optional[datetime] = None,
        tz: Optional[str] = None,
        level: Optional[str | int] = None,
        code: Optional[int] = None,
        context: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            message=message,
            id=id,
            name=name,
            time=time,
            tz=tz,
            level=self._level(level),
            code=code,
            context=context,
            tags=tags,
            metrics=metrics,
            extra=extra,
            **kwargs,
        )
        self.levelno = getattr(logging, self.level, logging.INFO)

    def _level(self, value) -> str:
        if isinstance(value, int):
            return logging.getLevelName(value)
        if isinstance(value, str):
            return value.upper()
        return "INFO"

    def _resolve_levelno(self):
        return getattr(logging, self.level, logging.INFO)

    def __str__(self):
        return self.message

    def __repr__(self):
        name = self.__class__.__name__
        rep = f"message={self.message}, level={self.level}"
        return f"{name}({rep})"

    def to_dict(self):
        origin = super().to_dict()
        origin.update({"levelno": self.levelno})
        return origin
