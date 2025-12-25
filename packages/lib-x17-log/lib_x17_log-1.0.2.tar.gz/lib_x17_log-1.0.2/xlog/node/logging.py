from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional


class Logging:
    """
    DESC:
        Logging node wrapper around Python's standard logging.Logger.
        Provides simplified interface for log output with level management.

    Params:
        id: Optional[str] = None, unique identifier for the logger.
        name: Optional[str] = None, name of the logger.
        level: Optional[str] = None, log level (DEBUG, INFO, WARNING, ERROR).
        propagate: Optional[bool] = None, whether to propagate to parent loggers.
        verbose: Optional[bool] = None, whether to add console handler (default True).

    Examples:
        ```python
        from xlog.node.logging import Logging

        # Create logging node
        node = Logging(name="app", level="INFO", verbose=True)
        node.info("Application started")
        node.error("An error occurred")
        ```
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        level: Optional[str] = None,
        propagate: Optional[bool] = None,
        verbose: Optional[bool] = None,
    ):
        self.id = self._resolve_id(id)
        self.name = self._resolve_name(name)
        self.level = self._resolve_level(level)
        self.propagate = self._resolve_propagate(propagate)
        self.verbose = self._resolve_verbose(verbose)
        self.node = self._resolve_node()

    def _resolve_id(
        self,
        id: Optional[str],
    ) -> str:
        if id:
            return id
        else:
            return str(uuid.uuid4())[:5]

    def _resolve_name(
        self,
        name: Optional[str],
    ) -> str:
        return str(self.id) if not name else name.lower()

    def _resolve_level(
        self,
        level: Optional[str],
    ) -> int:
        if not level:
            return logging.INFO
        else:
            level = level.upper()
            return getattr(logging, level, logging.INFO)

    def _resolve_propagate(
        self,
        propagate: Optional[bool],
    ) -> bool:
        return bool(propagate) if propagate is not None else False

    def _resolve_verbose(
        self,
        verbose: Optional[bool],
    ) -> bool:
        return bool(verbose) if verbose is not None else True

    def _resolve_node(
        self,
    ) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        logger.propagate = self.propagate
        owned = any(getattr(h, "_x17", False) for h in logger.handlers)
        if self.verbose:
            if not owned:
                handler = logging.StreamHandler()
                handler._x17 = True
                formatter = logging.Formatter("%(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        return logger

    def set_level(
        self,
        level: str,
    ) -> None:
        self.level = self._resolve_level(level)
        self.node.setLevel(self.level)

    def log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        level = self._resolve_level(level)
        self.node.log(
            level,
            message,
            extra=extra or {},
        )

    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.log(
            "INFO",
            message,
            extra=extra or {},
        )

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.log(
            "ERROR",
            message,
            extra=extra or {},
        )

    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.log(
            "WARNING",
            message,
            extra=extra or {},
        )

    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.log(
            "DEBUG",
            message,
            extra=extra or {},
        )
