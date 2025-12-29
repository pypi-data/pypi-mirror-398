"""
gRPC 错误处理器

提供统一的错误处理、恢复策略和重试逻辑。
"""

import asyncio
import random
import grpc
import logging
from typing import Optional, Dict, Any, Callable, Union
from collections import defaultdict

from .core import get_protected_logger
from .exceptions import (
    ErrorContext, TamarModelException,
    NetworkException, ConnectionException, TimeoutException,
    AuthenticationException, TokenExpiredException, PermissionDeniedException,
    ValidationException, InvalidParameterException,
    RateLimitException, ProviderException,
    ERROR_CATEGORIES, RETRY_POLICY, ErrorStats
)

logger = get_protected_logger(__name__)


class GrpcErrorHandler:
    """统一的 gRPC 错误处理器"""

    def __init__(self, client_logger: Optional[logging.Logger] = None):
        self.logger = client_logger or logger
        self.error_stats = ErrorStats()

    def handle_error(self, error: Union[grpc.RpcError, Exception], context: dict) -> TamarModelException:
        """
        统一错误处理流程：
        1. 创建错误上下文
        2. 记录错误日志
        3. 更新错误统计
        4. 决定错误类型
        5. 返回相应异常
        """
        error_context = ErrorContext(error, context)

        # 记录详细错误日志
        # 将error_context的重要信息平铺到日志的data字段中
        log_data = {
            "log_type": "info",
            "request_id": error_context.request_id,
            "data": {
                "error_code": error_context.error_code.name if error_context.error_code else 'UNKNOWN',
                "error_message": error_context.error_message,
                "provider": error_context.provider,
                "model": error_context.model,
                "method": error_context.method,
                "retry_count": error_context.retry_count,
                "category": error_context._get_error_category(),
                "is_retryable": error_context._is_retryable(),
                "suggested_action": error_context._get_suggested_action(),
                "debug_string": error_context.error_debug_string,
                "is_network_cancelled": error_context.is_network_cancelled() if error_context.error_code == grpc.StatusCode.CANCELLED else None
            }
        }

        # 如果上下文中有 duration，添加到日志中
        if 'duration' in context:
            log_data['duration'] = context['duration']

        self.logger.error(
            f"❌ gRPC Error occurred: {error_context.error_code.name if error_context.error_code else 'UNKNOWN'}",
            extra=log_data
        )

        # 更新错误统计
        if error_context.error_code:
            self.error_stats.record_error(error_context.error_code)

        # 根据错误类型返回相应异常
        return self._create_exception(error_context)

    def _create_exception(self, error_context: ErrorContext) -> TamarModelException:
        """根据错误上下文创建相应的异常"""
        error_code = error_context.error_code

        if not error_code:
            return TamarModelException(error_context)

        # 认证相关错误
        if error_code in ERROR_CATEGORIES['AUTH']:
            if error_code == grpc.StatusCode.UNAUTHENTICATED:
                return TokenExpiredException(error_context)
            else:
                return PermissionDeniedException(error_context)

        # 网络相关错误
        elif error_code in ERROR_CATEGORIES['NETWORK']:
            if error_code == grpc.StatusCode.DEADLINE_EXCEEDED:
                return TimeoutException(error_context)
            else:
                return ConnectionException(error_context)

        # 验证相关错误
        elif error_code in ERROR_CATEGORIES['VALIDATION']:
            return InvalidParameterException(error_context)

        # 资源相关错误
        elif error_code == grpc.StatusCode.RESOURCE_EXHAUSTED:
            return RateLimitException(error_context)

        # 服务商相关错误
        elif error_code in ERROR_CATEGORIES['PROVIDER']:
            return ProviderException(error_context)

        # 默认错误
        else:
            return TamarModelException(error_context)

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.get_stats()

    def reset_stats(self):
        """重置错误统计"""
        self.error_stats.reset()


