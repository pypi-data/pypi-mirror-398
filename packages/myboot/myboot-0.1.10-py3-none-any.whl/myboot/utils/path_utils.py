"""
路径工具模块

提供项目根目录检测和路径解析功能。
"""

import os
from pathlib import Path


def get_project_root() -> str:
    """
    获取项目根目录
    
    从当前文件所在目录开始向上查找，直到找到包含pyproject.toml的目录。
    如果没找到，则使用当前工作目录。
    
    Returns:
        str: 项目根目录的绝对路径
    """
    current_dir = Path(__file__).parent.absolute()
    
    while current_dir.parent != current_dir:
        if (current_dir / 'pyproject.toml').exists():
            return str(current_dir)
        current_dir = current_dir.parent
    
    return os.getcwd()


def resolve_path(path: str) -> str:
    """
    解析路径，如果是相对路径则基于项目根目录
    
    Args:
        path (str): 要解析的路径，可以是相对路径或绝对路径
        
    Returns:
        str: 解析后的绝对路径
        
    Examples:
        >>> resolve_path('./data/file.csv')
        '/path/to/project/data/file.csv'
        
        >>> resolve_path('/absolute/path/file.csv')
        '/absolute/path/file.csv'
    """
    if os.path.isabs(path):
        return path
    
    # 清理路径，移除多余的./前缀
    clean_path = path.lstrip('./')
    return os.path.join(get_project_root(), clean_path)


def get_data_dir() -> str:
    """
    获取数据目录的绝对路径
    
    Returns:
        str: 数据目录的绝对路径
    """
    return resolve_path('data')


def get_conf_dir() -> str:
    """
    获取配置目录的绝对路径
    
    Returns:
        str: 配置目录的绝对路径
    """
    return resolve_path('conf')


def ensure_dir_exists(path: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path (str): 目录路径
        
    Returns:
        str: 目录的绝对路径
    """
    abs_path = resolve_path(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path
