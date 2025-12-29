"""
Request ID 管理器

管理 request_id 的生成和追踪，支持为同一个原始 request_id 生成带序号的组合 ID。
"""

import threading
import time
from typing import Dict, Tuple, Optional


class RequestIdManager:
    """
    管理 request_id 的生成和追踪
    
    为同一个原始 request_id 生成带序号的组合 ID，如：
    - 原始 ID: abc-123
    - 第一次调用: abc-123-1
    - 第二次调用: abc-123-2
    
    包含自动清理机制，避免内存泄漏。
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        初始化 RequestIdManager
        
        Args:
            ttl_seconds: 计数器的生存时间（秒），默认 1 小时
        """
        self._counters: Dict[str, Dict[str, any]] = {}  # {origin_id: {'count': int, 'last_used': float}}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 每 5 分钟执行一次清理
        
    def get_composite_id(self, origin_id: str) -> Tuple[str, str]:
        """
        获取组合的 request_id
        
        Args:
            origin_id: 原始的 request_id
            
        Returns:
            tuple: (composite_request_id, origin_request_id)
                - composite_request_id: 带序号的组合 ID，如 "abc-123-1"
                - origin_request_id: 原始 ID，如 "abc-123"
        """
        with self._lock:
            current_time = time.time()
            
            # 定期清理过期的计数器
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_expired(current_time)
                self._last_cleanup = current_time
            
            # 获取或初始化计数器
            if origin_id not in self._counters:
                self._counters[origin_id] = {
                    'count': 0,
                    'last_used': current_time
                }
            
            # 递增计数
            self._counters[origin_id]['count'] += 1
            self._counters[origin_id]['last_used'] = current_time
            
            composite_id = f"{origin_id}-{self._counters[origin_id]['count']}"
            return composite_id, origin_id
    
    def _cleanup_expired(self, current_time: float):
        """
        清理过期的计数器
        
        Args:
            current_time: 当前时间戳
        """
        expired_ids = [
            origin_id for origin_id, info in self._counters.items()
            if current_time - info['last_used'] > self._ttl
        ]
        
        for origin_id in expired_ids:
            del self._counters[origin_id]
            
        # 如果计数器数量过多，保留最近使用的一半
        if len(self._counters) > 1000:
            sorted_items = sorted(
                self._counters.items(),
                key=lambda x: x[1]['last_used'],
                reverse=True
            )[:500]
            self._counters = dict(sorted_items)
    
    def get_stats(self) -> Dict[str, any]:
        """
        获取统计信息
        
        Returns:
            dict: 包含计数器数量等统计信息
        """
        with self._lock:
            return {
                'total_counters': len(self._counters),
                'ttl_seconds': self._ttl,
                'cleanup_interval': self._cleanup_interval
            }
    
    def clear(self):
        """清空所有计数器"""
        with self._lock:
            self._counters.clear()