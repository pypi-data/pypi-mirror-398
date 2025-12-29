from __future__ import annotations

from typing import Any, TypeVar
from collections.abc import Callable

from rich_click import Command, Group


AnyCallable = Callable[..., Any]

FuncType = TypeVar("FuncType", bound=AnyCallable | Command | Group)

Decorator = Callable[[FuncType], FuncType]


def join_decorators(*args: Decorator) -> Decorator:
    """Compose multiple option decorators into a single decorator."""

    def _join_decorators(func):
        for arg in reversed(args):
            func = arg(func)
        return func

    return _join_decorators
