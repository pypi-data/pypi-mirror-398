"""
Circuit Breaker implementation for resilient client

This module provides a thread-safe circuit breaker pattern implementation
to handle failures gracefully and prevent cascading failures.
"""

import time
import logging
from enum import Enum
from threading import Lock
from typing import Optional

from .core.logging_setup import get_protected_logger

logger = get_protected_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is broken, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreaker:
    """
    Thread-safe circuit breaker implementation
    
    The circuit breaker prevents cascading failures by failing fast when
    a service is unavailable, and automatically recovers when the service
    becomes available again.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize the circuit breaker
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = Lock()
        
    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if we should attempt recovery
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time > self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    logger.info("🔄 Circuit breaker entering HALF_OPEN state")
                    return False
                return True
            return False
    
    def record_success(self) -> None:
        """Record a successful request"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                # Success in half-open state means service has recovered
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("🔺 Circuit breaker recovered to CLOSED state")
            elif self.state == CircuitState.CLOSED and self.failure_count > 0:
                # Reset failure count on success
                self.failure_count = 0
    
    def record_failure(self, error_code=None) -> None:
        """
        Record a failed request
        
        Args:
            error_code: gRPC error code for failure classification
        """
        with self._lock:
            # 对于某些错误类型，不计入熔断统计或权重较低
            if error_code and self._should_ignore_for_circuit_breaker(error_code):
                return
                
            # ABORTED 错误权重较低，因为通常是瞬时的并发问题
            import grpc
            if error_code == grpc.StatusCode.ABORTED:
                # ABORTED 错误只计算半个失败
                self.failure_count += 0.5
            else:
                self.failure_count += 1
                
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    self.state = CircuitState.OPEN
                    logger.warning(
                        f"🔻 Circuit breaker OPENED after {self.failure_count} failures",
                        extra={
                            "log_type": "info",
                            "data": {
                                "failure_count": self.failure_count,
                                "threshold": self.failure_threshold,
                                "trigger_error": error_code.name if error_code else "unknown"
                            }
                        }
                    )
    
    def _should_ignore_for_circuit_breaker(self, error_code) -> bool:
        """
        判断错误是否应该被熔断器忽略
        
        某些错误不应该触发熔断：
        - 客户端主动取消的请求
        - 认证相关错误（不代表服务不可用）
        """
        import grpc
        ignored_codes = {
            grpc.StatusCode.UNAUTHENTICATED,    # 认证问题，不是服务问题
            grpc.StatusCode.PERMISSION_DENIED,  # 权限问题，不是服务问题
            grpc.StatusCode.INVALID_ARGUMENT,   # 参数错误，不是服务问题
        }
        return error_code in ignored_codes
    
    def should_fallback(self) -> bool:
        """Check if fallback should be used"""
        return self.is_open and self.state != CircuitState.HALF_OPEN
    
    def get_state(self) -> str:
        """Get current circuit state"""
        return self.state.value
    
    def reset(self) -> None:
        """Reset circuit breaker to initial state"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("🔄 Circuit breaker reset to CLOSED state")