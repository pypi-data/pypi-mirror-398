"""Render summarys describing multiple git repositories."""

from __future__ import annotations

import logging
from io import StringIO
from pathlib import Path
from dataclasses import dataclass
from collections.abc import Iterable
from typing import Literal

from dynaconf.base import Lazy
from git import Repo
from rich.json import JSON
from socx import AnyCallable, settings, get_console
from rich.text import Text
from rich.table import Table
from rich.console import Console, ConsoleOptions, RenderResult
from dynaconf.utils.boxing import DynaBox
from dynaconf.utils.parse_conf import apply_converter

from socx_plugins.git.utils import (
    get_repo_name,
    get_short_ref,
)


SummaryFormat = Literal["table", "json", "ref"]

logger = logging.getLogger(__name__)


@dataclass(init=False)
class Summary:
    """Compute and present a multi-repository summary view."""

    repos: list[Repo]
    style: DynaBox
    console: Console
    columns: list[DynaBox]
    headers: list[Text]
    records: list[list[Text]]

    def __init__(self, repos: Iterable[Repo]) -> None:
        self.repos = list(repos)
        self.style = settings.git.summary.style
        self.format = settings.git.summary.format
        self.columns = settings.git.summary.columns
        self.headers = Summary.get_headers(self.columns, self.style)
        self.records = Summary.get_records(self.columns, self.repos)
        self.console = get_console(indent_guides=False)
        self._formatters: dict[SummaryFormat, AnyCallable] = {
            "ref": self.as_short_refs,
            "json": self.as_json,
            "table": self.as_rich_table,
        }

    @classmethod
    def get_header(cls, column: DynaBox, style: DynaBox) -> Text:
        """Build a styled header string for a summary column."""
        header = column.get("name", "")
        header_style = " ".join(
            [column.get("style") or "", style.get("headers") or ""]
        ).strip()
        return Text.from_markup(text=header, style=header_style)

    @classmethod
    def get_column_func(cls, column: DynaBox) -> AnyCallable:
        func = column.func
        if isinstance(func, str):
            func = apply_converter("@symbol", column.func, settings)
        if isinstance(func, Lazy):
            func = func(settings)
        return func

    @classmethod
    def get_column_value(cls, column: DynaBox, repo: Repo) -> Text:
        """Render the column content for a single repository."""
        text = str(cls.get_column_func(column)(repo))
        style = column.get("style") or ""
        content = Text.from_markup(text=text, style=style)
        return content

    @classmethod
    def get_record(cls, columns: Iterable[DynaBox], repo: Repo) -> list[Text]:
        """Return all column values for ``repo``."""
        return [cls.get_column_value(c, repo) for c in columns]

    @classmethod
    def get_headers(cls, columns: list[DynaBox], style: DynaBox) -> list[Text]:
        """Return the summary headers with style applied."""
        rv = [cls.get_header(c, style) for c in columns]
        return rv

    @classmethod
    def get_records(
        cls, columns: Iterable[DynaBox], repos: Iterable[Repo]
    ) -> list[list[Text]]:
        """Convert repository metadata into row-wise records."""
        return [cls.get_record(columns, repo) for repo in repos]

    def export(self) -> str:
        """Export the summary according to the specified format."""
        buf = StringIO()
        console = get_console(file=buf)
        renderable = self._formatters[self.format]()
        console.print(renderable)
        return buf.getvalue()

    def as_json(self) -> JSON:
        """Serialize the summary into a JSON-compatible mapping."""
        return JSON.from_data(
            {
                "summary": [
                    {
                        key.plain: value.plain
                        for key, value in zip(
                            self.headers, column, strict=True
                        )
                    }
                    for column in self.records
                ]
            }
        )

    def as_short_refs(self) -> str:
        """Return references including commit metadata suitable for logging."""
        repos = {get_repo_name(repo): repo for repo in self.repos}
        names = list(repos.keys())
        names.sort(key=str.casefold)
        names.sort(key=len)
        maxlen = max(map(len, names))
        return "\n".join(
            f"{name:{maxlen}s}: {get_short_ref(repos[name])}" for name in names
        )

    def as_rich_table(self) -> Table:
        """Create a Rich ``Table`` representing the summary."""
        import rich.box

        box = settings.git.summary.table.box or ""

        if hasattr(rich.box, box):
            settings.git.summary.table.box = getattr(rich.box, box)
        else:
            settings.git.summary.table.box = None

        rv = Table(**settings.git.summary.table)
        for header in self.headers:
            rv.add_column(header)
        for record in self.records:
            rv.add_row(*record)
        return rv

    def export_json(self, path: str | Path) -> None:
        """Write the summary JSON representation to ``path``."""
        if isinstance(path, str):
            path = Path(path)
        with open(path, "w", encoding="utf-8") as file:
            self.console.file = file
            self.console.print_json(
                data=self.as_json(), indent=4, sort_keys=True
            )
        logger.info(f"Summary written to: '{path}'.")

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Allow ``Summary`` to act as a Rich renderable."""
        yield self._formatters[self.format]()
