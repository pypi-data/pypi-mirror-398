"""Composable Textual screens used by the SoCX TUI application."""

from __future__ import annotations

from typing import ClassVar

from socx import settings
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.binding import BindingType
from textual.widgets import Button, Footer, Header, Placeholder
from textual.containers import Container, HorizontalGroup

from socx_tui.regression.regression.table import Table
from socx_tui.regression.regression.table import TableVisitor


class TemplateView(ModalScreen[None], can_focus=True, inherit_bindings=True):
    """Placeholder layout demonstrating the composable screen scaffold."""

    CSS = """
    TemplateView {
        align: center top;
        Placeholder {
            padding: 0 1;
            border: none !important;
            height: auto;
        }
    }
    """

    @property
    def container(self) -> Container:
        """Return the scrollable container that hosts template content."""
        return self.query_one("#container", Container)

    def compose(self) -> ComposeResult:
        """Render a static placeholder view until real content is supplied."""
        yield Header()
        yield Footer()
        yield Placeholder("Hello")
        yield Placeholder("World")


class RegressionView(Screen[None], can_focus=True, inherit_bindings=True):
    """Screen responsible for rendering regression results within the TUI."""

    CSS = """
    RegressionView {
        height: auto;
        border: none;
        align: center top;
        max-height: 80vh;
        &.-maximized-view {
            height: 80vh;
            hatch: right ansi_black;
        }
        .-maximized { margin: 1 2; }

        Header {
            height: 1;
            margin: 0 1 !important;
        }
        Footer {
            height: 1;
            margin: 0 1 !important;
        }
        HorizontalGroup {
            align: center bottom;
            margin: 0 1 !important;
        }
        Table {
            margin: 0 1 !important;
            max-height: 60vh;
        }
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("L", "load_from_file", "Load new regression file"),
    ]

    def compose(self) -> ComposeResult:
        """Build the screen body using the regression results table widget."""
        yield Header()
        yield Footer()
        yield Table()
        with HorizontalGroup():
            yield Button("Stop", "error")
            yield Button("Start", "success")
            yield Button("Export", "primary")

    def action_load_from_file(self) -> None:
        """Load regression results from disk and refresh the table view."""
        cfg = settings.regression.run.input
        filepath = cfg.directory / cfg.filename
        table: Table = self.query_one(Table)
        table.load_from_file(filepath)
        table.accept(TableVisitor(table))
