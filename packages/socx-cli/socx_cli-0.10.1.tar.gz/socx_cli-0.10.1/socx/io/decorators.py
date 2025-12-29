"""Decorator utilities for logging function entry and exit."""

import logging
from typing import Any
from inspect import signature
from collections.abc import Callable

from functools import wraps


__all__ = ("log_it",)


AnyCallable = Callable[..., Any]


def log_it(
    level: str | int = logging.DEBUG,
    logger: logging.Logger | None = None,
) -> Callable[[AnyCallable], AnyCallable]:
    """Add automatic entered/returned logging to decorated callables."""
    if isinstance(level, str):
        level_map: dict[str, int] = logging.getLevelNamesMapping()
        level = level_map[level]

    if logger is None:
        logger = logging.getLogger("socx-cli")

    def _log_it(f: AnyCallable) -> AnyCallable:
        sig = f"{f.__name__}{signature(f)}"

        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.log(level, f"[{sig}] entered.")
            rv = f(*args, **kwargs)
            logger.log(level, f"[{sig}] returned {rv}.")
            return rv

        return wrapper

    return _log_it
