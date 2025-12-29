"""
Logging configuration for Tamar Model Client

This module provides centralized logging setup for both sync and async clients.
It includes request ID tracking, JSON formatting, and consistent log configuration.
"""

import logging
import threading
from typing import Optional, Dict

from ..json_formatter import JSONFormatter
from .utils import get_request_id, get_origin_request_id

# gRPC 消息长度限制（32位系统兼容）
MAX_MESSAGE_LENGTH = 2 ** 31 - 1

# SDK 专用的 logger 名称前缀
TAMAR_LOGGER_PREFIX = "tamar_model_client"

# 线程安全的 logger 配置锁
_logger_lock = threading.Lock()

# 已配置的 logger 缓存
_configured_loggers: Dict[str, logging.Logger] = {}


class RequestIdFilter(logging.Filter):
    """
    自定义日志过滤器，向日志记录中添加 request_id
    
    这个过滤器从 ContextVar 中获取当前请求的 ID，
    并将其添加到日志记录中，便于追踪和调试。
    """

    def filter(self, record):
        """
        过滤日志记录，添加 request_id 字段
        
        Args:
            record: 日志记录对象
            
        Returns:
            bool: 总是返回 True，表示记录应被处理
        """
        # 从 ContextVar 中获取当前的 request_id
        record.request_id = get_request_id()
        
        # 添加 origin_request_id 到 data 字段
        origin_request_id = get_origin_request_id()
        if origin_request_id:
            # 确保 data 字段存在且是字典类型
            if not hasattr(record, 'data'):
                record.data = {}
            elif record.data is None:
                record.data = {}
            elif isinstance(record.data, dict):
                # 只有在 data 是字典且没有 origin_request_id 时才添加
                if 'origin_request_id' not in record.data:
                    record.data['origin_request_id'] = origin_request_id
            
        return True


class TamarLoggerAdapter:
    """
    Logger 适配器，确保 SDK 的日志格式不被外部修改
    
    这个适配器包装了原始的 logger，拦截所有的日志方法调用，
    确保使用正确的格式和处理器。
    """
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._lock = threading.Lock()
        
    def _ensure_format(self):
        """确保 logger 使用正确的格式"""
        with self._lock:
            # 检查并修复处理器
            for handler in self._logger.handlers[:]:
                if not isinstance(handler.formatter, JSONFormatter):
                    handler.setFormatter(JSONFormatter())
            
            # 确保 propagate 设置正确
            if self._logger.propagate:
                self._logger.propagate = False
    
    def _log(self, level, msg, *args, **kwargs):
        """统一的日志方法"""
        self._ensure_format()
        getattr(self._logger, level)(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self._log('error', msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self._log('critical', msg, *args, **kwargs)


def setup_logger(logger_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    设置并配置logger (保持向后兼容)
    
    为指定的logger配置处理器、格式化器和过滤器。
    如果logger已经有处理器，则不会重复配置。
    
    Args:
        logger_name: logger的名称
        level: 日志级别，默认为 INFO
        
    Returns:
        logging.Logger: 配置好的logger实例
        
    特性：
    - 使用 JSON 格式化器提供结构化日志输出
    - 添加请求ID过滤器用于请求追踪
    - 避免重复配置
    """
    # 确保 logger 名称以 SDK 前缀开始
    if not logger_name.startswith(TAMAR_LOGGER_PREFIX):
        logger_name = f"{TAMAR_LOGGER_PREFIX}.{logger_name}"
    
    with _logger_lock:
        # 检查缓存
        if logger_name in _configured_loggers:
            return _configured_loggers[logger_name]
        
        logger = logging.getLogger(logger_name)
        
        # 强制清除所有现有的处理器
        logger.handlers.clear()
        
        # 创建专用的控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        
        # 为处理器设置唯一标识，便于识别
        console_handler.name = f"tamar_handler_{id(console_handler)}"
        
        # 添加处理器
        logger.addHandler(console_handler)
        
        # 设置日志级别
        logger.setLevel(level)
        
        # 添加请求ID过滤器
        logger.addFilter(RequestIdFilter())
        
        # 关键设置：
        # 1. 不传播到父 logger
        logger.propagate = False
        
        # 2. 禁用外部修改（Python 3.8+）
        if hasattr(logger, 'disabled'):
            logger.disabled = False
        
        # 缓存配置好的 logger
        _configured_loggers[logger_name] = logger
        
        return logger


def get_protected_logger(logger_name: str, level: int = logging.INFO) -> TamarLoggerAdapter:
    """
    获取受保护的 logger
    
    返回一个 logger 适配器，确保日志格式不会被外部修改。
    
    Args:
        logger_name: logger的名称
        level: 日志级别，默认为 INFO
        
    Returns:
        TamarLoggerAdapter: 受保护的 logger 适配器
    """
    logger = setup_logger(logger_name, level)
    return TamarLoggerAdapter(logger)


def reset_logger_config(logger_name: str) -> None:
    """
    重置 logger 配置
    
    用于测试或需要重新配置的场景。
    
    Args:
        logger_name: logger的名称
    """
    if not logger_name.startswith(TAMAR_LOGGER_PREFIX):
        logger_name = f"{TAMAR_LOGGER_PREFIX}.{logger_name}"
    
    with _logger_lock:
        if logger_name in _configured_loggers:
            del _configured_loggers[logger_name]
            
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.filters.clear()