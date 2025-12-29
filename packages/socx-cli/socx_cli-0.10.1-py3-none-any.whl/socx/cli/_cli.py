"""Custom Click group that dynamically loads SoCX plugin commands."""

from __future__ import annotations

from functools import cached_property
import inspect
import logging
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError
import rich_click as click

from socx.cli import params
from socx.config import settings, CommandConverter, ShConverter
from socx.cli.types import AnyCallable
from socx.config.schema.plugin import PluginModel


logger: logging.Logger = logging.getLogger(__name__)


class _CmdLine(click.RichGroup):
    """Custom Click group that loads plugin commands on demand."""

    def __init__(self, *args, **kwargs):
        self._plugins = {}
        self._sh_converter = ShConverter()
        self._cmd_converter = CommandConverter()
        self._cmd_converter._patch_theme()
        super().__init__(*args, **kwargs)

    @cached_property
    def plugins(self) -> dict[str, PluginModel]:
        """Return the plugin metadata keyed by plugin name."""
        if not self._plugins:
            for name, value in settings.plugins.items():
                try:
                    self._plugins[name] = PluginModel(name=name, **value)
                except ValidationError:
                    continue
        return self._plugins

    def get_command(
        self, ctx: click.RichContext, cmd_name: str
    ) -> click.Command | None:
        """Resolve commands from core registrations or configured plugins."""
        if cmd_name not in self.commands and cmd_name in self.plugins:
            plugin = self.plugins[cmd_name]

            if not plugin.enabled:
                return None

            cmd = self._cmd_converter(plugin)

            if isinstance(cmd, click.Command):
                self._update_command_attrs(cmd, plugin)
                self.add_command(cmd)

        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List command names including dynamically loaded plugins."""

        def get_cmd_order(cmd_name: str) -> int:
            cmd_len = len(cmd_name)
            return sum(cmd_len * i + ord(c) for i, c in enumerate(cmd_name))

        rv = [
            *super().list_commands(ctx),
            *list(filter(lambda k: self.plugins[k].enabled, self.plugins)),
        ]
        rv.sort(key=get_cmd_order)
        return rv

    def _update_command_attrs(
        self, cmd: click.Command, plugin: PluginModel
    ) -> None:
        if isinstance(cmd, click.Command):
            cmd.name = plugin.name
            cmd.epilog = cmd.epilog or plugin.epilog
            cmd.short_help = cmd.__doc__ = cmd.callback.__doc__ = (
                cmd.short_help
                or plugin.short_help
                or inspect.getdoc(cmd)
                or inspect.getdoc(cmd.callback)
            )
            cmd.help = cmd.__doc__ = cmd.callback.__doc__ = (
                cmd.help
                or plugin.help
                or plugin.short_help
                or cmd.short_help
                or inspect.getdoc(cmd)
                or inspect.getdoc(cmd.callback)
            )

            if isinstance(cmd, click.RichCommand):
                cmd.aliases = [*cmd.aliases, *plugin.aliases]
                cmd.panel = plugin.panel or cmd.panel


def socx(**kwargs: Any) -> Callable[[AnyCallable], click.Group]:
    """Decorate a callable as the root SoCX CLI group."""
    return params.group(name="socx", cls=_CmdLine, **kwargs)
