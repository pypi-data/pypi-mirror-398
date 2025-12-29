"""Plugin utilities for reporting the installed SoCX package version."""

from __future__ import annotations

import sys
import shlex
import logging

import sh


logger = logging.getLogger(__name__)


def version() -> None:
    """Print version information and exit."""
    import socx

    command = sh.Command("/usr/bin/env").bake(
        shlex.split(f"-S {sys.executable} -m pip show {socx.__project__}")
    )
    command(_fg=True)
