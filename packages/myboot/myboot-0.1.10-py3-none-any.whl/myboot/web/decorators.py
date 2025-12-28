"""
Web 路由装饰器

提供类似 Spring Boot 的注解式路由功能
"""

from functools import wraps
from typing import Any, Callable, List, Optional

from pydantic import BaseModel


def route(
    path: str,
    methods: Optional[List[str]] = None,
    response_model: Optional[Any] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    通用路由装饰器
    
    Args:
        path: 路由路径
        methods: HTTP 方法列表
        response_model: 响应模型
        status_code: 状态码
        tags: 标签
        summary: 摘要
        description: 描述
        **kwargs: 其他 FastAPI 参数
    """
    if methods is None:
        methods = ["GET"]
    
    def decorator(func: Callable) -> Callable:
        # 添加路由元数据
        func._route_metadata = {
            'path': path,
            'methods': methods,
            'response_model': response_model,
            'status_code': status_code,
            'tags': tags or [],
            'summary': summary or func.__doc__ or "",
            'description': description or func.__doc__ or "",
            **kwargs
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get(
    path: str,
    response_model: Optional[Any] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """GET 路由装饰器"""
    return route(
        path=path,
        methods=["GET"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        **kwargs
    )


def post(
    path: str,
    response_model: Optional[Any] = None,
    status_code: int = 201,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """POST 路由装饰器"""
    return route(
        path=path,
        methods=["POST"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        **kwargs
    )


def put(
    path: str,
    response_model: Optional[Any] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """PUT 路由装饰器"""
    return route(
        path=path,
        methods=["PUT"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        **kwargs
    )


def delete(
    path: str,
    response_model: Optional[Any] = None,
    status_code: int = 204,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """DELETE 路由装饰器"""
    return route(
        path=path,
        methods=["DELETE"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        **kwargs
    )


def patch(
    path: str,
    response_model: Optional[Any] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """PATCH 路由装饰器"""
    return route(
        path=path,
        methods=["PATCH"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        **kwargs
    )


def validate_request(model: BaseModel) -> Callable:
    """
    请求验证装饰器
    
    Args:
        model: Pydantic 模型类
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以添加请求验证逻辑
            # 在实际应用中，FastAPI 会自动处理 Pydantic 模型验证
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_auth(roles: Optional[List[str]] = None) -> Callable:
    """
    身份验证装饰器
    
    Args:
        roles: 需要的角色列表
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以添加身份验证逻辑
            # 在实际应用中，可以集成 JWT、OAuth 等认证方式
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def rate_limit(requests: int = 100, window: int = 60) -> Callable:
    """
    限流装饰器
    
    Args:
        requests: 时间窗口内允许的请求数
        window: 时间窗口（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以添加限流逻辑
            # 在实际应用中，可以集成 Redis 等存储来实现分布式限流
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def cache(ttl: int = 300) -> Callable:
    """
    缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以添加缓存逻辑
            # 在实际应用中，可以集成 Redis、Memcached 等缓存系统
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_route(
    path: str,
    methods: Optional[List[str]] = None,
    response_model: Optional[Any] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    异步路由装饰器
    
    用于标记异步处理函数
    """
    if methods is None:
        methods = ["GET"]
    
    def decorator(func: Callable) -> Callable:
        # 添加路由元数据
        func._route_metadata = {
            'path': path,
            'methods': methods,
            'response_model': response_model,
            'status_code': status_code,
            'tags': tags or [],
            'summary': summary or func.__doc__ or "",
            'description': description or func.__doc__ or "",
            'async': True,
            **kwargs
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
