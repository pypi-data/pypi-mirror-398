"""Settings initialization, loading, and reloading management."""

from __future__ import annotations

import logging
from textwrap import dedent
import contextvars as ctx
from typing import Any
from pathlib import Path
from collections import ChainMap

from dynaconf.utils import ensure_a_list
from werkzeug.local import LocalProxy

from socx.config import converters
from socx.config._paths import (
    LOCAL_CONFIG_FILENAME,
    LOCAL_CONFIG_FILE,
    USER_CONFIG_FILE,
)
from socx.config._settings import Settings


logger = logging.getLogger(__name__)


def get_local_config_files() -> list[Path]:
    """Get a list of local settings file paths found in parent folders.

    Description
    -----------
    After initialization, `socx` searches parent directories for any file
    named '.socx.<ext>' where <ext> is any file extension supported by the
    `socx` configuration system.



    Local configuration overrides are any files named '.socx.yaml' which
    found in any of the parent directories of the current working directory.

    For reference, it works similar to git:

    1.  first, default app configurations are loaded to initialize to app's
        core functionality.

    2.  second, global user configurations are loaded from the user's
        config directory, determined according to the 'XDG Base Directory
        Specification' (https://specifications.freedesktop.org/basedir-spec).

    3.  last, a search for local configuration files is done, matching (and
        loading) any configuration files named '.socx.yaml' found in any of the
        parent directories starting the search at the current working
        directory.

    Returns
    -------
    An ordered list of `Path` objects pointing at configuration files to be
    loaded in that exact order to preserve the described overrides order.

    """
    rv = []
    for parent in LOCAL_CONFIG_FILE.parents:
        cfg = parent / LOCAL_CONFIG_FILENAME
        if cfg.exists() and cfg.is_file():
            rv.append(cfg)
    return rv


def get_user_config_files() -> list[Path]:
    """Get a list of all local config files found in parent folders.

    Description
    -----------
    User configuration files are any configuration files who's format is
    supported and are located under the XDG_CONFIG_HOME directory.

    Local configuration overrides are any files named '.socx.yaml' which
    found in any of the parent directories of the current working directory.

    For reference, it works similar to git:

    1.  first, default app configurations are loaded to initialize to app's
        core functionality.

    2.  second, global user configurations are loaded from the user's
        config directory, determined according to the 'XDG Base Directory
        Specification' (https://specifications.freedesktop.org/basedir-spec).

    3.  last, a search for local configuration files is done, matching (and
        loading) any configuration files named '.socx.yaml' found in any of the
        parent directories starting the search at the current working
        directory.

    Returns
    -------
    An ordered list of `Path` objects pointing at configuration files to be
    loaded in that exact order to preserve the described overrides order.

    """
    return [USER_CONFIG_FILE] if USER_CONFIG_FILE.exists() else []


def get_settings(
    path: str | Path | None = None,
    /,
    user_overrides: bool = False,
    local_overrides: bool = False,
    extra_overrides: list[str | Path] | None = None,
    **kwargs: Any,
) -> Settings:
    """Create a configured ``Settings`` instance, including overrides."""
    from socx.config import paths
    from socx.config import metadata
    from socx.config.serializers import ModuleSerializer

    path = path or paths.APP_CONFIG_FILE

    if isinstance(path, str):
        path = Path(path)

    settings_file = ensure_a_list(path)
    includes = []

    if user_overrides:
        includes.extend(get_user_config_files())

    if local_overrides:
        includes.extend(get_local_config_files())

    if extra_overrides:
        includes.extend(extra_overrides)

    kwargs = dict(
        ChainMap(
            kwargs,
            dict(
                includes=includes,
                settings_file=settings_file,
                **ModuleSerializer.serialize(paths),
                **ModuleSerializer.serialize(metadata),
            ),
        )
    )
    return Settings(
        **kwargs,
    )


converters.init()

_default_settings = get_settings()

_global_settings = get_settings(user_overrides=True, local_overrides=True)

_local_settings = get_settings(local_overrides=True)

_user_settings = get_settings(user_overrides=True)

_settings_cv: ctx.ContextVar[Settings] = ctx.ContextVar("settings")

settings: LocalProxy[Settings] = LocalProxy(
    _settings_cv,
    unbound_message=dedent("""
        Working outside of application context.

        Attempted to use functionality that expected a current application to
        be set. To solve this, set up an app context.
    """),
)

_settings_cv.set(_default_settings)

_settings_cv.set(_global_settings)
