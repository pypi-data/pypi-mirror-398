"""Serialization helpers used when bootstrapping configuration objects."""

from __future__ import annotations

from types import ModuleType
from typing import Any, override

from dynaconf import LazySettings

from socx.core.serializer import Serializer


class ModuleSerializer(Serializer[ModuleType]):
    """Serialize module globals into a Dynaconf-ready mapping."""

    @classmethod
    @override
    def serialize(
        cls, obj: ModuleType, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        shortname = obj.__name__.rpartition(".")[-1]
        return {
            shortname: {
                k: getattr(obj, k) for k in getattr(obj, "__all__", ())
            }
        }


class SettingsSerializer(Serializer[LazySettings]):
    @classmethod
    @override
    def serialize(
        cls,
        obj: LazySettings,
        key: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Serialize a ``LazySettings`` obj into a python ``dict``."""
        from dynaconf.utils.inspect import inspect_settings

        data = inspect_settings(
            obj, key=key, history_limit=1, print_report=False
        )
        return data["current"]
