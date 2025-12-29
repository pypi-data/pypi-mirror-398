"""Mixins that provide unique identifiers and weak references for objects."""

from __future__ import annotations

from typing import Any
from typing import ClassVar
from weakref import WeakValueDictionary
from threading import RLock
from dataclasses import field, dataclass
from collections.abc import MutableMapping


InstMapType = MutableMapping[int, "UIDBase"]


class _UIDMeta(type):
    """Metaclass for creating unique instance id mixin classes."""

    __lock: ClassVar[RLock] = RLock()
    __uid_map: ClassVar[dict[type, int]] = {}
    __inst_map: ClassVar[InstMapType] = WeakValueDictionary()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Assign a unique identifier to each created instance."""
        inst = super().__call__(*args, **kwargs)
        inst.__uid = cls._next_uid()
        cls.__inst_map[inst.__uid] = inst
        return inst

    def _next_uid(cls) -> int:
        """Compute the next unique identifier for ``cls`` instances."""
        with _UIDMeta.__lock:
            rv = cls.__uid_map.get(cls, 0)
            cls.__uid_map[cls] = rv + 1
        return rv

    @classmethod
    def _get_uid(cls, inst: UIDBase) -> int:
        """Return the unique identifier assigned to ``inst``."""
        return inst.__uid

    def _get_inst(cls, uid: int) -> UIDBase | None:
        """Return the instance associated with ``uid`` if it exists."""
        with cls.__lock:
            return cls.__inst_map.get(uid)


class UIDBase(metaclass=_UIDMeta):
    """Base class that stores the generated UID attribute."""

    __uid: int


class PtrMixin(UIDBase):
    """
    Pointer mixin class.

    Extending this class adds the `ref` property to subclass instances and the
    `dref` class method to the subclass.
    """

    @property
    def ref(self) -> int:
        """Return the object's assigned unique identifier."""
        return UIDBase._get_uid(self)

    @classmethod
    def dref(cls, ref: int) -> UIDBase | None:
        """Dereference a stored UID and return the tracked instance."""
        return UIDBase._get_inst(ref)


@dataclass
class UIDMixin(PtrMixin):
    """
    Unique instance ID mixin class.

    Extending this class assigns a unique instance id to all instances of the
    extending subclass.
    """

    uid: property = field(
        init=False,
        repr=True,
        default=property(lambda self: UIDBase._get_uid(self)),
    )
