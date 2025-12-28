"""
核心基础设施模块

包含配置、数据库、日志、调度器等核心功能
"""

from .config import (
    get_settings,
    get_config,
    get_config_str,
    get_config_int,
    get_config_bool,
    reload_config
)
from .logger import Logger, get_logger, logger, setup_logging
from .scheduler import Scheduler, get_scheduler
from .auto_configuration import AutoConfigurationError

__all__ = [
    "get_settings",
    "get_config",
    "get_config_str",
    "get_config_int",
    "get_config_bool",
    "reload_config",
    "Logger",
    "get_logger",
    "logger",  # loguru logger，建议直接使用
    "setup_logging",
    "Scheduler",
    "get_scheduler",
    "AutoConfigurationError",
]