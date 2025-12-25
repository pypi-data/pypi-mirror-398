from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

from xlog.event.base import BaseEvent


class Procs(BaseEvent):
    TRUNCATE = 1000

    def __init__(
        self,
        proc: subprocess.CompletedProcess,
        id: Optional[str] = None,
        name: Optional[str] = None,
        level: Optional[str] = None,
        time: Optional[datetime] = None,
        context: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        self.proc = proc
        self.ok = getattr(self.proc, "returncode", 1) == 0
        context = context or {}
        context.update(
            {
                "status": self._status(),
                "command": self._cmd(),
                "stdout": self._stdout(),
                "stderr": self._stderr(),
            }
        )
        level = self._level(level)
        code = self._code()
        message = self._message()
        super().__init__(
            message=message,
            id=id,
            name=name,
            time=time,
            level=level,
            code=code,
            context=context,
            tags=tags,
            metrics=metrics,
            extra=extra,
        )

    def _message(self) -> str:
        status = self._status()
        cmd = self._cmd()
        return f"{status}: {cmd}"

    def _stdout(self) -> str:
        rawout = getattr(self.proc, "stdout", "")
        if isinstance(rawout, bytes):
            try:
                rawout = rawout.decode("utf-8", errors="replace")
            except Exception:
                rawout = str(rawout)
        return (rawout or "").strip()[: self.TRUNCATE]

    def _stderr(self) -> str:
        rawerr = getattr(self.proc, "stderr", "")
        if isinstance(rawerr, bytes):
            try:
                rawerr = rawerr.decode("utf-8", errors="replace")
            except Exception:
                rawerr = str(rawerr)
        return (rawerr or "").strip()[: self.TRUNCATE]

    def _code(
        self,
    ) -> Optional[int]:
        return getattr(self.proc, "returncode", None)

    def _cmd(self) -> str:
        args = getattr(self.proc, "args", None)
        if args is None:
            return ""
        if isinstance(args, (list, tuple)):
            cmd = " ".join(str(a) for a in args)
        else:
            cmd = str(args)
        return cmd

    def _level(
        self,
        value: Optional[str] = None,
    ) -> str:
        if not value:
            return "INFO" if self.ok else "ERROR"
        return value.upper()

    def _status(self) -> str:
        return "succeed" if self.ok else "failed"

    def __eq__(
        self,
        other: Any,
    ) -> bool:
        if isinstance(other, Procs):
            return (
                self.proc.args == other.proc.args
                and self.proc.returncode == other.proc.returncode
                and self._stdout() == other._stdout()
                and self._stderr() == other._stderr()
            )
        if isinstance(other, Dict):
            other_event = Procs.from_dict(other)
            return self.__eq__(other_event)
        return False

    def __ne__(self, value):
        return not self.__eq__(value)
