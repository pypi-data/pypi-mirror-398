"""Composable mixin that standardises Textual header/body/footer layouts."""

from textual.app import ComposeResult
from textual.widgets import Header
from textual.widgets import Footer


class Composable:
    """Provide convenience hooks for composing consistent screen scaffolds."""

    def compose(self) -> ComposeResult:
        """Compose the entire layout by chaining header, body, and footer."""
        yield from self.compose_header()
        yield from self.compose_body()
        yield from self.compose_footer()

    def compose_header(self) -> ComposeResult:
        """Yield the default header widget for the screen."""
        yield Header()

    def compose_body(self) -> ComposeResult:
        """Yield the main body content; subclasses must implement this."""
        raise NotImplementedError

    def compose_footer(self) -> ComposeResult:
        """Yield the default footer widget for the screen."""
        yield Footer()
