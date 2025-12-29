"""Canonical filesystem paths used throughout SoCX."""

from __future__ import annotations

__all__ = (
    # Project Directories
    "PROJECT_ROOT_DIR",
    "PROJECT_ROOT_CONFIG",
    # User Directories
    "USER_LOG_DIR",
    "USER_DATA_DIR",
    "USER_CACHE_DIR",
    "USER_STATE_DIR",
    "USER_CONFIG_DIR",
    "USER_RUNTIME_DIR",
    # User Files
    "USER_LOG_FILE",
    "USER_CONFIG_FILE",
    "LOCAL_CONFIG_FILE",
    "USER_LOG_FILENAME",
    "USER_CONFIG_FILENAME",
    "LOCAL_CONFIG_FILENAME",
    # Application Directories
    "APP_ROOT_DIR",
    "APP_STATIC_DIR",
    "APP_CONFIG_DIR",
    "APP_TEMPLATES_DIR",
    # Application Files
    "APP_CONFIG_FILE",
    "APP_CONFIG_FILENAME",
)


# Project Directories
from socx.config._paths import PROJECT_ROOT_DIR as PROJECT_ROOT_DIR
from socx.config._paths import PROJECT_ROOT_CFG as PROJECT_ROOT_CONFIG

# User Directories
from socx.config._paths import USER_LOG_DIR as USER_LOG_DIR
from socx.config._paths import USER_DATA_DIR as USER_DATA_DIR
from socx.config._paths import USER_CACHE_DIR as USER_CACHE_DIR
from socx.config._paths import USER_STATE_DIR as USER_STATE_DIR
from socx.config._paths import USER_CONFIG_DIR as USER_CONFIG_DIR
from socx.config._paths import USER_RUNTIME_DIR as USER_RUNTIME_DIR

# User Files
from socx.config._paths import USER_LOG_FILE as USER_LOG_FILE
from socx.config._paths import USER_CONFIG_FILE as USER_CONFIG_FILE
from socx.config._paths import LOCAL_CONFIG_FILE as LOCAL_CONFIG_FILE
from socx.config._paths import USER_LOG_FILENAME as USER_LOG_FILENAME
from socx.config._paths import USER_CONFIG_FILENAME as USER_CONFIG_FILENAME
from socx.config._paths import LOCAL_CONFIG_FILENAME as LOCAL_CONFIG_FILENAME

# Application Directories
from socx.config._paths import APP_ROOT_DIR as APP_ROOT_DIR
from socx.config._paths import APP_STATIC_DIR as APP_STATIC_DIR
from socx.config._paths import APP_CONFIG_DIR as APP_CONFIG_DIR
from socx.config._paths import APP_TEMPLATES_DIR as APP_TEMPLATES_DIR

# Application Files
from socx.config._paths import APP_CONFIG_FILE as APP_CONFIG_FILE
from socx.config._paths import APP_CONFIG_FILENAME as APP_CONFIG_FILENAME
