"""
日志管理模块

基于 loguru 的日志管理，提供初始化配置功能
所有代码可以直接使用: from loguru import logger
"""

import logging
import os
import sys
from typing import Optional, Union

from loguru import logger as loguru_logger
from dynaconf import Dynaconf

from .config import get_settings

logger = loguru_logger


def _get_worker_info() -> str:
    """
    获取当前 worker 信息
    
    Returns:
        worker 标识字符串，格式为 "Worker-1/4" 或 "Main" (主进程)
    """
    worker_id = os.environ.get("MYBOOT_WORKER_ID")
    worker_count = os.environ.get("MYBOOT_WORKER_COUNT")
    
    if worker_id and worker_count:
        return f"Worker-{worker_id}/{worker_count}"
    return "Main"  # Main process


def _get_log_format_with_worker() -> str:
    """
    获取带 worker 标识的日志格式
    
    Returns:
        日志格式字符串
    """
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<yellow>{extra[worker]}</yellow> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )


def _get_log_format_simple() -> str:
    """
    获取简单日志格式（无 worker 标识）
    
    Returns:
        日志格式字符串
    """
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )


def _parse_json_config(value) -> bool:
    """解析 JSON 配置值为布尔值"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def _convert_logging_format_to_loguru(user_format: str) -> str:
    """
    将标准 logging 格式转换为 loguru 格式
    
    Args:
        user_format: 用户提供的日志格式字符串
        
    Returns:
        转换后的 loguru 格式字符串
    """
    format_mapping = {
        "%(asctime)s": "{time:YYYY-MM-DD HH:mm:ss}",
        "%(name)s": "{name}",
        "%(levelname)s": "{level: <8}",
        "%(message)s": "{message}",
        "%(filename)s": "{file.name}",
        "%(funcName)s": "{function}",
        "%(lineno)d": "{line}",
    }
    
    result = user_format
    for old, new in format_mapping.items():
        result = result.replace(old, new)
    return result


def _build_json_handler_kwargs(log_level: str) -> tuple[dict, dict]:
    """
    构建 JSON 格式的 handler 参数
    
    Returns:
        (console_kwargs, file_kwargs) 元组
    """
    console_kwargs = {
        "sink": sys.stdout,
        "serialize": True,
        "level": log_level,
        "backtrace": True,
        "diagnose": True,
    }
    file_kwargs = {
        "serialize": True,
        "level": log_level,
        "rotation": "10 MB",
        "retention": "7 days",
        "compression": "zip",
        "backtrace": True,
        "diagnose": True,
    }
    return console_kwargs, file_kwargs


def _build_text_handler_kwargs(log_format: str, log_level: str) -> tuple[dict, dict]:
    """
    构建文本格式的 handler 参数
    
    Returns:
        (console_kwargs, file_kwargs) 元组
    """
    console_kwargs = {
        "sink": sys.stdout,
        "format": log_format,
        "level": log_level,
        "colorize": True,
        "backtrace": True,
        "diagnose": True,
    }
    file_kwargs = {
        "format": log_format,
        "level": log_level,
        "rotation": "10 MB",
        "retention": "7 days",
        "compression": "zip",
        "backtrace": True,
        "diagnose": True,
    }
    return console_kwargs, file_kwargs


def _get_third_party_config(config_obj) -> dict:
    """获取第三方库日志配置"""
    try:
        return config_obj.logging.third_party
    except (AttributeError, KeyError):
        pass
    
    try:
        return config_obj.get("logging.third_party", {})
    except (AttributeError, KeyError):
        return {}


def _configure_third_party_loggers(third_party_config: dict) -> None:
    """配置第三方库的日志级别"""
    if not isinstance(third_party_config, dict):
        return
    
    for logger_name, level_name in third_party_config.items():
        if isinstance(level_name, str):
            std_logger = logging.getLogger(logger_name)
            level = getattr(logging, level_name.upper(), logging.INFO)
            std_logger.setLevel(level)


def _add_file_handler(log_file: str, file_kwargs: dict) -> None:
    """添加文件日志 handler"""
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    loguru_logger.add(log_file, **file_kwargs)


def setup_logging(config: Optional[Union[str, Dynaconf]] = None, enable_worker_info: bool = True) -> None:
    """
    根据配置文件或配置对象初始化 loguru 日志系统
    
    Args:
        config: 配置文件路径或配置对象（Dynaconf），如果为 None 则使用默认配置
        enable_worker_info: 是否启用 worker 信息显示（多 worker 模式下自动启用）
    """
    # 获取配置对象
    config_obj = config if isinstance(config, Dynaconf) else get_settings(config)
    
    # 移除默认的 handler 并配置 worker 上下文
    loguru_logger.remove()
    loguru_logger.configure(extra={"worker": _get_worker_info()})
    
    # 获取日志级别
    log_level = config_obj.get("logging.level", "INFO").upper()
    
    # 构建 handler 参数
    use_json = _parse_json_config(config_obj.get("logging.json", False))
    if use_json:
        console_kwargs, file_kwargs = _build_json_handler_kwargs(log_level)
    else:
        # 确定日志格式
        user_format = config_obj.get("logging.format", None)
        if user_format:
            log_format = _convert_logging_format_to_loguru(user_format)
        else:
            worker_count = os.environ.get("MYBOOT_WORKER_COUNT")
            is_multi_worker = worker_count and int(worker_count) > 1
            log_format = _get_log_format_with_worker() if (is_multi_worker and enable_worker_info) else _get_log_format_simple()
        
        console_kwargs, file_kwargs = _build_text_handler_kwargs(log_format, log_level)
    
    # 添加 handlers
    loguru_logger.add(**console_kwargs)
    
    log_file = config_obj.get("logging.file")
    if log_file:
        _add_file_handler(log_file, file_kwargs)
    
    # 配置第三方库日志
    _configure_third_party_loggers(_get_third_party_config(config_obj))


def configure_worker_logger(worker_id: int, total_workers: int) -> None:
    """
    配置 worker 进程的日志上下文
    
    在多 worker 模式下，每个 worker 进程启动时调用此函数，
    以便在日志中显示 worker 标识
    
    Args:
        worker_id: Worker 进程 ID (从 1 开始)
        total_workers: 总 worker 数量
    """
    worker_info = f"Worker-{worker_id}/{total_workers}"
    loguru_logger.configure(extra={"worker": worker_info})


def setup_worker_logging(worker_id: int, total_workers: int) -> None:
    """
    为 worker 进程重新初始化日志系统
    
    在多 worker 模式下，每个 worker 进程启动后调用此函数，
    重新配置日志格式以显示 worker 标识
    
    Args:
        worker_id: Worker 进程 ID (从 1 开始)
        total_workers: 总 worker 数量
    """
    # 移除现有的 handler
    loguru_logger.remove()
    
    # 设置 worker 上下文
    worker_info = f"Worker-{worker_id}/{total_workers}"
    loguru_logger.configure(extra={"worker": worker_info})
    
    # 使用带 worker 标识的日志格式
    log_format = _get_log_format_with_worker()
    
    # 添加控制台输出 handler
    loguru_logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG",  # 使用 DEBUG，让应用配置控制实际级别
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


# 为了向后兼容，提供 get_logger 函数
# 但实际上直接使用 loguru 的 logger 即可
def get_logger(name: str = "app"):
    """
    获取日志器实例（向后兼容）
    
    注意：建议直接使用 `from loguru import logger`
    
    Args:
        name: 日志器名称（loguru 中用于标识，可通过 bind 方法绑定）
        
    Returns:
        loguru Logger 实例
    """
    return loguru_logger.bind(name=name)


# 为了向后兼容，提供 Logger 类
class Logger:
    """
    日志器类（向后兼容）
    
    注意：建议直接使用 `from loguru import logger`
    """
    
    def __init__(self, name: str = "app"):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
        """
        self.name = name
        self._logger = loguru_logger.bind(name=name)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """记录调试日志"""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """记录信息日志"""
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """记录警告日志"""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """记录错误日志"""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """记录严重错误日志"""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """记录异常日志"""
        self._logger.exception(message, *args, **kwargs)
