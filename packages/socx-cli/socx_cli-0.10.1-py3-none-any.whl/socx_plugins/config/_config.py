"""Interactive helpers that power the ``socx config`` edit workflow."""

from __future__ import annotations

import os
from pathlib import Path

from rich.prompt import Prompt
import rich_click as click

from socx import settings, console, get_logger


logger = get_logger(__name__)


def edit_config():
    """Prompt the user for a config file and editor, then persist edits."""
    files = {
        Path(file).stem: Path(settings.app_settings_dir / file)
        for file in settings.dynaconf_include
    }

    for name in files:
        try:
            files[name] = files[name].resolve()
        except OSError:
            del files[name]

    file_choice = Prompt.ask(
        console=console,
        prompt="Which configuration would you like to edit?",
        choices=list(files),
        show_choices=True,
        case_sensitive=True,
    )

    editor_choice = Prompt.ask(
        console=console,
        prompt="Which editor would you like to use?",
        default=settings.get_environ("EDITOR", "vim"),
        choices=["nano", "vim", "nvim", "gvim", "neovim", "emacs"],
        show_default=True,
        show_choices=True,
        case_sensitive=False,
    )

    file = files[file_choice]
    user_file = settings.user_config_dir / file.name

    if editor_choice.casefold() in ["nvim".casefold(), "neovim".casefold()]:
        editor_choice = "nvim"

    if text := click.edit(
        env=os.environ,
        text=file.read_text(),
        editor=editor_choice,
        extension=file.suffix,
        require_save=True,
    ):
        user_file.write_text(text, encoding="utf-8")
        logger.info(f"File saved to: {user_file}")
