"""Utility helpers for inspecting git repositories in SoCX plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from pathlib import Path
from collections.abc import Generator, Iterable

import git
from socx import settings
from rich.text import Text
from dynaconf.utils.files import glob, deduplicate


def get_repo(path: str | Path) -> git.Repo | None:
    """Return a ``git.Repo`` for ``path`` if it exists and is valid."""
    try:
        rv = git.Repo(path)
    except (git.NoSuchPathError, git.InvalidGitRepositoryError):
        rv = None
    return rv


def get_repo_dir(repo: git.Repo) -> Path:
    with repo:
        return Path(repo.working_dir)


def get_repo_name(repo: git.Repo) -> str:
    """Return the leaf directory name for the repository's working tree."""
    with repo:
        return Path(repo.working_dir).name


def get_ref_name(repo: git.Repo) -> str:
    """Return the current branch name or describe the detached HEAD tag."""
    with repo:
        if repo.head.is_detached:
            rv = repo.git.describe("--tags")
        else:
            rv = f"{repo.active_branch.name}"
        return rv


def get_ref_type(repo: git.Repo) -> str:
    """Identify if the current ref resolves to a branch or detached tag."""
    with repo:
        return "Branch" if is_branch(repo.head) else "Tag"


def get_short_ref(repo: git.Repo) -> str:
    ref = get_commit_hash(repo)
    args = (
        "-s",
        "--date=short",
        f"--pretty=format:[red]%<( 10 ){ref}[/] (%s, [cyan]%ad[/])",
    )
    with repo:
        return str(repo.git.show(*args))


def get_author_date(repo: git.Repo) -> str:
    """Return the author date of the current commit (short format)."""
    with repo:
        return repo.git.show("-s", "--date=short", "--pretty=%ad")


def get_author_name(repo: git.Repo) -> str:
    """Return the author date of the current commit (short format)."""
    with repo:
        return repo.git.show("-s", "--date=short", "--pretty=%an")


def get_commit_hash(repo: git.Repo) -> str:
    """Return the short hash for the repository's HEAD commit."""
    with repo:
        return repo.git.rev_parse(repo.git.show("-s", "--pretty=%H"), short=8)


def get_commit_message(repo: git.Repo) -> str:
    """Return the current commit subject line."""
    with repo:
        return repo.git.show("-s", "--pretty=%s")


def get_ahead_behind(repo: git.Repo) -> str:
    """Compare the active branch against its upstream to find divergence."""
    ahead, behind = 0, 0
    with repo:
        if is_branch(repo.head):
            local_branch = repo.active_branch
            tracking_branch = local_branch.tracking_branch()

            if tracking_branch:
                args = (
                    "--count",
                    "--left-right",
                    f"{local_branch.name}...{tracking_branch.name}",
                )
                ahead, behind = repo.git.rev_list(*args).split()

        ahead, behind = (
            Text(text=f"{ahead}", style="green"),
            Text(text=f"{behind}", style="red"),
        )

    return Text(" ").join([ahead, behind]).markup


def is_branch(head: git.HEAD | git.Head) -> bool:
    """Return ``True`` if ``head`` refers to a branch (non-detached)."""
    return not head.is_detached


def is_repo(path: str | Path) -> bool:
    """Return ``True`` if ``path`` points to a git repository."""
    return bool(get_repo(path))


def iter_repositories(
    root: Path, recursive: bool = False
) -> Generator[git.Repo]:
    if root.is_dir() and is_repo(root):
        yield git.Repo(root)

    for path in root.iterdir():
        if recursive:
            yield from iter_repositories(path, recursive)
        elif path.is_dir() and is_repo(path):
            yield git.Repo(path)


def find_repositories(
    root: Path | None,
    includes: Iterable[str | Path] | None = None,
    excludes: Iterable[str | Path] | None = None,
) -> Generator[git.Repo]:
    """Yield repositories discovered directly underneath ``directory``."""
    root = root or settings.paths.project_root_dir

    if TYPE_CHECKING:
        root = cast(Path, root)

    def deduplicate_paths(paths: Iterable[Path]) -> list[Path]:
        return list(map(Path, deduplicate([str(p) for p in paths])))

    def match_directories(
        root: Path,
        patterns: Iterable[str | Path],
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> list[Path]:
        if not root.is_dir():
            return []

        rv = [root]
        kwargs = {
            "root_dir": root,
            "recursive": recursive,
            "include_hidden": include_hidden,
        }

        for pattern in map(str, patterns):
            if not pattern.endswith("/"):
                pattern += "/"

            paths = [
                (root / path).relative_to(Path.cwd(), walk_up=True)
                for path in glob(pattern, **kwargs)
            ]
            rv.extend(filter(Path.is_dir, paths))

        return rv

    def match_repos(
        root: Path, patterns: Iterable[str | Path], deduplicate: bool = False
    ) -> list[Path]:
        dirs = filter(is_repo, match_directories(root, patterns))
        return deduplicate_paths(dirs) if deduplicate else list(dirs)

    dirs = match_repos(root, ["*/"])

    includes = (
        [includes] if isinstance(includes, str) else list(includes or [])
    )

    if includes:
        dirs.extend(match_repos(root=root, patterns=includes))

    if excludes:
        excludes = {
            str(p.resolve()) for p in match_repos(root=root, patterns=excludes)
        }
        dirs = [d for d in dirs if str(d.resolve()) not in excludes]

    dirs = deduplicate_paths(dirs)
    dirs.sort(key=lambda x: Path(x).name.lower())
    dirs.sort(key=lambda x: len(Path(x).name))

    for d in dirs:
        repo = get_repo(d)
        if repo:
            yield repo
