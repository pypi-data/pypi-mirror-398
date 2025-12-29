"""Dynaconf configuration wrappers used across SoCX."""

from __future__ import annotations

import sys
import logging
from typing import Any, Literal
from pathlib import Path
from collections import ChainMap
from collections.abc import Callable, Iterable

import box
from dynaconf import LazySettings
from dynaconf.base import SourceMetadata, ensure_a_list, Lazy
from dynaconf.utils.boxing import DynaBox
from dynaconf.utils.inspect import get_debug_info, _get_data_by_key

from socx.config.serializers import SettingsSerializer


logger = logging.getLogger(__name__)


sys.modules["dynaconf.vendor.box"] = box


SETTINGS_DEFAULTS: dict[str, Any] = dict(
    env="default",
    envvar="SOCX_SETTINGS_PATH",
    encoding="utf-8",
    auto_cast=True,
    load_dotenv=True,
    environments=False,
    dotted_lookup=True,
    envvar_prefix="SOCX",
    merge_enabled=True,
    lowercase_read=True,
    sysenv_fallback=True,
    dotenv_override=False,
    commentjson_enabled=True,
    apply_default_on_none=False,
)
"""Default options passed to Dynaconf constructor in `get_settings`."""


def transform(
    obj: Any, *func: Callable[..., Any] | Iterable[Callable[..., Any]]
) -> Any:
    """Apply one or more func callables to object obj and return the result."""

    def _transform(obj, fn):
        if isinstance(obj, dict):
            return type(obj)(
                {fn(k): _transform(v, fn) for k, v in obj.items()}
            )

        if isinstance(obj, list | tuple | set):
            return type(obj)([_transform(v, fn) for v in obj])

        return obj

    funcs = list(func)
    rv = obj
    for f in funcs:
        rv = _transform(rv, f)
    return rv


def encode(obj: Any):
    """Return obj or an encoded obj if obj is a decoded ``Lazy`` instance."""
    return obj._dynaconf_encode() if isinstance(obj, Lazy) else obj


def lowerfy(obj: Any):
    """Lowercase a string and return it."""
    return obj.lower() if isinstance(obj, str) else obj


class Settings(LazySettings):
    """Singleton settings instance of loaded `socx` configurations."""

    def __init__(self, wrapped=None, **kwargs: Any) -> None:
        kwargs = dict(ChainMap(kwargs, SETTINGS_DEFAULTS))
        LazySettings.__init__(self, wrapped=wrapped, **kwargs)

    def __contains__(self, key: object):
        _sentinel = object()
        return self.exists(key)

    @property
    def raw(self) -> dict[str, Any]:
        """Return this instance with all nested values as raw values.

        See Also
        --------
        get_raw : Further information regarding 'raw values'.

        """
        return self.get_raw()

    @property
    def root(self) -> Path:
        """Get the root path of the current settings instance."""
        return Path(self._root_path)

    @root.setter
    def root(self, value: str | Path) -> None:
        if isinstance(value, str):
            value = Path(value)

        if value.is_file() and value.exists():
            self.set(
                "SETTINGS_FILE_FOR_DYNACONF",
                value,
                loader_identifier="init_settings_module",
            )
            self.reload()

    @property
    def history(self) -> list[dict[str, Any]]:
        """Get the history of this instance.

        See Also
        --------
        get_history : Additional options for retrieving the settings history.

        """
        return self.get_history()

    @property
    def metadata(self) -> list[SourceMetadata]:
        """Return the ``SourceMetadata`` of loaded settings history."""
        return self._loaded_by_loaders.keys()

    @property
    def excludes(self) -> list[str]:
        """Get a list of settings paths and glob expressions not to load."""
        return self.get("SKIP_FILES_FOR_DYNACONF", [])

    @excludes.setter
    def excludes(self, value: str | Path | list[str | Path]) -> None:
        """Set the list of settings paths and glob expressions not to load."""
        excludes = [str(v) for v in ensure_a_list(value)]
        self.update(
            data={"SKIP_FILES_FOR_DYNACONF": excludes},
            merge=bool("merge" in excludes),
            tomlfy=True,
        )
        self.reload()

    @property
    def includes(self) -> list[str]:
        """Get a list of settings paths and glob expressions to load."""
        return self.get("DYNACONF_INCLUDE", [])

    @includes.setter
    def includes(self, value: str | Path | list[str | Path]) -> None:
        """Set the list of settings paths and glob expressions to load."""
        includes = [str(v) for v in ensure_a_list(value)]
        self.update(
            {"DYNACONF_INCLUDE": includes},
            merge=bool("merge" in includes),
            tomlfy=True,
        )
        self.reload()

    @property
    def loaded_files(self):
        """Get a list of paths to all loaded settings files."""
        return self._loaded_files

    @property
    def debug_info(self) -> dict[str, Any]:
        """Return a ``dict`` with useful debugging information of settings."""
        return self.get_debug_info()

    def as_box(self, key: str | None = None) -> DynaBox:
        """Get the current settings as a ``DynaBox`` instance."""
        return (
            DynaBox({key: self.get_raw(key)})
            if key
            else DynaBox(self.get_raw())
        )

    def to_json(self, key: str | None = None) -> str:
        """Serialize the current settings to JSON."""
        return self.as_box(key).to_json() or ""

    def to_toml(self, key: str | None = None) -> str:
        """Serialize the current settings to TOML."""
        return self.as_box(key).to_toml() or ""

    def to_yaml(self, key: str | None = None) -> str:
        """Serialize the current settings to YAML."""
        return self.as_box(key).to_yaml() or ""

    def get_raw(
        self,
        key: str | None = None,
        default: Any = None,
        sep: str | None = None,
    ) -> Any:
        """Return the raw value for key if such exists, else default.

        A raw value is the original value string as it was originally defined
        in the a configuration file, prior to casting it into a python object
        type.

        This is useful when writing back configuration files in order to
        revert unserializable python types into their original configuration
        string form.

        Parameters
        ----------
        key: str, optional
            The dictionary key of the raw value to return.
        default: Any, optional
            A default value to return if the key does not exist.
        sep: str, optional
            An optional seperator in the original key that will be replaced
            with a dot before performing a dotted lookup.

        Returns
        -------
        value_or_default: Any
            The value in its raw configuration format or default if key does
            not exist.
        """
        raw = SettingsSerializer.serialize(self)
        raw = transform(raw, encode, lowerfy)

        if key is None:
            return raw

        return _get_data_by_key(
            data=self.raw,
            key_dotted_path=key,
            default=default,
            sep=(sep or "__"),
        )

    def get_history(self, limit: int = 0) -> list[dict[str, Any]]:
        """Get up to limit entries of loaded data history.

        Parameters
        ----------
        limit : int, optional
            If limit > 0, it specifies the maximum number of history entries
            to append to the returned result.

            If limit == 0, all history entries are returned in the result.

            entries are sorted from newest to oldest, with the newest entry
            being at index 0.

        Returns
        -------
        list[dict[str, Any]]
            A list of history entries where each entry is a transformation
            that has been previously applied to the settings instance.

        """
        return [
            {
                **metadata._asdict(),
                "data": transform(data, encode, lowerfy),
                "num_keys": len(data),
            }
            for i, (metadata, data) in enumerate(
                reversed(self._loaded_by_loaders.items())
            )
            if i < limit or limit == 0
        ]

    def get_debug_info(
        self, key: str | None = None, verbosity: Literal[0, 1, 2] = 0
    ) -> dict[str, Any]:
        """Get a dict of debugging information about the settings isntance."""
        return get_debug_info(settings=self, verbosity=verbosity, key=key)