class ErrorRecoveryStrategy:
    """错误恢复策略"""

    RECOVERY_ACTIONS = {
        'refresh_token': 'handle_token_refresh',
        'reconnect': 'handle_reconnect',
        'backoff': 'handle_backoff',
        'circuit_break': 'handle_circuit_break',
    }

    def __init__(self, client):
        self.client = client

    async def recover_from_error(self, error_context: ErrorContext):
        """根据错误类型执行恢复动作"""
        if not error_context.error_code:
            return

        policy = RETRY_POLICY.get(error_context.error_code, {})

        if action := policy.get('action'):
            if action in self.RECOVERY_ACTIONS:
                handler = getattr(self, self.RECOVERY_ACTIONS[action])
                await handler(error_context)

    async def handle_token_refresh(self, error_context: ErrorContext):
        """处理 Token 刷新"""
        self.client.logger.info("🔄 Attempting to refresh JWT token")
        # 这里需要客户端实现 _refresh_jwt_token 方法
        if hasattr(self.client, '_refresh_jwt_token'):
            await self.client._refresh_jwt_token()

    async def handle_reconnect(self, error_context: ErrorContext):
        """处理重连"""
        self.client.logger.info("🔄 Attempting to reconnect channel")
        # 这里需要客户端实现 _reconnect_channel 方法
        if hasattr(self.client, '_reconnect_channel'):
            await self.client._reconnect_channel()

    async def handle_backoff(self, error_context: ErrorContext):
        """处理退避等待"""
        wait_time = self._calculate_backoff(error_context.retry_count)
        await asyncio.sleep(wait_time)

    async def handle_circuit_break(self, error_context: ErrorContext):
        """处理熔断"""
        self.client.logger.warning("⚠️ Circuit breaker activated")
        # 这里可以实现熔断逻辑
        pass

    def _calculate_backoff(self, retry_count: int) -> float:
        """计算退避时间"""
        base_delay = 1.0
        max_delay = 60.0
        jitter_factor = 0.1

        delay = min(base_delay * (2 ** retry_count), max_delay)
        jitter = random.uniform(0, delay * jitter_factor)
        return delay + jitter


