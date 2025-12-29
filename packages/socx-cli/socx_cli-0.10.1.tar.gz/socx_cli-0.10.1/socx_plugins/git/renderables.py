from __future__ import annotations

from collections.abc import Iterable
from io import StringIO

from git import Repo
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from pydantic import BaseModel, ConfigDict

from socx_plugins.git.utils import get_short_ref


class ShortRefs(BaseModel):
    repos: dict[str, Repo]
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __str__(self) -> str:
        buf = StringIO()
        console = Console(file=buf)
        for renderable in self.__rich_repr__():
            console.print(renderable)
        return buf.getvalue()

    def __rich_repr__(self) -> Iterable[RenderableType]:
        names = list(self.repos.keys())
        names.sort(key=str.casefold)
        names.sort(key=len)
        maxlen = max(map(len, names))
        yield from (
            f"{name:{maxlen}s}: {get_short_ref(self.repos[name])}"
            for name in names
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.__rich_repr__()
