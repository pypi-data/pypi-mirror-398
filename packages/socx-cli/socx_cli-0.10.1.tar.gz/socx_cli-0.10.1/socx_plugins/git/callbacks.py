from __future__ import annotations

from pathlib import Path

import rich_click as click
from socx import settings
from socx_plugins.git.summary import SummaryFormat


def manifest_cb(
    ctx: click.Context, param: click.Parameter, value: Path
) -> Path:
    """Update manifest root path."""
    settings.git.manifest.update({param.name: value})
    return value


def manifest_lst_cb(
    ctx: click.Context, param: click.Parameter, value: tuple[str, ...]
) -> list[str]:
    """Update manifest root path."""
    settings.git.manifest.update(
        {param.name: [*settings.git.manifest.get(param.name), *value]}
    )
    return settings.git.manifest.get(param.name)


def summary_cb(
    ctx: click.Context, param: click.Parameter, value: SummaryFormat
) -> SummaryFormat:
    """Update git summary format."""
    settings.git.summary.update({param.name: value})
    return value
