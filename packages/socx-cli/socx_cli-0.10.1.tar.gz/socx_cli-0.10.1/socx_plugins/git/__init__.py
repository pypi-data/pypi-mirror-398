"""Expose git-related CLI extensions for SoCX."""

__all__ = (
    "cli",
    "get_repo",
    "get_repo_dir",
    "get_repo_name",
    "get_ref_name",
    "get_ref_type",
    "get_short_ref",
    "get_author_date",
    "get_author_name",
    "get_commit_hash",
    "get_commit_message",
    "get_ahead_behind",
    "is_branch",
    "is_repo",
    "iter_repositories",
    "find_repositories",
    "Manifest",
)

from socx_plugins.git.cli import cli as cli

from socx_plugins.git.utils import is_repo as is_repo
from socx_plugins.git.utils import is_branch as is_branch
from socx_plugins.git.utils import get_repo as get_repo
from socx_plugins.git.utils import get_repo_dir as get_repo_dir
from socx_plugins.git.utils import get_repo_name as get_repo_name
from socx_plugins.git.utils import get_ref_type as get_ref_type
from socx_plugins.git.utils import get_ref_name as get_ref_name
from socx_plugins.git.utils import get_short_ref as get_short_ref
from socx_plugins.git.utils import get_author_date as get_author_date
from socx_plugins.git.utils import get_author_name as get_author_name
from socx_plugins.git.utils import get_commit_hash as get_commit_hash
from socx_plugins.git.utils import get_commit_message as get_commit_message
from socx_plugins.git.utils import get_ahead_behind as get_ahead_behind
from socx_plugins.git.utils import iter_repositories as iter_repositories
from socx_plugins.git.utils import find_repositories as find_repositories

from socx_plugins.git.manifest import Manifest as Manifest
