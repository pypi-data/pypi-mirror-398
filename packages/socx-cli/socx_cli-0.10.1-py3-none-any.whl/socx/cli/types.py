"""Type aliases shared by the SoCX CLI implementation."""

from typing import Any
from typing import TypeVar
from collections.abc import Callable

from rich_click import Command, Group


FuncType = TypeVar("FuncType", bound=Callable[..., Any] | Command | Group)

GroupType = TypeVar("GroupType", bound=Group)

CommandType = TypeVar("CommandType", bound=Command)

AnyCallable = TypeVar("AnyCallable", bound=Callable[..., Any])

Decorator = Callable[[AnyCallable], FuncType]

GroupDecorator = Callable[[AnyCallable], GroupType]

CommandDecorator = Callable[[AnyCallable], CommandType]
