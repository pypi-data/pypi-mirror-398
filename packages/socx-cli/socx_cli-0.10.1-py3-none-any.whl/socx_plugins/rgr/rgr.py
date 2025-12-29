"""Regression rerun (rgr) Click command group."""

from __future__ import annotations

import asyncio
from pathlib import Path

from socx import settings, group, command

from socx_plugins.rgr._rgr import options, _run_from_file


@group()
def cli() -> None:
    """Perform various regression related actions."""


@command(parent=cli)
def tui() -> None:
    """Open regression dashboard TUI (Terminal User Interface)."""
    from socx_tui import SoCX as SoCX

    SoCX().run(inline=True)


@command(parent=cli, no_args_is_help=True)
@options()
def run(input: Path, output: Path):  # noqa: A002
    r"""Run a regression of multiple tests defined in FILE.

    The FILE argument is a file containing a list of test commands to be ran.

    Each line represents a command to a run a single test.

    Comment lines are supported.

    Multi-line commands are not supported (but will be in the future).

    The test name is set by looking for a --test flag and setting the name
    to the argument following that flag.

    If your command does not contain such flag, you can simply append a
    shell comment to the end of the command, e.g.

    ```console
    $ make -C /foo/bar/bazz clean test  # --test bazz_test
    ```
    """
    try:
        regression = asyncio.run(
            _run_from_file(input, output), debug=settings.cli.params.debug
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        rv = 0x80 + 2  # SIGINT
    else:
        rv = sum(1 if test.failed else 0 for test in regression)

    return rv
