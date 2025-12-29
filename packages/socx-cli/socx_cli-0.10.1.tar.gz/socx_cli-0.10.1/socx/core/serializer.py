from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Serializer[T](ABC):
    """Generic protocol for converting values into configuration payloads."""

    @classmethod
    @abstractmethod
    def serialize(cls, obj: T, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize obj as a ``dict`` instance."""
        ...
