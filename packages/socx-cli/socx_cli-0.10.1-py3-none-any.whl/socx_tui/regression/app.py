"""Textual application glue for the SoCX terminal user interface."""

from __future__ import annotations

from typing import Any
from typing import ClassVar
from collections.abc import Iterable
from collections.abc import Callable

from textual.app import App
from textual.app import ComposeResult
from textual.app import SystemCommand
from textual.screen import Screen
from textual.widgets import Header
from textual.widgets import Footer
from textual.binding import Binding
from textual.binding import BindingType
from hoptex.decorator import hoptex

from socx_tui.regression.screens import TemplateView
from socx_tui.regression.screens import RegressionView


@hoptex()
class SoCX(App[int]):
    """SoCX Terminal-UI application."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("t", "push_screen('template')", "Template", show=True),
        Binding("r", "push_screen('regression')", "Regression", show=True),
    ]

    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "template": TemplateView,
        "regression": RegressionView,
    }

    MODES: ClassVar[dict[str, str | Callable[[], Screen[None]]]] = {
        "default": "regression",
        "template": TemplateView,
    }

    INLINE_PADDING = 0

    ALLOW_IN_MAXIMIZED_VIEW = ""

    def compose(self) -> ComposeResult:
        """Lay out the application chrome shared between all screens."""
        yield Header(show_clock=True, name="app_header")
        footer = Footer(classes="-ansi-colors")
        footer.compact = True
        yield footer

    async def on_mount(self) -> None:
        """Run any startup logic once the app attaches to the event loop."""
        self.call_later(self.push_screen("regression"))

    def get_system_commands(
        self, screen: Screen[None]
    ) -> Iterable[SystemCommand]:
        """Expose extra debug commands alongside Textual's defaults."""
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Log DOM Tree",
            "Print the current DOM Tree to dev log",
            lambda: self.log.info(self.tree),
        )


if __name__ == "__main__":
    app: App = SoCX(inline=True)
