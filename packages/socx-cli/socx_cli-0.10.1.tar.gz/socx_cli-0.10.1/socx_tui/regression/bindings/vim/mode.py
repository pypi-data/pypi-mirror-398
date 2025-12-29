"""Definitions of Textual key binding presets that emulate Vim modes."""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from textual.binding import Binding
from textual.binding import BindingType


class _Mode:
    """Base class for defining modes."""

    BINDINGS: ClassVar[list[BindingType]] = []


class Normal(_Mode):
    """Normal mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("g", "scroll_top", "Cursor Bottom", show=False),
        Binding("G", "scroll_bottom", "Cursor Top", show=False),
        Binding(
            "dollar_sign",
            "scroll_end",
            "End",
            show=False,
        ),
        Binding(
            "circumflex_accent",
            "scroll_home",
            "Home",
            show=False,
        ),
    ]


class Insert(_Mode):
    """Insert mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class Visual(_Mode):
    """Visual mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class Select(_Mode):
    """Select mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class Terminal(_Mode):
    """Terminal mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class CommandLine(_Mode):
    """CommandLine mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class OperatorPending(_Mode):
    """OperatorPending mode key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = []


class VimMode(Enum):
    """Vim mode."""

    Normal = Normal.BINDINGS
    Insert = Insert.BINDINGS
    Select = Select.BINDINGS
    Visual = Visual.BINDINGS
    Terminal = Terminal.BINDINGS
    CommandLine = CommandLine.BINDINGS
    OperatorPending = OperatorPending.BINDINGS