class EnhancedRetryHandler:
    """增强的重试处理器"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_handler = GrpcErrorHandler()

    async def execute_with_retry(
            self,
            func: Callable,
            *args,
            context: Optional[Dict[str, Any]] = None,
            **kwargs
    ):
        """
        执行函数并处理重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            context: 请求上下文信息
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            TamarModelException: 包装后的异常
        """
        # 记录开始时间
        import time
        method_start_time = time.time()

        context = context or {}
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                context['retry_count'] = attempt
                return await func(*args, **kwargs)

            except (grpc.RpcError, grpc.aio.AioRpcError) as e:
                # 创建错误上下文
                error_context = ErrorContext(e, context)
                current_duration = time.time() - method_start_time
                context['duration'] = current_duration

                # 判断是否可以重试
                should_retry = self._should_retry(e, attempt)
                
                # 检查是否应该尝试快速降级（需要从外部注入client引用）
                should_try_fallback = False
                if hasattr(self.error_handler, 'client') and hasattr(self.error_handler.client, '_should_try_fallback'):
                    should_try_fallback = self.error_handler.client._should_try_fallback(e.code(), attempt)
                
                if should_try_fallback:
                    # 尝试快速降级到HTTP
                    logger.warning(
                        f"🚀 Fast fallback triggered for {e.code().name} after {attempt + 1} attempts",
                        extra={
                            "log_type": "fast_fallback",
                            "request_id": error_context.request_id,
                            "data": {
                                "error_code": e.code().name,
                                "attempt": attempt,
                                "fallback_reason": "immediate" if hasattr(self.error_handler.client, 'immediate_fallback_errors') and e.code() in self.error_handler.client.immediate_fallback_errors else "after_retries"
                            }
                        }
                    )
                    
                    try:
                        # 尝试HTTP降级（需要从context获取必要参数）
                        if hasattr(self.error_handler, 'client'):
                            # 检查是否是批量请求
                            if hasattr(self.error_handler.client, '_current_batch_request'):
                                batch_request = self.error_handler.client._current_batch_request
                                origin_request_id = getattr(self.error_handler.client, '_current_origin_request_id', None)
                                timeout = context.get('timeout')
                                request_id = context.get('request_id')
                                
                                # 尝试批量HTTP降级
                                result = await self.error_handler.client._invoke_batch_http_fallback(batch_request, timeout, request_id, origin_request_id)
                            elif hasattr(self.error_handler.client, '_current_model_request'):
                                model_request = self.error_handler.client._current_model_request
                                origin_request_id = getattr(self.error_handler.client, '_current_origin_request_id', None)
                                timeout = context.get('timeout')
                                request_id = context.get('request_id')
                                
                                # 尝试HTTP降级
                                result = await self.error_handler.client._invoke_http_fallback(model_request, timeout, request_id, origin_request_id)
                            
                            logger.info(
                                f"✅ Fast fallback to HTTP succeeded",
                                extra={
                                    "log_type": "fast_fallback_success",
                                    "request_id": request_id,
                                    "data": {
                                        "grpc_attempts": attempt + 1,
                                        "fallback_duration": time.time() - method_start_time
                                    }
                                }
                            )
                            
                            return result
                    except Exception as fallback_error:
                        # 降级失败，记录日志但继续原有重试逻辑
                        logger.warning(
                            f"⚠️ Fast fallback to HTTP failed: {str(fallback_error)}",
                            extra={
                                "log_type": "fast_fallback_failed",
                                "request_id": error_context.request_id,
                                "data": {
                                    "fallback_error": str(fallback_error),
                                    "will_continue_grpc_retry": should_retry and attempt < self.max_retries
                                }
                            }
                        )

                if not should_retry:
                    # 不可重试或已达到最大重试次数
                    # 记录最终失败日志
                    log_data = {
                        "log_type": "info",
                        "request_id": error_context.request_id,
                        "data": {
                            "error_code": error_context.error_code.name if error_context.error_code else 'UNKNOWN',
                            "error_message": error_context.error_message,
                            "retry_count": attempt,
                            "max_retries": self.max_retries,
                            "category": error_context._get_error_category(),
                            "is_retryable": False,
                            "method": error_context.method,
                            "final_failure": True
                        },
                        "duration": current_duration
                    }
                    error_detail = f" - {error_context.error_message}" if error_context.error_message else ""
                    logger.warning(
                        f"⚠️ Attempt {attempt + 1}/{self.max_retries + 1} failed: {e.code()}{error_detail} (no more retries)",
                        extra=log_data
                    )
                    last_exception = self.error_handler.handle_error(e, context)
                    break

                # 可以重试，记录重试日志
                log_data = {
                    "log_type": "info",
                    "request_id": error_context.request_id,
                    "data": {
                        "error_code": error_context.error_code.name if error_context.error_code else 'UNKNOWN',
                        "error_message": error_context.error_message,
                        "retry_count": attempt,
                        "max_retries": self.max_retries,
                        "category": error_context._get_error_category(),
                        "is_retryable": True,
                        "method": error_context.method,
                        "will_retry": True,
                        "fallback_attempted": should_try_fallback
                    },
                    "duration": current_duration
                }
                error_detail = f" - {error_context.error_message}" if error_context.error_message else ""
                logger.warning(
                    f"🔄 Attempt {attempt + 1}/{self.max_retries + 1} failed: {e.code()}{error_detail} (will retry)",
                    extra=log_data
                )

                # 执行退避等待
                if attempt < self.max_retries:
                    delay = self._calculate_backoff(attempt)
                    await asyncio.sleep(delay)

                # 保存异常，以备后续使用
                last_exception = e

            except Exception as e:
                # 非 gRPC 错误，直接包装抛出
                context['retry_count'] = attempt
                error_context = ErrorContext(None, context)
                error_context.error_message = str(e)
                last_exception = TamarModelException(error_context)
                break

        # 抛出最后的异常
        if last_exception:
            if isinstance(last_exception, TamarModelException):
                raise last_exception
            else:
                # 对于原始的 gRPC 异常，需要包装
                raise self.error_handler.handle_error(last_exception, context)
        else:
            raise TamarModelException("Unknown error occurred")

    def _should_retry(self, error: grpc.RpcError, attempt: int) -> bool:
        """判断是否应该重试"""
        error_code = error.code()
        policy = RETRY_POLICY.get(error_code, {})

        # 先检查错误级别的 max_attempts 配置
        # max_attempts 表示最大重试次数（不包括初始请求）
        error_max_attempts = policy.get('max_attempts', self.max_retries)
        if attempt >= error_max_attempts:
            return False

        # 再检查全局的 max_retries
        if attempt >= self.max_retries:
            return False

        # 检查基本重试策略
        retryable = policy.get('retryable', False)
        if retryable == False:
            return False
        elif retryable == True:
            return True
        elif retryable == 'conditional':
            # 条件重试，需要检查错误详情
            return self._check_conditional_retry(error)

        return False

    def _check_conditional_retry(self, error: grpc.RpcError) -> bool:
        """检查条件重试"""
        error_message = error.details().lower() if error.details() else ""

        # 一些可重试的内部错误模式
        retryable_patterns = [
            'temporary', 'timeout', 'unavailable',
            'connection', 'network', 'try again'
        ]

        for pattern in retryable_patterns:
            if pattern in error_message:
                return True

        return False

    def _calculate_backoff(self, attempt: int) -> float:
        """计算退避时间"""
        max_delay = 60.0
        jitter_factor = 0.1

        delay = min(self.base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0, delay * jitter_factor)
        return delay + jitter
