"""Preconfigured Rich console used throughout SoCX."""

from __future__ import annotations

from typing import Any
from collections import ChainMap
from collections.abc import Iterable

from sh import RunningCommand
from rich import pretty
from rich import traceback
from rich.console import Console, RenderableType
import click
import dynaconf
import rich_click

from socx.config.formatters import TreeFormatter


__all__ = ("console", "get_console")

_DEFAULTS = dict(tab_size=4, markup=True, highlight=True, record=False)


def print_with_pager(
    *renderables: RenderableType | Iterable[RenderableType],
) -> None:
    """
    Print the given text using the console pager.

    Parameters
    ----------
    *renderables: RenderableType | Iterable[RenderableType]
        The text or renderable objects to display.
    """
    with console.pager(styles=True, links=True):
        console.print(*renderables)


def print_outputs(
    outputs: dict[str, Any],
    pager: bool = True,
    title: str | None = None,
) -> None:
    """
    Print a dictionary of outputs, optionally using a pager.

    Parameters
    ----------
    outputs: dict[str, str]
        Mapping of names to output strings.
    pager: bool, optional
        Whether to use a pager for output. Defaults to True.
    title: str | None, optional
        Optional title for the output. Defaults to None.
    """
    title = title or ""
    formatter = TreeFormatter()
    text = formatter(outputs, title)
    if not pager:
        console.print(text)
    else:
        print_with_pager(text)


def print_command_outputs(
    outputs: dict[str, RunningCommand],
    pager: bool = True,
    title: str | None = None,
) -> None:
    """
    Print the stdout of a dictionary of RunningCommand objects.

    Parameters
    ----------
    outputs: dict[str, RunningCommand]
        Mapping of names to RunningCommand objects.
    pager: bool = True
        Whether to use a pager for output. Defaults to True.
    title: str | None
        Optional title for the output. Defaults to None.
    """
    cmd_outputs = {
        name: output.stdout.decode() for name, output in outputs.items()
    }
    print_outputs(cmd_outputs, pager=pager, title=title)


def get_console(
    *args: Any, indent_guides: bool = True, **kwargs: Any
) -> Console:
    """
    Create and configure a rich Console instance with custom settings.

    Parameters
    ----------
    indent_guides: bool = True
        Whether to show indent guides. Defaults to True.
    **kwargs: dict[str, Any]
        Additional keyword arguments for Console.

    Returns
    -------
    Console:
        Configured Console instance.
    """
    kwargs = dict(ChainMap(kwargs, _DEFAULTS))
    console = Console(*args, **kwargs)
    pretty.install(console, indent_guides=indent_guides)
    traceback.install(
        console=console,
        suppress=[click, rich_click, dynaconf],
        word_wrap=True,
        code_width=88,
        extra_lines=3,
        show_locals=True,
        locals_hide_sunder=True,
        locals_hide_dunder=True,
    )
    return console


console: Console = get_console()
