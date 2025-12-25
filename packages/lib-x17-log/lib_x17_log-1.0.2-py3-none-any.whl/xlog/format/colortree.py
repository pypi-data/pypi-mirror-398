from __future__ import annotations

from typing import Any, Dict, Optional

from rich.console import Console
from rich.style import Style
from rich.tree import Tree as RichTree

from xlog.event.base import EventLike
from xlog.format.base import FormatLike


class ColorTree(FormatLike):
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    FORMAT = "[{time}][{level}] {message}"
    COLORS = {
        "INFO": "green",
        "DEBUG": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
        "UNKNOWN": "purple",
    }

    def __init__(
        self,
        width: Optional[int] = None,
        all_fields: bool = False,
        colors: Optional[Dict[str, str]] = None,
        prefix_timeformat: Optional[str] = None,
        prefix_format: Optional[str] = None,
        prefix_on: Optional[bool] = True,
    ):
        self.width = width
        self.all_fields = all_fields
        self.colors = colors or self.COLORS
        self.prefix_timeformat = self._resolve_timeformat(prefix_timeformat)
        self.prefix_format = self._resolve_format(prefix_format)
        self.prefix_on = self._resolve_prefix(prefix_on)

    def _resolve_timeformat(
        self,
        value: Optional[str],
    ) -> str:
        return value if value is not None else self.TIME_FORMAT

    def _resolve_format(
        self,
        value: Optional[str],
    ) -> str:
        return value if value is not None else self.FORMAT

    def _resolve_prefix(
        self,
        value: Optional[bool],
    ) -> bool:
        return value if value is not None else True

    def _pick_level_style(
        self,
        event: EventLike,
    ) -> str:
        lvl = getattr(event, "level", None)
        lvl = str(lvl).upper() if lvl else "INFO"
        return self.colors.get(lvl, self.colors.get("UNKNOWN", "magenta"))

    def _add_node(
        self,
        tree: RichTree,
        key: str,
        value: Any,
    ) -> None:
        if isinstance(value, dict):
            node = tree.add(f"[bold]{key}[/bold]")
            for k, v in value.items():
                self._add_node(node, k, v)
        elif isinstance(value, list):
            parent = tree.add(f"{key}")
            for item in value:
                if isinstance(item, (dict, list)):
                    child = parent.add("•")
                    if isinstance(item, dict):
                        for k, v in item.items():
                            self._add_node(child, k, v)
                    else:
                        child.add(f"{item}")
                else:
                    parent.add(f"- {item}")
        else:
            tree.add(f"[cyan]{key}[/cyan]: [reset]{value}[/reset]")

    def format(
        self,
        event: EventLike,
    ) -> str:
        console = Console(
            record=True,
            width=self.width,
            soft_wrap=True,
        )
        if not isinstance(event, EventLike):
            return ""

        payload = event.describe()
        if not self.all_fields:
            payload = {k: v for k, v in payload.items() if v not in (None, "", [], {}, False)}

        console.begin_capture()
        color = self._pick_level_style(event)
        if self.prefix_on:
            console.print(
                self.prefix_format.format(
                    time=event.time.strftime(self.prefix_timeformat),
                    level=event.level,
                    message="",
                ),
                markup=False,
                highlight=False,
                style=Style(color=color),
            )

        root = RichTree(f"{event.name}")
        for key, value in payload.items():
            self._add_node(root, key, value)
        console.print(root, style=Style(color=color), highlight=False)
        return console.end_capture().rstrip()
