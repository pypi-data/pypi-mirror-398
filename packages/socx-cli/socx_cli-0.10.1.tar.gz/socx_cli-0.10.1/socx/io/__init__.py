"""Expose logging, console, and decorator utilities for I/O facilities."""

__all__ = (
    # Modules
    "log",
    # Constants
    "DEFAULT_LEVEL",
    "DEFAULT_FORMAT",
    "DEFAULT_HANDLERS",
    "DEFAULT_TIME_FORMAT",
    # Classes
    "Level",
    # Functions
    "log_it",
    "logger",
    "get_level",
    "set_level",
    "get_logger",
    "add_filter",
    "remove_filter",
    "add_handler",
    "get_handler",
    "has_handlers",
    "is_enabled_for",
    "remove_handler",
    "get_handler_names",
    # console
    "console",
    "get_console",
    "print_outputs",
    "print_with_pager",
    "print_command_outputs",
)

from socx.io import log as log

from socx.io.log import DEFAULT_LEVEL as DEFAULT_LEVEL
from socx.io.log import DEFAULT_FORMAT as DEFAULT_FORMAT
from socx.io.log import DEFAULT_HANDLERS as DEFAULT_HANDLERS
from socx.io.log import DEFAULT_TIME_FORMAT as DEFAULT_TIME_FORMAT
from socx.io.log import Level as Level
from socx.io.log import logger as logger
from socx.io.log import get_level as get_level
from socx.io.log import set_level as set_level
from socx.io.log import get_logger as get_logger
from socx.io.log import add_filter as add_filter
from socx.io.log import remove_filter as remove_filter
from socx.io.log import add_handler as add_handler
from socx.io.log import get_handler as get_handler
from socx.io.log import has_handlers as has_handlers
from socx.io.log import is_enabled_for as is_enabled_for
from socx.io.log import remove_handler as remove_handler
from socx.io.log import get_handler_names as get_handler_names

from socx.io.console import console as console
from socx.io.console import get_console as get_console
from socx.io.console import print_outputs as print_outputs
from socx.io.console import print_with_pager as print_with_pager
from socx.io.console import print_command_outputs as print_command_outputs

from socx.io.decorators import log_it as log_it
