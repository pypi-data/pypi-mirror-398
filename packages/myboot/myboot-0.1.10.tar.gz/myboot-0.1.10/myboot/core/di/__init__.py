"""
依赖注入模块

提供基于 dependency_injector 的自动依赖注入功能
"""

from .container import DependencyContainer
from .registry import ServiceRegistry
from .decorators import inject, Provide

__all__ = [
    'DependencyContainer',
    'ServiceRegistry',
    'inject',
    'Provide',
]

