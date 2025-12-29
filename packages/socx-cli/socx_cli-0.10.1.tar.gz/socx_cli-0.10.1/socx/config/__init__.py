"""Aggregate configuration utilities and metadata for SoCX."""

__all__ = (
    # Schema
    "PluginModel",
    # Settings
    "SETTINGS_DEFAULTS",
    "Settings",
    "settings",
    "get_settings",
    "get_local_config_files",
    # Paths
    "PROJECT_ROOT_DIR",
    "PROJECT_ROOT_CONFIG",
    "USER_LOG_DIR",
    "USER_DATA_DIR",
    "USER_CACHE_DIR",
    "USER_STATE_DIR",
    "USER_CONFIG_DIR",
    "USER_RUNTIME_DIR",
    "USER_LOG_FILE",
    "USER_CONFIG_FILE",
    "LOCAL_CONFIG_FILE",
    "USER_LOG_FILENAME",
    "USER_CONFIG_FILENAME",
    "LOCAL_CONFIG_FILENAME",
    "APP_ROOT_DIR",
    "APP_STATIC_DIR",
    "APP_CONFIG_DIR",
    "APP_TEMPLATES_DIR",
    "APP_CONFIG_FILE",
    "APP_CONFIG_FILENAME",
    # Metadata
    "__author__",
    "__project__",
    "__version__",
    "__appname__",
    "__directory__",
    # Converters
    "Converter",
    "ShConverter",
    "PathConverter",
    "ImportConverter",
    "CompileConverter",
    "EvalConverter",
    "SymbolConverter",
    "CommandConverter",
    "IncludeConverter",
    "add_converters",
    "get_converters",
    # Validators
    "Validator",
    "ValidationError",
    "validate_all",
    # Formatters
    "Formatter",
    "TreeFormatter",
)


from socx.config.schema import PluginModel as PluginModel

from socx.config._settings import Settings as Settings
from socx.config._settings import SETTINGS_DEFAULTS as SETTINGS_DEFAULTS

from socx.config._config import settings as settings
from socx.config._config import get_settings as get_settings
from socx.config._config import (
    get_local_config_files as get_local_config_files,
)

from socx.config.paths import USER_LOG_DIR as USER_LOG_DIR
from socx.config.paths import USER_DATA_DIR as USER_DATA_DIR
from socx.config.paths import USER_CACHE_DIR as USER_CACHE_DIR
from socx.config.paths import USER_STATE_DIR as USER_STATE_DIR
from socx.config.paths import USER_CONFIG_DIR as USER_CONFIG_DIR
from socx.config.paths import USER_RUNTIME_DIR as USER_RUNTIME_DIR
from socx.config.paths import USER_LOG_FILE as USER_LOG_FILE
from socx.config.paths import USER_CONFIG_FILE as USER_CONFIG_FILE
from socx.config.paths import PROJECT_ROOT_DIR as PROJECT_ROOT_DIR
from socx.config.paths import PROJECT_ROOT_CONFIG as PROJECT_ROOT_CONFIG
from socx.config.paths import LOCAL_CONFIG_FILE as LOCAL_CONFIG_FILE
from socx.config.paths import USER_LOG_FILENAME as USER_LOG_FILENAME
from socx.config.paths import USER_CONFIG_FILENAME as USER_CONFIG_FILENAME
from socx.config.paths import LOCAL_CONFIG_FILENAME as LOCAL_CONFIG_FILENAME
from socx.config.paths import APP_ROOT_DIR as APP_ROOT_DIR
from socx.config.paths import APP_STATIC_DIR as APP_STATIC_DIR
from socx.config.paths import APP_CONFIG_DIR as APP_CONFIG_DIR
from socx.config.paths import APP_TEMPLATES_DIR as APP_TEMPLATES_DIR
from socx.config.paths import APP_CONFIG_FILE as APP_CONFIG_FILE
from socx.config.paths import APP_CONFIG_FILENAME as APP_CONFIG_FILENAME

from socx.config.metadata import __author__ as __author__
from socx.config.metadata import __project__ as __project__
from socx.config.metadata import __version__ as __version__
from socx.config.metadata import __appname__ as __appname__
from socx.config.metadata import __directory__ as __directory__

from socx.config.converters import Converter as Converter
from socx.config.converters import ShConverter as ShConverter
from socx.config.converters import PathConverter as PathConverter
from socx.config.converters import ImportConverter as ImportConverter
from socx.config.converters import CompileConverter as CompileConverter
from socx.config.converters import EvalConverter as EvalConverter
from socx.config.converters import SymbolConverter as SymbolConverter
from socx.config.converters import CommandConverter as CommandConverter
from socx.config.converters import IncludeConverter as IncludeConverter
from socx.config.converters import add_converters as add_converters
from socx.config.converters import get_converters as get_converters

from socx.config.validators import Validator as Validator
from socx.config.validators import ValidationError as ValidationError
from socx.config.validators import validate_all as validate_all

from socx.config.formatters import Formatter as Formatter
from socx.config.formatters import TreeFormatter as TreeFormatter
