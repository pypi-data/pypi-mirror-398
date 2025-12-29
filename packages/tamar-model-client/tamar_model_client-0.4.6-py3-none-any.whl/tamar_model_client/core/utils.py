"""
Common utility functions for Tamar Model Client

This module contains shared utility functions used by both sync and async clients.
All functions in this module are pure functions without side effects.
"""

import base64
import uuid
from typing import Any, Iterable
from contextvars import ContextVar

from openai import NOT_GIVEN, Omit
from pydantic import BaseModel

# 使用 contextvars 管理请求ID，支持异步和同步上下文中的请求追踪
_request_id: ContextVar[str] = ContextVar('request_id', default='-')
_origin_request_id: ContextVar[str] = ContextVar('origin_request_id', default=None)


def is_effective_value(value) -> bool:
    """
    递归判断值是否为有效值

    用于过滤掉空值、None、NOT_GIVEN、Omit 等无意义的参数，
    确保只有有效的参数被发送到服务器。

    Args:
        value: 待检查的值

    Returns:
        bool: True 表示值有效，False 表示值无效

    处理的无效值类型：
    - None、NOT_GIVEN 和 Omit 实例
    - 空字符串（仅包含空白字符）
    - 空字节序列
    - 空字典（所有值都无效）
    - 空列表（所有元素都无效）
    """
    if value is None or value is NOT_GIVEN or isinstance(value, Omit):
        return False

    if isinstance(value, str):
        return value.strip() != ""

    if isinstance(value, bytes):
        return len(value) > 0

    if isinstance(value, dict):
        # 递归检查字典中的所有值
        for v in value.values():
            if is_effective_value(v):
                return True
        return False

    if isinstance(value, list):
        # 递归检查列表中的所有元素
        for item in value:
            if is_effective_value(item):
                return True
        return False

    # 其他类型（int/float/bool）只要不是 None 就算有效
    return True


def serialize_value(value, skip_effectiveness_check=False):
    """
    递归序列化值，处理各种复杂数据类型
    
    将 Pydantic 模型、字典、列表、字节等复杂类型转换为
    可以发送给 gRPC 服务的简单类型。
    
    Args:
        value: 待序列化的值
        skip_effectiveness_check: 是否跳过有效性检查，用于工具相关字段
        
    Returns:
        序列化后的值，如果值无效则返回 None
        
    支持的类型转换：
    - BaseModel -> dict (通过 model_dump)
    - bytes -> base64 字符串
    - dict -> 递归处理所有键值对
    - list -> 递归处理所有元素
    - 其他类型 -> 直接返回
    """
    if not skip_effectiveness_check and not is_effective_value(value):
        return None
    if isinstance(value, BaseModel):
        return serialize_value(value.model_dump(), skip_effectiveness_check)
    if hasattr(value, "dict") and callable(value.dict):
        return serialize_value(value.dict(), skip_effectiveness_check)
    if isinstance(value, dict):
        return {k: serialize_value(v, skip_effectiveness_check) for k, v in value.items()}
    if isinstance(value, list) or (isinstance(value, Iterable) and not isinstance(value, (str, bytes))):
        return [serialize_value(v, skip_effectiveness_check) for v in value]
    if isinstance(value, bytes):
        return f"bytes:{base64.b64encode(value).decode('utf-8')}"
    return value


def remove_none_from_dict(data: Any) -> Any:
    """
    递归清理数据结构中的 None 值
    
    遍历字典和列表，移除所有值为 None 的字段，
    确保发送给服务器的数据结构干净整洁。
    
    Args:
        data: 待清理的数据（dict、list 或其他类型）
        
    Returns:
        清理后的数据结构
        
    示例：
        >>> remove_none_from_dict({"a": 1, "b": None, "c": {"d": None, "e": 2}})
        {"a": 1, "c": {"e": 2}}
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if value is None:
                continue
            # 递归清理嵌套结构
            cleaned_value = remove_none_from_dict(value)
            new_dict[key] = cleaned_value
        return new_dict
    elif isinstance(data, list):
        # 递归处理列表中的每个元素
        return [remove_none_from_dict(item) for item in data]
    else:
        # 其他类型直接返回
        return data


def generate_request_id():
    """
    生成唯一的请求ID
    
    使用 UUID4 生成全局唯一的请求标识符，
    用于追踪和调试单个请求的生命周期。
    
    Returns:
        str: 格式为 "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx" 的UUID字符串
    """
    return str(uuid.uuid4())


def set_request_id(request_id: str):
    """
    设置当前上下文的请求ID
    
    在 ContextVar 中设置请求ID，使得在整个异步调用链中
    都能访问到同一个请求ID，便于日志追踪。
    
    Args:
        request_id: 要设置的请求ID字符串
    """
    _request_id.set(request_id)


def get_request_id() -> str:
    """
    获取当前上下文的请求ID
    
    从 ContextVar 中获取当前的请求ID，如果没有设置则返回默认值 '-'
    
    Returns:
        str: 当前的请求ID或默认值
    """
    return _request_id.get()


def set_origin_request_id(origin_request_id: str):
    """
    设置当前上下文的原始请求ID
    
    在 ContextVar 中设置原始请求ID，使得在整个异步调用链中
    都能访问到同一个原始请求ID，便于追踪请求来源。
    
    Args:
        origin_request_id: 要设置的原始请求ID字符串
    """
    _origin_request_id.set(origin_request_id)


def get_origin_request_id() -> str:
    """
    获取当前上下文的原始请求ID
    
    从 ContextVar 中获取当前的原始请求ID，如果没有设置则返回 None
    
    Returns:
        str: 当前的原始请求ID或 None
    """
    return _origin_request_id.get()