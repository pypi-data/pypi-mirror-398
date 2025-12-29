"""
Base client class for Tamar Model Client

This module provides the base client class with shared initialization logic
and configuration management for both sync and async clients.
"""

import os
from typing import Optional
from abc import ABC, abstractmethod

from ..auth import JWTAuthHandler
from ..error_handler import GrpcErrorHandler, ErrorRecoveryStrategy
from .logging_setup import MAX_MESSAGE_LENGTH, get_protected_logger


class BaseClient(ABC):
    """
    基础客户端抽象类
    
    提供同步和异步客户端的共享功能：
    - 配置管理
    - 认证设置
    - 连接选项构建
    - 错误处理器初始化
    """

    def __init__(
            self,
            server_address: Optional[str] = None,
            jwt_secret_key: Optional[str] = None,
            jwt_token: Optional[str] = None,
            default_payload: Optional[dict] = None,
            token_expires_in: int = 3600,
            max_retries: Optional[int] = None,
            retry_delay: Optional[float] = None,
            logger_name: str = None,
    ):
        """
        初始化基础客户端
        
        Args:
            server_address: gRPC 服务器地址，格式为 "host:port"
            jwt_secret_key: JWT 签名密钥，用于生成认证令牌
            jwt_token: 预生成的 JWT 令牌（可选）
            default_payload: JWT 令牌的默认载荷
            token_expires_in: JWT 令牌过期时间（秒）
            max_retries: 最大重试次数（默认从环境变量读取）
            retry_delay: 初始重试延迟（秒，默认从环境变量读取）
            logger_name: 日志记录器名称
            
        Raises:
            ValueError: 当服务器地址未提供时
        """
        # === 服务端地址配置 ===
        self.server_address = server_address or os.getenv("MODEL_MANAGER_SERVER_ADDRESS")
        if not self.server_address:
            raise ValueError("Server address must be provided via argument or environment variable.")

        # 默认调用超时时间
        self.default_invoke_timeout = float(os.getenv("MODEL_MANAGER_SERVER_INVOKE_TIMEOUT", 30.0))

        # === JWT 认证配置 ===
        self.jwt_secret_key = jwt_secret_key or os.getenv("MODEL_MANAGER_SERVER_JWT_SECRET_KEY")
        self.jwt_handler = JWTAuthHandler(self.jwt_secret_key) if self.jwt_secret_key else None
        self.jwt_token = jwt_token  # 用户传入的预生成 Token（可选）
        self.default_payload = default_payload
        self.token_expires_in = token_expires_in

        # === TLS/Authority 配置 ===
        self.use_tls = os.getenv("MODEL_MANAGER_SERVER_GRPC_USE_TLS", "true").lower() == "true"
        self.default_authority = os.getenv("MODEL_MANAGER_SERVER_GRPC_DEFAULT_AUTHORITY")

        # === 重试配置 ===
        self.max_retries = max_retries if max_retries is not None else int(
            os.getenv("MODEL_MANAGER_SERVER_GRPC_MAX_RETRIES", 6))
        self.retry_delay = retry_delay if retry_delay is not None else float(
            os.getenv("MODEL_MANAGER_SERVER_GRPC_RETRY_DELAY", 1.0))

        # === 日志配置 ===
        self.logger = get_protected_logger(logger_name or __name__)

        # === 错误处理器 ===
        self.error_handler = GrpcErrorHandler(self.logger)
        self.recovery_strategy = ErrorRecoveryStrategy(self)

        # === 连接状态 ===
        self._closed = False

        # === 连接池配置 ===
        self._init_pool_config()

        # === 熔断降级配置 ===
        self._init_resilient_features()

        # === 快速降级配置 ===
        self._init_fast_fallback_config()

    def build_channel_options(self) -> list:
        """
        构建 gRPC 通道选项

        配置策略：与服务器端保持一致，避免窗口阻塞和超时问题

        Returns:
            list: gRPC 通道配置选项列表
        """
        options = [
            # === 消息大小限制 ===
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),

            # === HTTP/2 窗口配置（关键！解决窗口阻塞问题）===
            # 参考服务器配置：server.py:431-433
            ('grpc.http2.max_frame_size', 4194304),  # 4MB - 单个帧最大大小
            ('grpc.http2.initial_stream_window_size', 1 << 20),  # 1MB - 流级窗口
            ('grpc.http2.initial_connection_window_size', 16 << 20),  # 16MB - 连接级窗口

            # === HTTP/2 Ping 配置（与服务器一致）===
            # 参考服务器配置：server.py:434-435
            ('grpc.http2.max_pings_without_data', 0),  # 0=无限制（与服务器一致）
            ('grpc.http2.min_time_between_pings_ms', 15000),  # 15秒（与服务器一致）

            # === Keepalive 配置（与服务器一致）===
            # 参考服务器配置：server.py:438-439
            ('grpc.keepalive_time_ms', 60000),  # 60秒发送一次 keepalive ping
            ('grpc.keepalive_timeout_ms', 10000),  # ping 响应超时时间 10秒
            ('grpc.keepalive_permit_without_calls', 1),  # 空闲时也发送 keepalive

            # === 并发流控制 ===
            # 匹配服务器的 max_concurrent_streams: 5000
            ('grpc.http2.max_concurrent_streams', 5000),

            # === 连接生命周期管理 ===
            ('grpc.http2.max_connection_idle_ms', 300000),  # 最大空闲时间 5分钟
            ('grpc.http2.max_connection_age_ms', 3600000),  # 连接最大生存时间 1小时
            ('grpc.http2.max_connection_age_grace_ms', 5000),  # 优雅关闭时间 5秒

            # === 其他性能配置 ===
            ('grpc.http2.bdp_probe', 0),  # 关闭 BDP 探测（与服务器一致）
            ('grpc.enable_retries', 1),  # 启用内置重试

            # === 资源配额 ===
            ('grpc.resource_quota_size', 1048576000),  # 1GB

            # === 负载均衡（用于连接池的 DNS 解析）===
            ('grpc.lb_policy_name', 'round_robin'),
        ]

        if self.default_authority:
            options.append(("grpc.default_authority", self.default_authority))

        return options

    def force_refresh_token(self) -> bool:
        """
        强制刷新 JWT token

        当检测到 UNAUTHENTICATED 错误时调用，强制生成新的 token。
        只有在提供了 jwt_secret_key 时才能刷新，否则返回 False。

        Returns:
            bool: True 表示成功刷新，False 表示无法刷新（使用预生成 token）
        """
        if self.jwt_handler and self.default_payload:
            # 强制生成新 token（忽略缓存）
            self.jwt_token = self.jwt_handler.encode_token(
                self.default_payload,
                expires_in=self.token_expires_in
            )
            self.logger.info(
                "🔄 JWT token refreshed due to authentication error",
                extra={
                    "log_type": "token_refresh",
                    "data": {"reason": "UNAUTHENTICATED_error"}
                }
            )
            return True
        else:
            # 没有 jwt_handler 或 default_payload，无法自动刷新
            self.logger.warning(
                "⚠️ Cannot refresh token: using pre-generated token or missing jwt_secret_key",
                extra={
                    "log_type": "token_refresh_failed",
                    "data": {
                        "has_jwt_handler": bool(self.jwt_handler),
                        "has_default_payload": bool(self.default_payload)
                    }
                }
            )
            return False

    def _build_auth_metadata(self, request_id: str, origin_request_id: Optional[str] = None) -> list:
        """
        构建认证元数据

        为每个请求构建包含认证信息和请求ID的gRPC元数据。
        JWT令牌会在每次请求时重新生成以确保有效性。

        Args:
            request_id: 当前请求的唯一标识符
            origin_request_id: 原始请求ID（可选）

        Returns:
            list: gRPC元数据列表，包含请求ID和认证令牌
        """
        metadata = [("x-request-id", request_id)]  # 将 request_id 添加到 headers

        # 如果有原始请求ID，也添加到 headers
        if origin_request_id:
            metadata.append(("x-origin-request-id", origin_request_id))

        if self.jwt_handler:
            # 如果没有 default_payload，使用空字典
            payload = self.default_payload if self.default_payload is not None else {}

            # 检查token是否即将过期，如果是则刷新
            if self.jwt_handler.is_token_expiring_soon():
                self.jwt_token = self.jwt_handler.encode_token(
                    payload,
                    expires_in=self.token_expires_in
                )
            else:
                # 使用缓存的token
                cached_token = self.jwt_handler.get_cached_token()
                if cached_token:
                    self.jwt_token = cached_token
                else:
                    # 如果没有缓存，生成新token
                    self.jwt_token = self.jwt_handler.encode_token(
                        payload,
                        expires_in=self.token_expires_in
                    )

            metadata.append(("authorization", f"Bearer {self.jwt_token}"))
        elif self.jwt_token:
            # 使用用户提供的预生成token
            metadata.append(("authorization", f"Bearer {self.jwt_token}"))

        return metadata

    @abstractmethod
    def close(self):
        """关闭客户端连接（由子类实现）"""
        pass

    @abstractmethod
    def __enter__(self):
        """进入上下文管理器（由子类实现）"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器（由子类实现）"""
        pass

    def _init_pool_config(self):
        """
        初始化连接池配置

        智能计算默认连接池大小：
        - 基于CPU核心数动态计算
        - 最小3个，最大10个
        - 可通过环境变量覆盖
        """
        # 动态计算默认连接池大小
        default_pool_size = self._calculate_default_pool_size()

        # 从环境变量读取（可覆盖动态计算值）
        pool_size_env = os.getenv("MODEL_MANAGER_SERVER_GRPC_POOL_SIZE")

        if pool_size_env:
            self.pool_size = int(pool_size_env)
        else:
            self.pool_size = default_pool_size

        # 确保至少有1个连接
        if self.pool_size < 1:
            self.pool_size = 1

        self.logger.debug(
            f"Connection pool size: {self.pool_size}",
            extra={
                "log_type": "pool_config",
                "data": {
                    "pool_size": self.pool_size,
                    "calculated_default": default_pool_size,
                    "from_env": pool_size_env is not None
                }
            }
        )

    def _calculate_default_pool_size(self) -> int:
        """
        动态计算默认连接池大小

        策略：
        - CPU核心数 <= 2: 使用3个连接
        - CPU核心数 3-8: 使用CPU核心数
        - CPU核心数 > 8: 使用8个连接（避免过多连接）

        Returns:
            int: 推荐的连接池大小
        """
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()

            # 根据CPU核心数计算
            if cpu_count <= 2:
                return 3  # 最小3个连接
            elif cpu_count <= 8:
                return cpu_count  # 中等配置，使用CPU核心数
            else:
                return 8  # 高配置，限制为8个避免过多连接

        except Exception:
            # 无法获取CPU信息，使用保守值
            return 3

    def _should_use_pool(self) -> bool:
        """判断是否应该使用连接池"""
        return self.pool_size > 1

    def _init_resilient_features(self):
        """初始化熔断降级特性"""
        # 是否启用熔断降级
        self.resilient_enabled = os.getenv('MODEL_CLIENT_RESILIENT_ENABLED', 'false').lower() == 'true'

        if self.resilient_enabled:
            # HTTP 降级地址
            self.http_fallback_url = os.getenv('MODEL_CLIENT_HTTP_FALLBACK_URL')

            if not self.http_fallback_url:
                self.logger.warning("🔶 Resilient mode enabled but MODEL_CLIENT_HTTP_FALLBACK_URL not set")
                self.resilient_enabled = False
                return

            # 初始化熔断器
            from ..circuit_breaker import CircuitBreaker
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=int(os.getenv('MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', '5')),
                recovery_timeout=int(os.getenv('MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT', '60'))
            )

            # HTTP 客户端（延迟初始化）
            self._http_client = None
            self._http_session = None  # 异步客户端使用

            self.logger.info(
                "🛡️ Resilient mode enabled",
                extra={
                    "log_type": "info",
                    "data": {
                        "http_fallback_url": self.http_fallback_url,
                        "circuit_breaker_threshold": self.circuit_breaker.failure_threshold,
                        "circuit_breaker_timeout": self.circuit_breaker.recovery_timeout
                    }
                }
            )
        else:
            self.circuit_breaker = None
            self.http_fallback_url = None
            self._http_client = None
            self._http_session = None

    def get_resilient_metrics(self):
        """获取熔断降级指标"""
        if not self.resilient_enabled or not self.circuit_breaker:
            return None

        return {
            "enabled": self.resilient_enabled,
            "circuit_breaker": {
                "state": self.circuit_breaker.get_state(),
                "failure_count": self.circuit_breaker.failure_count,
                "last_failure_time": self.circuit_breaker.last_failure_time,
                "failure_threshold": self.circuit_breaker.failure_threshold,
                "recovery_timeout": self.circuit_breaker.recovery_timeout
            },
            "http_fallback_url": self.http_fallback_url
        }

    def _init_fast_fallback_config(self):
        """
        初始化快速降级配置

        注意：默认关闭降级功能，需要显式启用
        """
        import grpc

        # 是否启用快速降级（默认关闭）
        self.fast_fallback_enabled = os.getenv('MODEL_CLIENT_FAST_FALLBACK_ENABLED', 'false').lower() == 'true'

        # 降级前的最大gRPC重试次数
        self.fallback_after_retries = int(os.getenv('MODEL_CLIENT_FALLBACK_AFTER_RETRIES', '1'))

        # 立即降级的错误码配置
        immediate_fallback_errors = os.getenv('MODEL_CLIENT_IMMEDIATE_FALLBACK_ERRORS',
                                              'UNAVAILABLE,DEADLINE_EXCEEDED,CANCELLED')
        self.immediate_fallback_errors = set()

        if immediate_fallback_errors:
            for error_name in immediate_fallback_errors.split(','):
                error_name = error_name.strip()
                if hasattr(grpc.StatusCode, error_name):
                    self.immediate_fallback_errors.add(getattr(grpc.StatusCode, error_name))

        # 永不降级的错误码
        never_fallback_errors = os.getenv('MODEL_CLIENT_NEVER_FALLBACK_ERRORS',
                                          'UNAUTHENTICATED,PERMISSION_DENIED,INVALID_ARGUMENT')
        self.never_fallback_errors = set()

        if never_fallback_errors:
            for error_name in never_fallback_errors.split(','):
                error_name = error_name.strip()
                if hasattr(grpc.StatusCode, error_name):
                    self.never_fallback_errors.add(getattr(grpc.StatusCode, error_name))

        # 流式响应单个数据块的超时时间（秒）
        # AI模型生成可能需要更长时间，默认设置为120秒
        self.stream_chunk_timeout = float(os.getenv('MODEL_CLIENT_STREAM_CHUNK_TIMEOUT', '120.0'))

        if self.fast_fallback_enabled:
            self.logger.info(
                "🚀 Fast fallback enabled",
                extra={
                    "data": {
                        "fallback_after_retries": self.fallback_after_retries,
                        "immediate_fallback_errors": [e.name for e in self.immediate_fallback_errors],
                        "never_fallback_errors": [e.name for e in self.never_fallback_errors]
                    }
                }
            )

    def _should_try_fallback(self, error_code, attempt: int) -> bool:
        """
        判断是否应该尝试降级
        
        Args:
            error_code: gRPC错误码
            attempt: 当前重试次数
            
        Returns:
            bool: 是否应该尝试降级
        """
        # 未启用快速降级
        if not self.fast_fallback_enabled:
            return False

        # 未启用熔断降级功能
        if not self.resilient_enabled or not self.http_fallback_url:
            return False

        # 永不降级的错误类型
        if error_code in self.never_fallback_errors:
            return False

        # 立即降级的错误类型
        if error_code in self.immediate_fallback_errors:
            return True

        # 其他错误在达到重试次数后降级
        return attempt >= self.fallback_after_retries
