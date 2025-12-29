"""Click command hook for launching the SoCX terminal user interface."""

import rich_click as click

from socx import settings
from socx_tui import SoCX as SoCX


@click.command("ui", context_settings=settings.cli.context_settings)
def cli() -> None:
    """Launch the SoCX Textual UI from the command line."""
    SoCX().run()
