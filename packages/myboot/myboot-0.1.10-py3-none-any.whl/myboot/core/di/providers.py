"""
服务提供者配置

定义服务的提供者配置和生命周期管理
"""

from typing import Any, Type, Optional
from dependency_injector import providers


class ServiceProvider:
    """服务提供者配置"""
    
    SINGLETON = 'singleton'
    FACTORY = 'factory'
    
    def __init__(
        self,
        service_class: Type,
        service_name: str,
        scope: str = SINGLETON,
        **kwargs
    ):
        """
        初始化服务提供者
        
        Args:
            service_class: 服务类
            service_name: 服务名称
            scope: 生命周期范围 (singleton/factory)
            **kwargs: 其他配置参数
        """
        self.service_class = service_class
        self.service_name = service_name
        self.scope = scope
        self.kwargs = kwargs
        self._provider: Optional[Any] = None
    
    def create_provider(self, dependencies: dict = None) -> Any:
        """
        创建 dependency_injector Provider
        
        Args:
            dependencies: 依赖的服务提供者字典
            
        Returns:
            dependency_injector Provider 实例
        """
        if self.scope == self.SINGLETON:
            if dependencies:
                self._provider = providers.Singleton(
                    self.service_class,
                    **dependencies
                )
            else:
                self._provider = providers.Singleton(self.service_class)
        else:
            if dependencies:
                self._provider = providers.Factory(
                    self.service_class,
                    **dependencies
                )
            else:
                self._provider = providers.Factory(self.service_class)
        
        return self._provider
    
    def get_provider(self) -> Any:
        """获取提供者实例"""
        return self._provider

