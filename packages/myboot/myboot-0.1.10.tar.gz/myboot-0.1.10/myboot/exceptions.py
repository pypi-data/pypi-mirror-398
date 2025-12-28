"""
MyBoot 异常模块

提供框架相关的异常类
"""

from typing import Any, Dict, Optional


class MyBootException(Exception):
    """MyBoot 框架异常基类"""
    
    def __init__(
        self,
        message: str = "MyBoot 框架错误",
        code: str = "MYBOOT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(MyBootException):
    """配置错误异常"""
    
    def __init__(
        self,
        message: str = "配置错误",
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.config_key = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ValidationError(MyBootException):
    """验证错误异常"""
    
    def __init__(
        self,
        message: str = "验证失败",
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        self.value = value
        super().__init__(message, "VALIDATION_ERROR", details)


class InitializationError(MyBootException):
    """初始化错误异常"""
    
    def __init__(
        self,
        message: str = "初始化失败",
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.component = component
        super().__init__(message, "INITIALIZATION_ERROR", details)


class DependencyError(MyBootException):
    """依赖错误异常"""
    
    def __init__(
        self,
        message: str = "依赖错误",
        dependency: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.dependency = dependency
        super().__init__(message, "DEPENDENCY_ERROR", details)


class ServiceError(MyBootException):
    """服务错误异常"""
    
    def __init__(
        self,
        message: str = "服务错误",
        service: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.service = service
        super().__init__(message, "SERVICE_ERROR", details)


class JobError(MyBootException):
    """任务错误异常"""
    
    def __init__(
        self,
        message: str = "任务错误",
        job_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.job_name = job_name
        super().__init__(message, "JOB_ERROR", details)


class SchedulerError(MyBootException):
    """调度器错误异常"""
    
    def __init__(
        self,
        message: str = "调度器错误",
        scheduler: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.scheduler = scheduler
        super().__init__(message, "SCHEDULER_ERROR", details)


class MiddlewareError(MyBootException):
    """中间件错误异常"""
    
    def __init__(
        self,
        message: str = "中间件错误",
        middleware: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.middleware = middleware
        super().__init__(message, "MIDDLEWARE_ERROR", details)


class RouteError(MyBootException):
    """路由错误异常"""
    
    def __init__(
        self,
        message: str = "路由错误",
        route: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.route = route
        super().__init__(message, "ROUTE_ERROR", details)


class LifecycleError(MyBootException):
    """生命周期错误异常"""
    
    def __init__(
        self,
        message: str = "生命周期错误",
        phase: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.phase = phase
        super().__init__(message, "LIFECYCLE_ERROR", details)
