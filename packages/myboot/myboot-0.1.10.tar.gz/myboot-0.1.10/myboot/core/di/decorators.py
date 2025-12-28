"""
依赖注入装饰器

提供 @inject 装饰器和 Provide 类型提示
"""

from typing import Any, TypeVar, Generic
from functools import wraps
import inspect

T = TypeVar('T')


class Provide(Generic[T]):
    """
    依赖提供者类型提示
    
    用于在类型注解中显式指定需要注入的服务名称
    
    Example:
        @service()
        class OrderService:
            @inject
            def __init__(
                self,
                user_service: Provide['user_service'],
                email_service: Provide['email_service']
            ):
                self.user_service = user_service
                self.email_service = email_service
    """
    def __class_getitem__(cls, item: str) -> str:
        """支持 Provide['service_name'] 语法"""
        return item


def inject(func):
    """
    依赖注入装饰器
    
    用于标记需要自动注入依赖的方法（通常是 __init__）
    
    Example:
        @service()
        class OrderService:
            @inject
            def __init__(self, user_service: UserService):
                self.user_service = user_service
    
    Note:
        如果使用类型注解，通常不需要显式使用 @inject 装饰器
        框架会自动检测并注入依赖
    """
    if not hasattr(func, '__myboot_inject__'):
        func.__myboot_inject__ = True
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper


def get_injectable_params(func) -> dict:
    """
    获取可注入的参数信息
    
    Args:
        func: 函数或方法
        
    Returns:
        参数字典，格式: {param_name: {type, service_name, is_optional, default}}
    """
    signature = inspect.signature(func)
    params = {}
    
    for param_name, param in signature.parameters.items():
        if param_name == 'self':
            continue
        
        param_type = param.annotation
        is_optional = False
        service_name = None
        
        # 处理类型注解
        if param_type != inspect.Parameter.empty:
            # 处理 Provide['service_name'] 类型（字符串形式）
            if isinstance(param_type, str):
                if param_type.startswith("Provide['") and param_type.endswith("']"):
                    service_name = param_type[9:-2]  # 提取 'service_name'
                    param_type = None
            # 处理类型对象
            elif hasattr(param_type, '__origin__'):
                origin = param_type.__origin__
                args = getattr(param_type, '__args__', ())
                
                # 处理 Optional[Type] 或 Union[Type, None]
                if origin is type(None) or (hasattr(origin, '__name__') and origin.__name__ == 'Union'):
                    # 取第一个非 None 的类型
                    for arg in args:
                        if arg is not type(None):
                            param_type = arg
                            is_optional = True
                            break
                
                # 处理 Provide[Type] 泛型
                if hasattr(origin, '__name__'):
                    origin_name = origin.__name__
                    if 'Provide' in origin_name or str(origin).startswith('typing.Union') and any('Provide' in str(arg) for arg in args):
                        # 查找 Provide 类型参数
                        for arg in args:
                            if isinstance(arg, str):
                                service_name = arg
                                param_type = None
                                break
                            elif hasattr(arg, '__origin__') and 'Provide' in str(arg):
                                # 处理嵌套的 Provide
                                nested_args = getattr(arg, '__args__', ())
                                if nested_args and isinstance(nested_args[0], str):
                                    service_name = nested_args[0]
                                    param_type = None
                                    break
        
        # 如果没有显式指定服务名，尝试从类型推断
        if service_name is None and param_type != inspect.Parameter.empty:
            if hasattr(param_type, '__name__'):
                # 将类名转换为服务名（驼峰转下划线）
                from myboot.core.decorators import _camel_to_snake
                service_name = _camel_to_snake(param_type.__name__)
            elif isinstance(param_type, type):
                # 处理直接的类型对象
                from myboot.core.decorators import _camel_to_snake
                service_name = _camel_to_snake(param_type.__name__)
        
        # 检查默认值（表示可选）
        if param.default != inspect.Parameter.empty:
            is_optional = True
        
        params[param_name] = {
            'type': param_type,
            'service_name': service_name,
            'is_optional': is_optional,
            'default': param.default if param.default != inspect.Parameter.empty else None
        }
    
    return params

