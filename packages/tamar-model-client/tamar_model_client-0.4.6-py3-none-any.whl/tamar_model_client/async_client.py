"""
Tamar Model Client 异步客户端实现

本模块实现了异步的 gRPC 客户端，用于与 Model Manager Server 进行通信。
支持单个请求、批量请求、流式响应等功能，并提供了完整的错误处理和重试机制。

主要功能：
- 异步 gRPC 通信
- JWT 认证
- 自动重试和错误处理
- 流式响应支持
- 连接池管理
- 详细的日志记录

使用示例：
    async with AsyncTamarModelClient() as client:
        request = ModelRequest(...)
        response = await client.invoke(request)
"""

import asyncio
import atexit
import json
import logging
import random
import time
from typing import Optional, AsyncIterator, Union

import grpc
from grpc import RpcError

from .core import (
    generate_request_id,
    set_request_id,
    set_origin_request_id,
    get_protected_logger,
    MAX_MESSAGE_LENGTH,
    get_request_id,
    RequestIdManager
)
from .core.base_client import BaseClient
from .core.request_builder import RequestBuilder
from .core.response_handler import ResponseHandler
from .core.async_channel_pool import AsyncChannelPool
from .enums import ProviderType, InvokeType
from .exceptions import ConnectionError, TamarModelException
from .error_handler import EnhancedRetryHandler
from .schemas import ModelRequest, ModelResponse, BatchModelRequest, BatchModelResponse, TaskStatusResponse, BatchTaskStatusResponse
from .generated import model_service_pb2, model_service_pb2_grpc
from .core.http_fallback import AsyncHttpFallbackMixin

# 配置日志记录器（使用受保护的logger）
logger = get_protected_logger(__name__)


