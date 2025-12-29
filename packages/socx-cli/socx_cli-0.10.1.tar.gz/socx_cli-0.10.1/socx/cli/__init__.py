"""Expose primary CLI entry points and shared helpers."""

__all__ = (
    "cfg",
    "cli",
    "debug",
    "configure",
    "verbosity",
    "opts",
    "debug_cb",
    "configure_cb",
    "verbosity_cb",
    "Decorator",
    "AnyCallable",
)


import socx.cli.cfg as cfg

from socx.cli.cli import cli as cli

from socx.cli.types import Decorator as Decorator
from socx.cli.types import AnyCallable as AnyCallable

from socx.cli.params import opts as opts
from socx.cli.params import debug as debug
from socx.cli.params import group as group
from socx.cli.params import command as command
from socx.cli.params import configure as configure
from socx.cli.params import verbosity as verbosity

from socx.cli.callbacks import debug_cb as debug_cb
from socx.cli.callbacks import configure_cb as configure_cb
from socx.cli.callbacks import verbosity_cb as verbosity_cb
