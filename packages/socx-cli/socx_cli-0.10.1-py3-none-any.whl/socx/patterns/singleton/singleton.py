"""Simple Singleton metaclass and mixin implementation."""

from __future__ import annotations

from typing import Any
from typing import ClassVar


class _SingletonMeta(type):
    """Metaclass that caches the first instance per subclass."""

    _instances: ClassVar[dict[type, Singleton]] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Singleton:
        """Return the singleton instance for ``cls``."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_SingletonMeta("SingletonMeta", (object,), {})):
    """Mixin class for creating singleton classes.

    Extending this class enforces the singleton pattern on the subclass.

    """

    pass
