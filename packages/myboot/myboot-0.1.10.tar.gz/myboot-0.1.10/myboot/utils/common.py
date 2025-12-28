"""
公共工具函数

包含常用的工具函数和辅助方法
"""

import hashlib
import secrets
import socket
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from loguru import logger as loguru_logger

logger = loguru_logger.bind(name="utils")


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def get_local_ip() -> str:
    """获取本机真实 IP 地址"""
    try:
        # 连接到一个外部地址来获取本地 IP
        # 不实际发送数据，只是用于获取本地 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 连接到公共 DNS（不需要实际连接成功）
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        # 如果失败，尝试使用主机名
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            # 如果不是有效的 IP（可能是 127.0.0.1），返回 localhost
            if ip.startswith('127.'):
                return 'localhost'
            return ip
        except Exception:
            return 'localhost'


def generate_short_id(length: int = 8) -> str:
    """生成短ID"""
    return secrets.token_urlsafe(length)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的字符串
    """
    if dt is None:
        return ""
    
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式字符串
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        logger.warning(f"无法解析日期时间: {date_str}")
        return None


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def hash_password(password: str) -> str:
    """
    哈希密码
    
    Args:
        password: 原始密码
        
    Returns:
        str: 哈希后的密码
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{password_hash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    
    Args:
        password: 原始密码
        password_hash: 哈希后的密码
        
    Returns:
        bool: 是否匹配
    """
    try:
        salt, hash_value = password_hash.split(':')
        password_hash_check = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash_check.hex() == hash_value
    except ValueError:
        return False


def generate_token(length: int = 32) -> str:
    """
    生成随机令牌
    
    Args:
        length: 令牌长度
        
    Returns:
        str: 随机令牌
    """
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """生成API密钥"""
    return f"pk_{secrets.token_urlsafe(32)}"


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    遮蔽敏感数据
    
    Args:
        data: 原始数据
        mask_char: 遮蔽字符
        visible_chars: 可见字符数
        
    Returns:
        str: 遮蔽后的数据
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def safe_get(data: dict, key: str, default: any = None) -> any:
    """
    安全获取字典值
    
    Args:
        data: 字典数据
        key: 键，支持点号分隔的嵌套键
        default: 默认值
        
    Returns:
        any: 值或默认值
    """
    keys = key.split('.')
    value = data
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        list: 分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_none_values(data: dict) -> dict:
    """
    移除字典中的None值
    
    Args:
        data: 原始字典
        
    Returns:
        dict: 清理后的字典
    """
    return {k: v for k, v in data.items() if v is not None}


def deep_merge_dict(dict1: dict, dict2: dict) -> dict:
    """
    深度合并字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        dict: 合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def get_current_timestamp() -> int:
    """获取当前时间戳（毫秒）"""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的大小
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_valid_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL字符串
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


class RetryHelper:
    """重试辅助类"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
    
    def execute(self, func, *args, **kwargs):
        """执行带重试的函数"""
        import time
        
        last_exception = None
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(f"执行失败，{current_delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                    time.sleep(current_delay)
                    current_delay *= self.backoff_factor
                else:
                    logger.error(f"执行失败，已达到最大重试次数: {e}")
        
        raise last_exception
