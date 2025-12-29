from __future__ import annotations

import logging
from pathlib import Path
from collections.abc import Iterable, Iterator

from sh import RunningCommand
from sh.contrib import git  # pyright: ignore[reportMissingImports]
from git import Repo
from socx import settings
from pydantic import BaseModel, ConfigDict, computed_field

from socx_plugins.git.utils import (
    get_repo_dir,
    get_repo_name,
    find_repositories,
)


logger = logging.getLogger(__name__)


class Manifest(BaseModel):
    root: Path = settings.git.manifest.root
    includes: list[str | Path] = []
    excludes: list[str | Path] = []
    cmd_timeout: float | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __len__(self) -> int:
        return len(self.repos)

    def __contains__(self, item: str | Repo) -> bool:
        if isinstance(item, str):
            return item in self.repos

        return get_repo_name(item) in self

    @computed_field
    @property
    def repos(self) -> dict[str, Repo]:
        rv = {
            get_repo_name(repo): repo
            for repo in find_repositories(
                self.root, self.includes, self.excludes
            )
        }
        return rv

    def git(self, cmd: str, *args: Iterable[str]) -> dict[str, RunningCommand]:
        rv: dict[str, RunningCommand] = {}
        procs: dict[str, RunningCommand] = {}
        repos: dict[str, Repo] = self.repos

        for name, repo in repos.items():
            procs[name] = git(
                "-C", f"{get_repo_dir(repo)}", cmd, *args, _bg=True
            )
        for name in procs:
            rv[name] = procs[name].wait(self.cmd_timeout)
        return rv

    def iter_items(self) -> Iterator[tuple[str, Repo]]:
        return iter(self.repos.items())

    def iter_repos(self) -> Iterator[Repo]:
        return iter(self.repos.values())

    def iter_names(self) -> Iterator[str]:
        return iter(self.repos)
