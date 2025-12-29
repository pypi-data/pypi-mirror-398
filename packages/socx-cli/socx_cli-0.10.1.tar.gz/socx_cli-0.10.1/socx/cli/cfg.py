"""Configuration and theme defaults for the SoCX CLI."""

from __future__ import annotations

from rich_click import rich_click
from socx.config import settings

for attr in settings.rich_click:
    if isinstance(attr, str) and settings.rich_click.get(attr, None):
        if hasattr(rich_click, attr.lower()):
            setattr(rich_click, attr.lower(), settings.rich_click.get(attr))
        elif hasattr(rich_click, attr.upper()):
            setattr(rich_click, attr.upper(), settings.rich_click.get(attr))