class AsyncTamarModelClient(BaseClient, AsyncHttpFallbackMixin):
    """
    Tamar Model Client 异步客户端
    
    提供与 Model Manager Server 的异步通信能力，支持：
    - 单个和批量模型调用
    - 流式和非流式响应
    - 自动重试和错误恢复
    - JWT 认证
    - 连接池管理
    
    使用示例：
        # 基本用法
        client = AsyncTamarModelClient()
        await client.connect()
        
        request = ModelRequest(...)
        response = await client.invoke(request)
        
        # 上下文管理器用法（推荐）
        async with AsyncTamarModelClient() as client:
            response = await client.invoke(request)
    
    环境变量配置：
        MODEL_MANAGER_SERVER_ADDRESS: gRPC 服务器地址
        MODEL_MANAGER_SERVER_JWT_SECRET_KEY: JWT 密钥
        MODEL_MANAGER_SERVER_GRPC_USE_TLS: 是否使用 TLS
        MODEL_MANAGER_SERVER_GRPC_MAX_RETRIES: 最大重试次数
        MODEL_MANAGER_SERVER_GRPC_RETRY_DELAY: 重试延迟
    """

    def __init__(self, **kwargs):
        """
        初始化异步客户端
        
        参数继承自 BaseClient，包括：
        - server_address: gRPC 服务器地址
        - jwt_secret_key: JWT 签名密钥
        - jwt_token: 预生成的 JWT 令牌
        - default_payload: JWT 令牌的默认载荷
        - token_expires_in: JWT 令牌过期时间
        - max_retries: 最大重试次数
        - retry_delay: 初始重试延迟
        """
        super().__init__(logger_name=__name__, **kwargs)

        # === 连接池管理 ===
        self.channel_pool: Optional[AsyncChannelPool] = None
        self._pool_enabled = self._should_use_pool()

        # === 单连接模式（向后兼容）===
        # 仅在 pool_size=1 时使用
        if not self._pool_enabled:
            self.channel: Optional[grpc.aio.Channel] = None
            self.stub: Optional[model_service_pb2_grpc.ModelServiceStub] = None
        else:
            self.channel = None
            self.stub = None

        self._channel_error_count = 0
        self._last_channel_error_time = None
        
        # === Request ID 管理 ===
        self._request_id_manager = RequestIdManager()
        
        # === 增强的重试处理器 ===
        self.retry_handler = EnhancedRetryHandler(
            max_retries=self.max_retries,
            base_delay=self.retry_delay
        )
        
        # 设置client引用，用于快速降级
        self.retry_handler.error_handler.client = self
        
        # 注册退出时的清理函数
        atexit.register(self._cleanup_atexit)

    def _cleanup_atexit(self):
        """程序退出时的清理函数"""
        if self.channel and not self._closed:
            try:
                asyncio.create_task(self.close())
            except RuntimeError:
                # 如果事件循环已经关闭，忽略错误
                pass

    async def close(self):
        """
        关闭客户端连接

        优雅地关闭 gRPC 通道并清理资源。
        建议在程序结束前调用此方法，或使用上下文管理器自动管理。
        """
        if not self._closed:
            # 关闭连接池（如果启用）
            if self._pool_enabled and self.channel_pool:
                await self.channel_pool.close()
                logger.info("🔒 Async connection pool closed",
                            extra={"log_type": "info", "data": {"status": "closed", "pool_enabled": True}})
            # 关闭单连接（如果存在）
            elif self.channel:
                await self.channel.close()
                logger.info("🔒 gRPC channel closed",
                            extra={"log_type": "info", "data": {"status": "closed", "pool_enabled": False}})

            self._closed = True

        # 清理 HTTP session（如果有）
        if self.resilient_enabled:
            await self._cleanup_http_session()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    def __enter__(self):
        """同步上下文管理器入口（不支持）"""
        raise TypeError("Use 'async with' for AsyncTamarModelClient")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口（不支持）"""
        pass

    async def connect(self):
        """
        显式连接到服务器
        
        建立与 gRPC 服务器的连接。通常不需要手动调用，
        因为 invoke 方法会自动确保连接已建立。
        """
        await self._ensure_initialized()

    async def _ensure_initialized(self):
        """
        初始化gRPC通道或连接池

        根据配置选择初始化连接池（多连接）或单连接。

        连接池模式（pool_size > 1）:
        - 创建多个 gRPC channel
        - 自动负载均衡和健康检查
        - 提升并发性能和稳定性

        单连接模式（pool_size = 1）:
        - 传统单 channel 模式
        - 向后兼容

        连接配置包括：
        - 消息大小限制
        - HTTP/2 窗口配置（1MB流窗口，16MB连接窗口）
        - Keepalive设置（60秒ping间隔，10秒超时）
        - 连接生命周期管理（1小时最大连接时间）
        - 性能优化选项（关闭BDP探测，启用内置重试）

        Raises:
            ConnectionError: 当达到最大重试次数仍无法连接时
        """
        # === 连接池模式 ===
        if self._pool_enabled:
            if self.channel_pool:
                return  # 连接池已初始化

            try:
                options = self.build_channel_options()
                self.channel_pool = AsyncChannelPool(
                    pool_size=self.pool_size,
                    server_address=self.server_address,
                    channel_options=options,
                    use_tls=self.use_tls,
                    stub_class=model_service_pb2_grpc.ModelServiceStub,
                    logger=logger
                )
                await self.channel_pool.initialize()
                return
            except Exception as e:
                logger.error(
                    f"❌ Failed to initialize async connection pool: {e}",
                    exc_info=True,
                    extra={"log_type": "pool_init"}
                )
                raise ConnectionError(f"Failed to initialize async connection pool: {e}") from e

        # === 单连接模式 ===
        if self.channel and self.stub and await self._is_channel_healthy():
            return

        # 如果 channel 存在但不健康，记录日志
        if self.channel and self.stub:
            logger.warning(
                "⚠️ Channel exists but unhealthy, will recreate",
                extra={
                    "log_type": "channel_recreate",
                    "data": {
                        "channel_error_count": self._channel_error_count,
                        "time_since_last_error": time.time() - self._last_channel_error_time if self._last_channel_error_time else None
                    }
                }
            )
            await self._recreate_channel()

        retry_count = 0
        options = self.build_channel_options()

        while retry_count <= self.max_retries:
            try:
                if self.use_tls:
                    credentials = grpc.ssl_channel_credentials()
                    self.channel = grpc.aio.secure_channel(
                        self.server_address,
                        credentials,
                        options=options
                    )
                    logger.info("🔐 Using secure gRPC channel (TLS enabled)",
                                extra={"log_type": "info",
                                       "data": {"tls_enabled": True, "server_address": self.server_address}})
                else:
                    self.channel = grpc.aio.insecure_channel(
                        f"dns:///{self.server_address}",
                        options=options
                    )
                    logger.info("🔓 Using insecure gRPC channel (TLS disabled)",
                                extra={"log_type": "info",
                                       "data": {"tls_enabled": False, "server_address": self.server_address}})

                await self.channel.channel_ready()
                self.stub = model_service_pb2_grpc.ModelServiceStub(self.channel)
                logger.info(f"✅ gRPC channel initialized to {self.server_address}",
                            extra={"log_type": "info",
                                   "data": {"status": "success", "server_address": self.server_address}})
                return

            except grpc.FutureTimeoutError as e:
                logger.error(f"❌ gRPC channel initialization timed out: {str(e)}", exc_info=True,
                             extra={"log_type": "info",
                                    "data": {"error_type": "timeout", "server_address": self.server_address}})
            except grpc.RpcError as e:
                logger.error(f"❌ gRPC channel initialization failed: {str(e)}", exc_info=True,
                             extra={"log_type": "info",
                                    "data": {"error_type": "grpc_error", "server_address": self.server_address}})
            except Exception as e:
                logger.error(f"❌ Unexpected error during gRPC channel initialization: {str(e)}", exc_info=True,
                             extra={"log_type": "info",
                                    "data": {"error_type": "unknown", "server_address": self.server_address}})

            retry_count += 1
            if retry_count <= self.max_retries:
                await asyncio.sleep(self.retry_delay * retry_count)

        raise ConnectionError(f"Failed to connect to {self.server_address} after {self.max_retries} retries")
    
    async def _is_channel_healthy(self) -> bool:
        """
        检查 channel 是否健康
        
        Returns:
            bool: True 如果 channel 健康，False 如果需要重建
        """
        if not self.channel:
            return False
            
        try:
            # 检查 channel 状态
            state = self.channel.get_state()
            
            # 如果处于关闭或失败状态，需要重建
            if state in [grpc.ChannelConnectivity.SHUTDOWN, 
                        grpc.ChannelConnectivity.TRANSIENT_FAILURE]:
                logger.warning(f"⚠️ Channel in unhealthy state: {state}",
                             extra={"log_type": "info", 
                                   "data": {"channel_state": str(state)}})
                return False
                
            # 快速失败检测：如果连续立即失败，说明连接已坏
            # 降低阈值，更快标记问题连接
            if self._channel_error_count > 2 and self._last_channel_error_time:
                time_since_error = time.time() - self._last_channel_error_time
                # 30秒内超过2次错误，说明连接有问题
                if time_since_error < 30:
                    logger.warning(
                        "⚠️ Too many channel errors recently, marking as unhealthy",
                        extra={
                            "log_type": "info",
                            "data": {
                                "error_count": self._channel_error_count,
                                "time_window": time_since_error
                            }
                        }
                    )
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking channel health: {e}",
                        extra={"log_type": "info", 
                              "data": {"error": str(e)}})
            return False
    
    async def _recreate_channel(self):
        """
        重建 gRPC channel
        
        关闭旧的 channel 并创建新的连接
        """
        # 关闭旧 channel
        if self.channel:
            try:
                await self.channel.close()
                logger.info("🔚 Closed unhealthy channel",
                          extra={"log_type": "info"})
            except Exception as e:
                logger.warning(f"⚠️ Error closing channel: {e}",
                             extra={"log_type": "info"})
                
        # 清空引用
        self.channel = None
        self.stub = None
        
        # 重置错误计数
        self._channel_error_count = 0
        self._last_channel_error_time = None
        
        logger.info("🔄 Recreating gRPC channel...",
                   extra={"log_type": "info"})
    
    def _record_channel_error(self, error: grpc.RpcError):
        """
        记录 channel 错误，用于健康检查

        如果启用了连接池，会同步记录到连接池的健康检查系统。

        Args:
            error: gRPC 错误
        """
        self._channel_error_count += 1
        self._last_channel_error_time = time.time()

        # 如果启用了连接池，记录到连接池
        if self._pool_enabled and self.channel_pool:
            # 异步记录到连接池（不阻塞）
            try:
                asyncio.create_task(self.channel_pool.record_error(error))
            except Exception:
                pass  # 不让健康检查失败影响主流程

        # 获取当前 channel 状态（单连接模式）
        channel_state = None
        if not self._pool_enabled and self.channel:
            try:
                channel_state = self.channel.get_state()
            except:
                channel_state = "UNKNOWN"

        # 对于严重错误，增加错误权重
        if error.code() in [grpc.StatusCode.INTERNAL,
                           grpc.StatusCode.UNAVAILABLE]:
            self._channel_error_count += 2

        # 记录详细的错误信息
        logger.warning(
            f"⚠️ Channel error recorded: {error.code().name}",
            extra={
                "log_type": "channel_error",
                "data": {
                    "error_code": error.code().name,
                    "error_count": self._channel_error_count,
                    "pool_enabled": self._pool_enabled,
                    "channel_state": str(channel_state) if channel_state else "NO_CHANNEL",
                    "time_since_last_error": time.time() - self._last_channel_error_time if self._last_channel_error_time else 0,
                    "error_details": error.details() if hasattr(error, 'details') else "",
                    "debug_string": error.debug_error_string() if hasattr(error, 'debug_error_string') else ""
                }
            }
        )

    async def _retry_request(self, func, *args, **kwargs):
        """
        使用增强的重试处理器执行请求
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            TamarModelException: 当所有重试都失败时
        """
        # 从kwargs中提取request_id（如果有的话），然后移除它
        request_id = kwargs.pop('request_id', None) or get_request_id()
        
        # 构建包含request_id的上下文
        context = {
            'method': func.__name__ if hasattr(func, '__name__') else 'unknown',
            'client_version': 'async',
            'request_id': request_id,
        }
        return await self.retry_handler.execute_with_retry(func, *args, context=context, **kwargs)

    async def _retry_request_stream(self, func, *args, **kwargs):
        """
        流式请求的重试逻辑
        
        对于流式响应，需要特殊的重试处理，因为流不能简单地重新执行。
        
        Args:
            func: 生成流的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            AsyncIterator: 流式响应迭代器
        """
        # 记录方法开始时间
        import time
        method_start_time = time.time()
        
        # 从kwargs中提取request_id（如果有的话），然后移除它
        request_id = kwargs.pop('request_id', None) or get_request_id()
        
        last_exception = None
        context = {
            'method': 'stream',
            'client_version': 'async',
            'request_id': request_id,
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                context['retry_count'] = attempt
                # 尝试创建流
                async for item in func(*args, **kwargs):
                    yield item
                return
                
            except RpcError as e:
                # 使用智能重试判断
                context['retry_count'] = attempt
                
                # 创建错误上下文并判断是否应该重试
                from .exceptions import ErrorContext, get_retry_policy
                error_context = ErrorContext(e, context)
                error_code = e.code()
                policy = get_retry_policy(error_code)

                # 特殊处理 UNAUTHENTICATED 错误：尝试刷新 token
                if error_code == grpc.StatusCode.UNAUTHENTICATED:
                    # 尝试刷新 token
                    token_refreshed = self.force_refresh_token()
                    if token_refreshed and attempt < 1:
                        # Token 刷新成功，允许重试（只重试一次）
                        should_retry = True
                    else:
                        # Token 无法刷新或已重试过，不再重试
                        should_retry = False
                # 先检查错误级别的 max_attempts 配置
                # max_attempts 表示最大重试次数（不包括初始请求）
                elif attempt >= policy.get('max_attempts', self.max_retries):
                    should_retry = False
                elif attempt >= self.max_retries:
                    should_retry = False
                else:
                    retryable = policy.get('retryable', False)
                    if retryable == True:
                        should_retry = True
                    elif retryable == 'conditional':
                        # 条件重试，特殊处理 CANCELLED
                        if error_code == grpc.StatusCode.CANCELLED:
                            # 获取 channel 状态信息
                            channel_state = None
                            if self.channel:
                                try:
                                    channel_state = self.channel.get_state()
                                except:
                                    channel_state = "UNKNOWN"
                            
                            is_network_cancelled = error_context.is_network_cancelled()
                            
                            logger.warning(
                                f"⚠️ CANCELLED error in stream, channel state: {channel_state}",
                                extra={
                                    "log_type": "cancelled_debug",
                                    "request_id": context.get('request_id'),
                                    "data": {
                                        "channel_state": str(channel_state) if channel_state else "NO_CHANNEL",
                                        "channel_error_count": self._channel_error_count,
                                        "time_since_last_error": time.time() - self._last_channel_error_time if self._last_channel_error_time else None,
                                        "channel_healthy": await self._is_channel_healthy(),
                                        "is_network_cancelled": is_network_cancelled,
                                        "debug_string": e.debug_error_string() if hasattr(e, 'debug_error_string') else ""
                                    }
                                }
                            )
                            
                            should_retry = is_network_cancelled
                        else:
                            should_retry = self._check_error_details_for_retry(e)
                    else:
                        should_retry = False
                
                if should_retry:
                    current_duration = time.time() - method_start_time
                    log_data = {
                        "log_type": "info",
                        "request_id": context.get('request_id'),
                        "data": {
                            "error_code": e.code().name if e.code() else 'UNKNOWN',
                            "error_details": e.details() if hasattr(e, 'details') else '',
                            "retry_count": attempt,
                            "max_retries": self.max_retries,
                            "method": "stream"
                        },
                        "duration": current_duration
                    }
                    error_detail = f" - {e.details()}" if e.details() else ""
                    logger.warning(
                        f"🔄 Attempt {attempt + 1}/{self.max_retries + 1} failed: {e.code()}{error_detail} (will retry)",
                        extra=log_data
                    )
                    
                    # 计算退避时间
                    delay = self._calculate_backoff(attempt, error_code)
                    await asyncio.sleep(delay)
                else:
                    # 不重试或已达到最大重试次数
                    current_duration = time.time() - method_start_time
                    log_data = {
                        "log_type": "info",
                        "request_id": context.get('request_id'),
                        "data": {
                            "error_code": e.code().name if e.code() else 'UNKNOWN',
                            "error_details": e.details() if hasattr(e, 'details') else '',
                            "retry_count": attempt,
                            "max_retries": self.max_retries,
                            "method": "stream",
                            "will_retry": False
                        },
                        "duration": current_duration
                    }
                    error_detail = f" - {e.details()}" if e.details() else ""
                    logger.warning(
                        f"⚠️ Attempt {attempt + 1}/{self.max_retries + 1} failed: {e.code()}{error_detail} (no more retries)",
                        extra=log_data
                    )
                    context['duration'] = current_duration
                    last_exception = self.error_handler.handle_error(e, context)
                    # 记录 channel 错误
                    self._record_channel_error(e)
                    break
                    
                last_exception = e
                
            except Exception as e:
                context['retry_count'] = attempt
                raise TamarModelException(str(e)) from e
        
        if last_exception:
            if isinstance(last_exception, TamarModelException):
                raise last_exception
            else:
                raise self.error_handler.handle_error(last_exception, context)
        else:
            raise TamarModelException("Unknown streaming error occurred")

    def _check_error_details_for_retry(self, error: RpcError) -> bool:
        """检查错误详情决定是否重试"""
        error_message = error.details().lower() if error.details() else ""
        
        # 可重试的错误模式
        retryable_patterns = [
            'temporary', 'timeout', 'unavailable', 
            'connection', 'network', 'try again'
        ]
        
        for pattern in retryable_patterns:
            if pattern in error_message:
                return True
                
        return False
    
    def _calculate_backoff(self, attempt: int, error_code = None) -> float:
        """
        计算退避时间，支持不同的退避策略
        
        Args:
            attempt: 当前重试次数
            error_code: gRPC错误码，用于确定退避策略
        """
        max_delay = 60.0
        base_delay = self.retry_delay
        
        # 获取错误的重试策略
        if error_code:
            from .exceptions import get_retry_policy
            policy = get_retry_policy(error_code)
            backoff_type = policy.get('backoff', 'exponential')
            use_jitter = policy.get('jitter', False)
        else:
            backoff_type = 'exponential'
            use_jitter = False
        
        # 根据退避类型计算延迟
        if backoff_type == 'linear':
            # 线性退避：delay * (attempt + 1)
            delay = min(base_delay * (attempt + 1), max_delay)
        else:
            # 指数退避：delay * 2^attempt
            delay = min(base_delay * (2 ** attempt), max_delay)
        
        # 添加抖动
        if use_jitter:
            jitter_factor = 0.2  # 增加抖动范围，减少竞争
            jitter = random.uniform(0, delay * jitter_factor)
            delay += jitter
        else:
            # 默认的小量抖动，避免完全同步
            jitter_factor = 0.05
            jitter = random.uniform(0, delay * jitter_factor)
            delay += jitter
            
        return delay

    async def _stream(self, request, metadata, invoke_timeout, request_id=None, origin_request_id=None) -> AsyncIterator[ModelResponse]:
        """
        处理流式响应

        包含块级超时保护，防止流式响应挂起。

        Args:
            request: gRPC 请求对象
            metadata: 请求元数据（为了兼容性保留，但会被忽略）
            invoke_timeout: 总体超时时间
            request_id: 请求ID
            origin_request_id: 原始请求ID

        Yields:
            ModelResponse: 流式响应的每个数据块

        Raises:
            TimeoutError: 当等待下一个数据块超时时
        """
        # 获取 stub（连接池或单连接）
        if self._pool_enabled:
            stub = await self.channel_pool.get_stub()
        else:
            stub = self.stub

        # 每次调用时重新生成metadata，确保JWT token是最新的
        fresh_metadata = self._build_auth_metadata(
            request_id or get_request_id(),
            origin_request_id
        )
        stream_iter = stub.Invoke(request, metadata=fresh_metadata, timeout=invoke_timeout).__aiter__()
        chunk_timeout = self.stream_chunk_timeout  # 单个数据块的超时时间
        
        try:
            while True:
                try:
                    # 对每个数据块的获取进行超时保护
                    response = await asyncio.wait_for(
                        stream_iter.__anext__(), 
                        timeout=chunk_timeout
                    )
                    yield ResponseHandler.build_model_response(response)
                    
                except asyncio.TimeoutError:
                    raise TimeoutError(f"流式响应在等待下一个数据块时超时 ({chunk_timeout}s)")
                    
                except StopAsyncIteration:
                    break  # 正常结束
        except Exception as e:
            raise

    async def _stream_with_logging(self, request, metadata, invoke_timeout, start_time, model_request, request_id=None, origin_request_id=None) -> AsyncIterator[
        ModelResponse]:
        """流式响应的包装器，用于记录完整的响应日志并处理重试"""
        total_content = ""
        final_usage = None
        error_occurred = None
        chunk_count = 0

        # 使用重试逻辑获取流生成器
        stream_generator = self._retry_request_stream(self._stream, request, metadata, invoke_timeout, request_id=request_id or get_request_id(), origin_request_id=origin_request_id)

        try:
            async for response in stream_generator:
                chunk_count += 1
                if response.content:
                    total_content += response.content
                if response.usage:
                    final_usage = response.usage
                if response.error:
                    error_occurred = response.error
                yield response

            # 流式响应完成，记录日志
            duration = time.time() - start_time
            if error_occurred:
                # 流式响应中包含错误
                logger.warning(
                    f"⚠️ Stream completed with errors | chunks: {chunk_count}",
                    extra={
                        "log_type": "response",
                        "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                        "duration": duration,
                        "data": ResponseHandler.build_log_data(
                            model_request,
                            stream_stats={
                                "chunks_count": chunk_count,
                                "total_length": len(total_content),
                                "usage": final_usage,
                                "error": error_occurred
                            }
                        )
                    }
                )
            else:
                # 流式响应成功完成
                logger.info(
                    f"✅ Stream completed successfully | chunks: {chunk_count}",
                    extra={
                        "log_type": "response",
                        "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                        "duration": duration,
                        "data": ResponseHandler.build_log_data(
                            model_request,
                            stream_stats={
                                "chunks_count": chunk_count,
                                "total_length": len(total_content),
                                "usage": final_usage
                            }
                        )
                    }
                )
        except Exception as e:
            # 流式响应出错，记录错误日志
            duration = time.time() - start_time
            logger.error(
                f"❌ Stream failed after {chunk_count} chunks: {str(e)}",
                exc_info=True,
                extra={
                    "log_type": "response",
                    "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                    "duration": duration,
                    "data": ResponseHandler.build_log_data(
                        model_request,
                        error=e,
                        stream_stats={
                            "chunks_count": chunk_count,
                            "partial_content_length": len(total_content)
                        }
                    )
                }
            )
            raise

    async def _invoke_request(self, request, metadata, invoke_timeout, request_id=None, origin_request_id=None):
        """执行单个非流式请求

        Args:
            request: gRPC请求对象
            metadata: 请求元数据（为了兼容性保留，但会被忽略）
            invoke_timeout: 请求超时时间
            request_id: 请求ID
            origin_request_id: 原始请求ID
        """
        # 获取 stub（连接池或单连接）
        if self._pool_enabled:
            stub = await self.channel_pool.get_stub()
        else:
            stub = self.stub

        # 每次调用时重新生成metadata，确保JWT token是最新的
        fresh_metadata = self._build_auth_metadata(
            request_id or get_request_id(),
            origin_request_id
        )
        async for response in stub.Invoke(request, metadata=fresh_metadata, timeout=invoke_timeout):
            return ResponseHandler.build_model_response(response)

    async def _invoke_batch_request(self, batch_request, metadata, invoke_timeout, request_id=None):
        """执行批量请求

        Args:
            batch_request: gRPC批量请求对象
            metadata: 请求元数据
            invoke_timeout: 请求超时时间
            request_id: 请求ID
        """
        # 获取 stub（连接池或单连接）
        if self._pool_enabled:
            stub = await self.channel_pool.get_stub()
        else:
            stub = self.stub

        return await stub.BatchInvoke(batch_request, metadata=metadata, timeout=invoke_timeout)

    async def invoke(self, model_request: ModelRequest, timeout: Optional[float] = None,
                     request_id: Optional[str] = None) -> Union[
        ModelResponse, AsyncIterator[ModelResponse]]:
        """
       通用调用模型方法。

        Args:
            model_request: ModelRequest 对象，包含请求参数。
            timeout: Optional[float]
            request_id: Optional[str]
        Yields:
            ModelResponse: 支持流式或非流式的模型响应

        Raises:
            ValidationError: 输入验证失败。
            ConnectionError: 连接服务端失败。
        """
        # 如果启用了熔断且熔断器打开，直接走 HTTP
        if self.resilient_enabled and self.circuit_breaker and self.circuit_breaker.is_open:
            if self.http_fallback_url:
                logger.warning("🔻 Circuit breaker is OPEN, using HTTP fallback")
                # 在这里还没有计算origin_request_id，所以先计算
                temp_origin_request_id = None
                temp_request_id = request_id
                if request_id:
                    temp_request_id, temp_origin_request_id = self._request_id_manager.get_composite_id(request_id)
                return await self._invoke_http_fallback(model_request, timeout, temp_request_id, temp_origin_request_id)
                
        await self._ensure_initialized()

        if not self.default_payload:
            self.default_payload = {
                "org_id": model_request.user_context.org_id or "",
                "user_id": model_request.user_context.user_id or ""
            }

        # 处理 request_id
        origin_request_id = None
        if request_id:
            # 用户提供了 request_id，生成组合 ID
            request_id, origin_request_id = self._request_id_manager.get_composite_id(request_id)
        else:
            # 没有提供，生成新的
            request_id = generate_request_id()
            
        set_request_id(request_id)
        if origin_request_id:
            set_origin_request_id(origin_request_id)
        metadata = self._build_auth_metadata(request_id, origin_request_id)

        # 构建日志数据
        log_data = ResponseHandler.build_log_data(model_request)
        if origin_request_id:
            log_data['origin_request_id'] = origin_request_id

        # 记录开始日志
        start_time = time.time()
        logger.info(
            f"🔵 Request Start | request_id: {request_id} | provider: {model_request.provider} | invoke_type: {model_request.invoke_type}",
            extra={
                "log_type": "request",
                "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                "data": log_data
            })

        try:
            # 构建 gRPC 请求
            request = RequestBuilder.build_single_request(model_request)
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ Request build failed: {str(e)}",
                exc_info=True,
                extra={
                    "log_type": "response",
                    "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                    "duration": duration,
                    "data": {
                        "provider": model_request.provider.value,
                        "invoke_type": model_request.invoke_type.value,
                        "model": getattr(model_request, 'model', None),
                        "error_type": "build_error",
                        "error_message": str(e)
                    }
                }
            )
            raise ValueError(f"构建请求失败: {str(e)}") from e

        try:
            invoke_timeout = timeout or self.default_invoke_timeout
            if model_request.stream:
                # 对于流式响应，直接返回带日志记录的包装器
                return self._stream_with_logging(request, metadata, invoke_timeout, start_time, model_request, request_id, origin_request_id)
            else:
                # 存储model_request和origin_request_id供重试方法使用
                self._current_model_request = model_request
                self._current_origin_request_id = origin_request_id
                try:
                    result = await self._retry_request(self._invoke_request, request, metadata, invoke_timeout, request_id=request_id, origin_request_id=origin_request_id)
                finally:
                    # 清理临时存储
                    if hasattr(self, '_current_model_request'):
                        delattr(self, '_current_model_request')
                    if hasattr(self, '_current_origin_request_id'):
                        delattr(self, '_current_origin_request_id')

                # 记录非流式响应的成功日志
                duration = time.time() - start_time
                content_length = len(result.content) if result.content else 0
                
                # 构建响应日志数据
                response_log_data = ResponseHandler.build_log_data(model_request, result)
                if origin_request_id:
                    response_log_data['origin_request_id'] = origin_request_id
                    
                logger.info(
                    f"✅ Request completed | content_length: {content_length}",
                    extra={
                        "log_type": "response",
                        "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                        "duration": duration,
                        "data": response_log_data
                    }
                )
                
                # 记录成功（如果启用了熔断）
                if self.resilient_enabled and self.circuit_breaker:
                    self.circuit_breaker.record_success()
                    
                return result
                
        except (ConnectionError, grpc.RpcError) as e:
            duration = time.time() - start_time
            error_message = f"❌ Invoke gRPC failed: {str(e)}"
            
            # 构建错误日志数据
            error_log_data = ResponseHandler.build_log_data(model_request, error=e)
            if origin_request_id:
                error_log_data['origin_request_id'] = origin_request_id
                
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                             "duration": duration,
                             "data": error_log_data
                         })
            
            # 记录 channel 错误
            if isinstance(e, grpc.RpcError):
                self._record_channel_error(e)
            
            # 记录失败（如果启用了熔断）
            if self.resilient_enabled and self.circuit_breaker:
                # 将错误码传递给熔断器，用于智能失败统计
                error_code = e.code() if hasattr(e, 'code') else None
                self.circuit_breaker.record_failure(error_code)
            
            raise e
        except Exception as e:
            duration = time.time() - start_time
            error_message = f"❌ Invoke other error: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": f"/invoke/{model_request.provider.value}/{model_request.invoke_type.value}",
                             "duration": duration,
                             "data": ResponseHandler.build_log_data(
                                 model_request,
                                 error=e
                             )
                         })
            raise e

    async def invoke_batch(self, batch_request_model: BatchModelRequest, timeout: Optional[float] = None,
                           request_id: Optional[str] = None) -> BatchModelResponse:
        """
        批量模型调用接口

        Args:
            batch_request_model: 多条 BatchModelRequest 输入
            timeout: 调用超时，单位秒
            request_id: 请求id
        Returns:
            BatchModelResponse: 批量请求的结果
        """
        # 如果启用了熔断且熔断器打开，直接走 HTTP
        if self.resilient_enabled and self.circuit_breaker and self.circuit_breaker.is_open:
            if self.http_fallback_url:
                logger.warning("🔻 Circuit breaker is OPEN, using HTTP fallback for batch request")
                # 在这里还没有计算origin_request_id，所以先计算
                temp_origin_request_id = None
                temp_request_id = request_id
                if request_id:
                    temp_request_id, temp_origin_request_id = self._request_id_manager.get_composite_id(request_id)
                return await self._invoke_batch_http_fallback(batch_request_model, timeout, temp_request_id, temp_origin_request_id)
                
        await self._ensure_initialized()

        if not self.default_payload:
            self.default_payload = {
                "org_id": batch_request_model.user_context.org_id or "",
                "user_id": batch_request_model.user_context.user_id or ""
            }

        # 处理 request_id
        origin_request_id = None
        if request_id:
            # 用户提供了 request_id，生成组合 ID
            request_id, origin_request_id = self._request_id_manager.get_composite_id(request_id)
        else:
            # 没有提供，生成新的
            request_id = generate_request_id()
            
        set_request_id(request_id)
        if origin_request_id:
            set_origin_request_id(origin_request_id)
        metadata = self._build_auth_metadata(request_id, origin_request_id)

        # 构建日志数据
        batch_log_data = {
            "batch_size": len(batch_request_model.items),
            "org_id": batch_request_model.user_context.org_id,
            "user_id": batch_request_model.user_context.user_id,
            "client_type": batch_request_model.user_context.client_type
        }
        if origin_request_id:
            batch_log_data['origin_request_id'] = origin_request_id

        # 记录开始日志
        start_time = time.time()
        logger.info(
            f"🔵 Batch Request Start | request_id: {request_id} | batch_size: {len(batch_request_model.items)}",
            extra={
                "log_type": "request",
                "uri": "/batch_invoke",
                "data": batch_log_data
            })

        try:
            # 构建批量请求
            batch_request = RequestBuilder.build_batch_request(batch_request_model)
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ Batch request build failed: {str(e)}",
                exc_info=True,
                extra={
                    "log_type": "response",
                    "uri": "/batch_invoke",
                    "duration": duration,
                    "data": {
                        "batch_size": len(batch_request_model.items),
                        "error_type": "build_error",
                        "error_message": str(e)
                    }
                }
            )
            raise ValueError(f"构建批量请求失败: {str(e)}") from e

        try:
            invoke_timeout = timeout or self.default_invoke_timeout

            # 保存批量请求信息用于降级
            self._current_batch_request = batch_request_model
            self._current_origin_request_id = origin_request_id

            batch_response = await self._retry_request(
                self._invoke_batch_request,
                batch_request,
                metadata,
                invoke_timeout,
                request_id=request_id
            )

            # 构建响应对象
            result = ResponseHandler.build_batch_response(batch_response)

            # 记录成功日志
            duration = time.time() - start_time
            logger.info(
                f"✅ Batch Request completed | batch_size: {len(result.responses)}",
                extra={
                    "log_type": "response",
                    "uri": "/batch_invoke",
                    "duration": duration,
                    "data": {
                        "batch_size": len(result.responses),
                        "success_count": sum(1 for item in result.responses if not item.error),
                        "error_count": sum(1 for item in result.responses if item.error)
                    }
                })

            return result

        except grpc.RpcError as e:
            duration = time.time() - start_time
            error_message = f"❌ Batch invoke gRPC failed: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/batch_invoke",
                             "duration": duration,
                             "data": {
                                 "error_type": "grpc_error",
                                 "error_code": str(e.code()) if hasattr(e, 'code') else None,
                                 "batch_size": len(batch_request_model.items)
                             }
                         })
            
            # 记录失败（如果启用了熔断）
            if self.resilient_enabled and self.circuit_breaker:
                # 将错误码传递给熔断器，用于智能失败统计
                error_code = e.code() if hasattr(e, 'code') else None
                self.circuit_breaker.record_failure(error_code)
            
            raise e
        except Exception as e:
            duration = time.time() - start_time
            error_message = f"❌ Batch invoke other error: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/batch_invoke",
                             "duration": duration,
                             "data": {
                                 "error_type": "other_error",
                                 "batch_size": len(batch_request_model.items)
                             }
                         })
            raise e

    async def get_task_status(self, task_id: str, timeout: Optional[float] = None) -> TaskStatusResponse:
        """
        查询异步任务状态

        Args:
            task_id: 任务ID
            timeout: 调用超时，单位秒

        Returns:
            TaskStatusResponse: 任务状态响应
        """
        await self._ensure_initialized()

        # 生成 request_id
        request_id = generate_request_id()
        set_request_id(request_id)
        metadata = self._build_auth_metadata(request_id, None)

        # 记录开始日志
        start_time = time.time()
        logger.info(
            f"🔵 GetTaskStatus Start | request_id: {request_id} | task_id: {task_id}",
            extra={
                "log_type": "request",
                "uri": "/get_task_status",
                "data": {"task_id": task_id}
            })

        try:
            # 构建请求
            request = model_service_pb2.GetTaskStatusRequest(task_id=task_id)
            invoke_timeout = timeout or self.default_invoke_timeout

            # 执行请求（带重试）
            async def get_task_status_request():
                if self._pool_enabled:
                    stub = await self.channel_pool.get_stub()
                else:
                    stub = self.stub
                return await stub.GetTaskStatus(request, metadata=metadata, timeout=invoke_timeout)

            response = await self._retry_request(
                get_task_status_request,
                request_id=request_id
            )

            # 构建响应对象
            result = ResponseHandler.build_task_status_response(response)

            # 记录成功日志
            duration = time.time() - start_time
            logger.info(
                f"✅ GetTaskStatus completed | status: {result.status}",
                extra={
                    "log_type": "response",
                    "uri": "/get_task_status",
                    "duration": duration,
                    "data": {
                        "task_id": task_id,
                        "status": result.status,
                        "provider": result.provider,
                        "model": result.model
                    }
                })

            return result

        except grpc.RpcError as e:
            duration = time.time() - start_time
            error_message = f"❌ GetTaskStatus gRPC failed: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/get_task_status",
                             "duration": duration,
                             "data": {
                                 "error_type": "grpc_error",
                                 "error_code": str(e.code()) if hasattr(e, 'code') else None,
                                 "task_id": task_id
                             }
                         })
            raise e
        except Exception as e:
            duration = time.time() - start_time
            error_message = f"❌ GetTaskStatus other error: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/get_task_status",
                             "duration": duration,
                             "data": {
                                 "error_type": "other_error",
                                 "task_id": task_id
                             }
                         })
            raise e

    async def batch_get_task_status(self, task_ids: list[str], timeout: Optional[float] = None) -> BatchTaskStatusResponse:
        """
        批量查询异步任务状态

        Args:
            task_ids: 任务ID列表
            timeout: 调用超时，单位秒

        Returns:
            BatchTaskStatusResponse: 批量任务状态响应
        """
        await self._ensure_initialized()

        # 生成 request_id
        request_id = generate_request_id()
        set_request_id(request_id)
        metadata = self._build_auth_metadata(request_id, None)

        # 记录开始日志
        start_time = time.time()
        logger.info(
            f"🔵 BatchGetTaskStatus Start | request_id: {request_id} | task_count: {len(task_ids)}",
            extra={
                "log_type": "request",
                "uri": "/batch_get_task_status",
                "data": {"task_count": len(task_ids), "task_ids": task_ids}
            })

        try:
            # 构建请求
            request = model_service_pb2.BatchGetTaskStatusRequest(task_ids=task_ids)
            invoke_timeout = timeout or self.default_invoke_timeout

            # 执行请求（带重试）
            async def batch_get_task_status_request():
                if self._pool_enabled:
                    stub = await self.channel_pool.get_stub()
                else:
                    stub = self.stub
                return await stub.BatchGetTaskStatus(request, metadata=metadata, timeout=invoke_timeout)

            response = await self._retry_request(
                batch_get_task_status_request,
                request_id=request_id
            )

            # 构建响应对象
            result = ResponseHandler.build_batch_task_status_response(response)

            # 记录成功日志
            duration = time.time() - start_time
            logger.info(
                f"✅ BatchGetTaskStatus completed | task_count: {len(result.tasks)}",
                extra={
                    "log_type": "response",
                    "uri": "/batch_get_task_status",
                    "duration": duration,
                    "data": {
                        "task_count": len(result.tasks),
                        "status_summary": {
                            "processing": sum(1 for t in result.tasks if t.status == "processing"),
                            "completed": sum(1 for t in result.tasks if t.status == "completed"),
                            "failed": sum(1 for t in result.tasks if t.status == "failed")
                        }
                    }
                })

            return result

        except grpc.RpcError as e:
            duration = time.time() - start_time
            error_message = f"❌ BatchGetTaskStatus gRPC failed: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/batch_get_task_status",
                             "duration": duration,
                             "data": {
                                 "error_type": "grpc_error",
                                 "error_code": str(e.code()) if hasattr(e, 'code') else None,
                                 "task_count": len(task_ids)
                             }
                         })
            raise e
        except Exception as e:
            duration = time.time() - start_time
            error_message = f"❌ BatchGetTaskStatus other error: {str(e)}"
            logger.error(error_message, exc_info=True,
                         extra={
                             "log_type": "response",
                             "uri": "/batch_get_task_status",
                             "duration": duration,
                             "data": {
                                 "error_type": "other_error",
                                 "task_count": len(task_ids)
                             }
                         })
            raise e