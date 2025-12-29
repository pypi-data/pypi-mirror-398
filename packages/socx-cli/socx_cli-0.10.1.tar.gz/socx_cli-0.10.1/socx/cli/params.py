"""Shared flag definitions and helpers for the SoCX CLI."""

from __future__ import annotations

import logging
from typing import Any, cast
from collections import ChainMap
from collections.abc import Callable

from pydantic import ValidationError
import rich_click as click

from socx.config import settings
from socx.config.schema.plugin import PluginModel
from socx.cli.types import Decorator, GroupType, CommandType, AnyCallable
from socx.cli.callbacks import debug_cb, verbosity_cb, configure_cb
from socx.utils.decorators import join_decorators


def command(
    name: str | AnyCallable | None = None,
    cls: type[CommandType] | None = None,
    parent: click.Group | None = None,
    **kwargs: Any,
) -> CommandType | Callable[[AnyCallable], CommandType | click.Command]:
    cls = cls or cast(type[CommandType], click.Command)
    kwargs = dict(ChainMap(kwargs, settings.cli.command))

    def decorator(func: AnyCallable) -> CommandType:
        cmd = click.command(
            name=name if not callable(name) else name.__name__,
            cls=cls,
            **kwargs,
        )(func)

        if parent is not None:
            parent.add_command(cmd)

        return cmd

    return decorator if not callable(name) else decorator(name)


def group(
    name: str | AnyCallable | None = None,
    cls: type[GroupType] | None = None,
    parent: GroupType | None = None,
    **kwargs: Any,
) -> GroupType | Callable[[AnyCallable], GroupType | click.Group]:
    cls = cls or cast(type[GroupType], click.Group)
    kwargs = dict(ChainMap(kwargs, settings.cli.group))

    def decorator(func: AnyCallable) -> GroupType | click.Group:
        cmd = click.group(
            name=name if not callable(name) else name.__name__,
            cls=cls,
            **kwargs,
        )(func)

        if parent is not None:
            parent.add_command(cmd)

        return cmd

    return decorator if not callable(name) else decorator(name)


debug: Decorator = click.option(
    "--debug",
    "-d",
    "debug",
    help="Enable debug mode and logging.",
    envvar="SOCX_DEBUG",
    default=False,
    is_flag=True,
    is_eager=True,
    show_envvar=True,
    show_default=True,
    expose_value=False,
    callback=debug_cb,
)


verbosity: Decorator = click.option(
    "--verbosity",
    "-v",
    "verbosity",
    nargs=1,
    help="set the logging verbosity to the specified level.",
    envvar="SOCX_VERBOSITY",
    default=settings.get("cli.params.verbosity", "ERROR"),
    is_eager=True,
    show_envvar=True,
    show_choices=True,
    show_default=True,
    expose_value=False,
    type=click.Choice(
        choices=tuple(logging.getLevelNamesMapping()),
        case_sensitive=False,
    ),
    callback=verbosity_cb,
)

configure: Decorator = click.option(
    "--configure/--no-configure",
    "-c/-nc",
    help="specifies whether or not user configurations should be loaded.",
    envvar="SOCX_CONFIGURE",
    default=True,
    is_flag=True,
    is_eager=True,
    flag_value=True,
    show_envvar=True,
    show_default=True,
    expose_value=False,
    callback=configure_cb,
)


def opts() -> Decorator:
    """Apply the standard set of global SoCX CLI options."""
    return join_decorators(configure, debug, verbosity)


def panels():
    if settings.rich_click.commands_before_options:
        return join_decorators(*_command_panels(), *_option_panels())
    else:
        return join_decorators(*_option_panels(), *_command_panels())


def option_panels():
    return join_decorators(*_option_panels())


def command_panels():
    return join_decorators(*_command_panels())


def _option_panels():
    return [
        click.option_panel(
            name=panel.name,
            options=panel.options,
        )
        for panel in settings.cli.option_panels
    ]


def _command_panels():
    panel_commands = {}

    for name, plugin in settings.plugins.items():
        try:
            plugin = PluginModel(name=name, **plugin)
        except ValidationError:
            continue

        if not plugin.enabled:
            continue

        panel_commands[plugin.panel] = [
            *panel_commands.get(plugin.panel, []),
            plugin.name,
        ]

    return [
        click.command_panel(name=name, commands=commands)
        for name, commands in panel_commands.items()
    ]
