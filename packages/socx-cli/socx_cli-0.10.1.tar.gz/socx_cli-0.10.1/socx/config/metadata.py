"""Metadata helpers that expose packaging information for SoCX."""

from __future__ import annotations

from pathlib import Path
from inspect import getfile
from importlib.metadata import version
from importlib.metadata import metadata
from importlib.metadata import PackageMetadata

__all__ = (
    "__author__",
    "__project__",
    "__version__",
    "__appname__",
    "__directory__",
)


__appname__: str = "socx"
"""Application name."""

__project__: str = "socx-cli"
"""Project name."""

__author__: str = "Sagi Kimhi <sagi.kim5@gmail.com>"
"""Project author."""

__version__: str = version(__project__)
"""Project version."""

__metadata__: PackageMetadata = metadata(__project__)
"""Project metadata."""

__directory__: Path = Path(getfile(lambda: None)).parents[1].resolve()
"""Project source directory."""
