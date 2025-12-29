"""Click command group that exposes configuration management workflows."""

from __future__ import annotations
from typing import cast

from box import SBox
import rich
from rich.syntax import Syntax
from rich.json import JSON
import rich_click as click

from socx import (
    group,
    console,
    print_with_pager,
    settings,
    get_logger,
    print_outputs,
    TreeFormatter,
)


logger = get_logger(__name__)


@group()
def cli():
    """Get, set, inspect, or debug configuration settings."""


@cli.command()
@click.option(
    "--user",
    "-u",
    is_flag=True,
    type=click.BOOL,
    default=False,
    help=f"""
        Edit user configuration file at '{settings.paths.USER_CONFIG_FILE}'
        instead of the default local .socx.yaml file.
    """.strip(),
)
def edit(user: bool):
    """Interactively edit configuration settings in your preferred editor."""
    from socx_plugins.config.edit import edit as _edit

    _edit(settings.paths.USER_CONFIG_FILE if user else None)


@cli.command()
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
def tree(pager: bool):
    """Print a pretty tree structure of all loaded configurations."""
    print_outputs({"config tree": settings.raw}, pager=pager, title="Tree")


@cli.command("list")
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
def list_(pager: bool):
    """Print a list of all current configuration values."""
    if not pager:
        console.print(settings.raw)
    else:
        print_with_pager(settings.raw)


@cli.command()
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
@click.argument(
    "field",
    type=click.STRING,
    default=None,
    required=False,
    metavar="[field]",
    help="The configuration field to debug.",
)
@click.pass_context
def debug(ctx: click.Context, pager: bool, field: str | None):
    """Dump cli debug info and modification history."""
    if field and field not in settings:
        ctx.fail(f"No such field: {field}")

    output = settings.get_debug_info(key=field, verbosity=2)
    if not pager:
        console.print(output)
    else:
        print_with_pager(output)


@cli.command()
@click.argument(
    "limit",
    default=0,
    required=False,
    type=click.IntRange(min=0),
    help="Limits the maximum number of history entries to list.",
    metavar="[integer]",
)
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
def history(limit: int, pager: bool):
    """Print configuration settings modification history."""
    if not pager:
        console.print(settings.get_history(limit))
    else:
        print_with_pager(settings.get_history(limit))


@cli.command()
def inspect():
    """Inspect the current settings instance and print the results."""
    rich.inspect(
        settings,
        title="Settings",
        help=True,
        docs=True,
        value=True,
        dunder=False,
        private=True,
        methods=True,
        console=console,
    )


@cli.command(no_args_is_help=True)
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
@click.argument(
    "field",
    type=click.STRING,
    required=True,
    metavar="<field>",
    help="The configuration field to be read.",
)
@click.pass_context
def get(ctx: click.Context, pager: bool, field: str):
    """Get the value of a configuration field in a pretty tree format."""
    if field not in settings:
        ctx.fail(f"Invalid field: '{field}'")

    formatter = TreeFormatter()
    outputs = formatter(obj=settings.get_raw(field), label=field)
    if not pager:
        console.print(outputs)
    else:
        print_with_pager(outputs)


get.help = """
Get the current value of a configuration field.

Some available fields:
{}

""".strip().format(
    "\n".join(
        f"- {key}"
        for key in settings.raw
        if "dynaconf" not in key and not key.startswith("_")
    )
)


@cli.command(**settings.cli.command)
@click.option(
    "--indent-guides",
    "--guides",
    "-i",
    "guides",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show indentation guides in the output.",
)
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    default=False,
    show_default=True,
    help="Display the output in a pager.",
)
@click.option(
    "--format",
    "-f",
    "format_",
    nargs=1,
    type=click.Choice(["yaml", "toml", "json"]),
    help="Specify a format for dumping configrations.",
    default="yaml",
    show_default=True,
)
@click.argument(
    "field",
    default=None,
    type=click.STRING,
    metavar="[field]",
    help="An optional name of the configuration field to be shown",
    required=False,
)
@click.pass_context
def dump(
    ctx: click.Context,
    pager: bool,
    guides: bool,
    format_: str,
    field: str | None,
) -> None:
    """Dump the current settings configurations in the specified format."""
    if field and field not in settings:
        ctx.fail(f"No such field: {field}")

    raw_box = SBox(settings.as_box(field))
    text = getattr(raw_box, format_)

    if format_ == "json":
        text = JSON(text).text.plain

    syntax = Syntax(
        cast(str, text),
        format_,
        tab_size=2,
        theme="ansi_dark",
        indent_guides=guides,
    )

    if not pager:
        console.print(syntax)
    else:
        print_with_pager(syntax)
