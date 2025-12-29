"""Interactive configuration editing helpers for the CLI plugin."""

import os
from pathlib import Path
from logging import Logger

import rich_click as click
from rich.prompt import Prompt

from socx import (
    APP_CONFIG_DIR,
    console,
    get_logger,
    get_settings,
)
from socx.config.paths import LOCAL_CONFIG_FILENAME


logger: Logger = get_logger(__name__)


def edit(target_path: Path | None = None):
    """Launch the user's editor with the selected configuration snapshot."""
    settings = get_settings()
    file_choices = {
        path.stem: path
        for path in map(Path, settings.includes)
        if path.exists() and path.stem in settings
    }
    editor_choices = ["vim", "gvim", "nano"]
    default_editor = settings.get_environ("EDITOR", "vim")

    if default_editor not in editor_choices:
        editor_choices.append(default_editor)

    for file in file_choices.values():
        if not file.exists():
            file_choices[file.stem] = APP_CONFIG_DIR / file.name

    file_choice = Prompt.ask(
        prompt="Which configuration would you like to edit?",
        console=console,
        choices=list(file_choices),
        show_choices=True,
        case_sensitive=True,
    )
    editor_choice = Prompt.ask(
        prompt="Which editor would you like to use?",
        console=console,
        default=default_editor,
        choices=editor_choices,
        show_choices=True,
        show_default=True,
        case_sensitive=False,
    )
    target_path = target_path or Path.cwd() / LOCAL_CONFIG_FILENAME
    modified_text = click.edit(
        env=os.environ,
        text=settings.to_yaml(file_choice),
        editor=editor_choice,
        extension=".yaml",
        require_save=True,
    )

    if modified_text:
        if target_path.exists():
            modified_text = "\n".join([target_path.read_text(), modified_text])
        target_path.write_text(modified_text)
        logger.info(f"settings file written to: '{target_path}'")
    else:
        logger.info("File was not saved/modified - operation aborted.")
