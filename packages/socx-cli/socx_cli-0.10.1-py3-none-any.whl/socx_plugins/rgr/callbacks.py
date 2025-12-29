"""Rich-Click callbacks for normalising regression CLI arguments."""

# type: ignore
from __future__ import annotations

from pathlib import Path

from socx import settings, log, log_it
from rich_click import Context, Parameter


logger = log.get_logger(__name__)


def input_cb(ctx: Context, param: Parameter, value: str | Path) -> Path:
    """Normalise the regression input path and update configuration."""
    if value and isinstance(value, str):
        path = Path(value)

        if path.exists() and path.is_file():
            input_ = {"filename": path.name, "directory": path.parent}
            settings.set("regression.run.input", input_, merge=True)

    file: str = settings.get("regression.run.input.filename")
    directory: Path = Path(settings.get("regression.run.input.directory"))
    input_path = directory / file
    return input_path


@log_it(logger=logger)
def output_cb(ctx: Context, param: Parameter, value: str) -> str:
    """Normalise the regression output directory and update configuration."""
    if value:
        path = Path(value)

        if path.exists() and path.is_dir():
            settings.set(
                "regression.run.output", {"directory": path}, merge=True
            )

    output_path: Path = Path(settings.get("regression.run.output.directory"))
    return output_path
