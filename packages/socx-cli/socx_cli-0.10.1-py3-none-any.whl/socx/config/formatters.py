"""Formatting helpers for rendering Dynaconf settings with Rich."""

import abc
from typing import Any
from typing import override

from rich import box
from rich.style import Style
from rich.text import Text
from rich.console import RenderableType
from rich.tree import Tree
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table


class Formatter(abc.ABC):
    """Base callable used to format configuration objects for display."""

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> RenderableType:
        """Format matches as text."""
        ...


def _to_text(value: Any, style: str | Style | None = None) -> Text:
    style = style or ""
    return Text.from_ansi(str(value), tab_size=4, style=style)


def _to_panel(value: Any, title: str | None = None) -> Panel:
    """Render a simple scalar settings value inside a Rich panel."""
    return Panel.fit(
        value,
        box=box.ROUNDED,
        title=title,
        title_align="left",
        highlight=True,
    )


def _to_table(key: str | Text, value: Any) -> Table:
    """Render list or dict settings values inside a Rich table."""
    tbl = Table(
        box=box.ROUNDED,
        expand=False,
        highlight=True,
        show_lines=True,
        show_header=True,
        show_footer=False,
        title_justify="left",
    )
    if isinstance(value, list | tuple | set):
        tbl.title = _to_text(key)
        tbl.add_column("index")
        for i, v in enumerate(value):
            tbl.add_row(_to_text(i).plain, _to_text(v).plain)
    elif isinstance(value, dict):
        for k in value:
            tbl.add_column(_to_text(k, "yellow"))
        tbl.add_row(*[_to_text(v) for v in value.values()])
    else:
        tbl.add_column(_to_text(key, "yellow"))
        tbl.add_row(_to_text(value))
    return tbl


def _to_tree(key: RenderableType, value: Any) -> Tree:
    """Convert nested settings structures into a Rich tree."""
    node: Tree | Table = Tree("", highlight=True)

    if isinstance(value, list | set | tuple):
        node.label = _to_text(key)
        for i, v in enumerate(value):
            k = _to_text(f"{key}[{i}]", style="bold italic")
            if not isinstance(v, dict):
                node.add(_to_tree(k, v))
            else:
                node.add(_to_table(k, v))
    elif isinstance(value, dict):
        node.label = _to_text(key)
        for k, v in value.items():
            k = _to_text(k, style="bold italic")
            if isinstance(v, dict | list | set | tuple):
                node.add(_to_tree(k, v))
            else:
                node.add(_to_table(k, v))
    else:
        node.label = _to_table(_to_text(key, "italic"), _to_text(value))
    return node


class TreeFormatter(Formatter):
    """Format Dynaconf settings into an inspectable tree view."""

    @override
    def __call__(self, obj: Any, label: str | None = None) -> Columns:
        return self.format(obj, label)

    def format(self, obj: Any, label: RenderableType | None = None) -> Columns:
        label = Text.from_ansi(f"{label}") if label else ""
        obj = _to_tree(key=label, value=obj)
        columns = Columns(
            [_to_panel(obj)],
            align="left",
            equal=True,
            expand=False,
            column_first=True,
        )

        if isinstance(obj, Table):
            return columns

        for node in obj.children:
            if isinstance(node, Tree) and len(node.children) > 1:
                columns.add_renderable(_to_panel(node))

        return columns
