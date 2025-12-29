"""Pydantic models describing SoCX CLI plugin registrations."""

from __future__ import annotations

import shlex

from box import SBox
import sh
import rich_click as click
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class PluginModel(BaseModel):
    """Metadata describing a plugin-backed CLI command."""

    env: dict[str, str] = Field(
        default_factory=dict,
        description="""
            Environment variables that should be present when the
            command/script is invoked
        """.strip(),
    )
    name: str = Field(
        pattern=r"[a-zA-Z0-9]+", description="Name of the plugin."
    )
    help: str = Field(
        default="",
        description="""
        Description of what the plugin does to be printed during plugin
        invocation if any of -h or --help flags were passed with the
        command.
    """.strip(),
    )
    panel: str = Field(
        default="Commands",
        description="""
        Custom panel name in which plugin help text will be displayed when
        CLI is invoked with the -h/--help flag.
        """.strip(),
    )
    enabled: bool = Field(
        default=True,
        description="Whether or not the plugin should be enabled.",
    )
    aliases: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Additional command aliases for the plugin.",
    )
    script: str | sh.Command = Field(
        default="",
        description="""
            A shell command or a path to an executable file to run on plugin
            invocation.
        """.strip(),
    )
    command: str | click.Command = Field(
        default="",
        pattern=r"(((((\w+)(.|/))*)(\w+))(:(\w+))?)?",
        description="""
            A path to a python module or symbol that will be called upon
            plugin invocation specified in the form of
            `<module_path/file_path>[:<symbol_name>]`.
        """.strip(),
    )
    epilog: str = Field(
        default="",
        description="""
            Help string printed at the end of the help page after everything
            else.
        """.strip(),
    )
    short_help: str = Field(
        default="",
        description="The short help to use for this command",
    )
    fresh_env: bool = Field(
        default=False,
        description="""
            Whether or not to run the plugin with a fresh environment.

            When set to True, when the plugin is launched it will be started
            in a subprocess with a fresh environment as if it was started with
            `/usr/bin/env -i` and will be passed only the environment
            variables defined under the plugin's ``env`` field.

            When set to False, both the current environment, as well as any
            key-value pairs defined under the ``env`` field, will be copied to
            the enviornment of the subprocess in which the plugin will run.
        """,
    )
    model_config = ConfigDict(
        extra="allow",
        from_attributes=True,
        arbitrary_types_allowed=True,
    )

    def is_script(self) -> bool:
        return bool(self.script)

    def is_command(self) -> bool:
        return bool(self.command)

    @classmethod
    def toml_schema(cls) -> str | None:
        return SBox(cls.model_json_schema()).toml

    @classmethod
    def yaml_schema(cls) -> str:
        return SBox(cls.model_json_schema()).yaml

    @classmethod
    def json_schema(cls) -> str:
        return SBox(cls.model_json_schema()).json

    @field_validator("script", mode="before")
    @classmethod
    def validate_script(cls, value: str | sh.Command) -> str | sh.Command:
        if not value:
            return value

        if isinstance(value, sh.Command):
            return value

        args = shlex.split(value, comments=True)

        try:
            cmd = sh.Command(args.pop(0))
        except sh.CommandNotFound as exc:
            err = f"Invalid script '{shlex.quote(value)}': {exc}"
            raise ValueError(err) from None

        return cmd.bake(*args) if args else cmd
