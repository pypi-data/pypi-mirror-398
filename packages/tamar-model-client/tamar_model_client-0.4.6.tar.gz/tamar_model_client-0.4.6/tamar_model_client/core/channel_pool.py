"""
gRPC Channel 连接池

提供连接池管理，避免单连接复用导致的问题：
- Connection reset
- Upstream request timeout
- HTTP/2 窗口阻塞

设计原则：
- 简洁清晰，避免过度复杂
- 轮询策略，公平分配请求
- 被动健康检查，记录错误但不主动探测
"""

import time
import threading
from typing import List
import grpc


class ChannelWrapper:
    """
    单个 Channel 包装器

    跟踪单个连接的状态和统计信息
    """

    def __init__(self, index: int, channel: grpc.Channel, stub):
        self.index = index
        self.channel = channel
        self.stub = stub

        # 统计信息
        self.request_count = 0
        self.error_count = 0
        self.last_used_time = time.time()
        self.created_time = time.time()

        # 健康状态
        self.is_healthy = True
        self.last_error_time = None

        # 线程锁
        self._lock = threading.Lock()

    def mark_used(self):
        """标记已使用"""
        with self._lock:
            self.request_count += 1
            self.last_used_time = time.time()

    def mark_error(self, error: grpc.RpcError):
        """
        标记错误

        对于严重错误（UNAVAILABLE, CANCELLED等），标记为不健康
        """
        with self._lock:
            self.error_count += 1
            self.last_error_time = time.time()

            # 严重错误标记为不健康
            if error.code() in [
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.CANCELLED,
                grpc.StatusCode.DEADLINE_EXCEEDED,
                grpc.StatusCode.INTERNAL
            ]:
                self.is_healthy = False

    def try_recover(self):
        """
        尝试恢复健康状态

        如果距离上次错误已经超过一定时间，尝试恢复
        """
        if not self.is_healthy and self.last_error_time:
            # 30秒后尝试恢复
            if time.time() - self.last_error_time > 30:
                self.is_healthy = True
                return True
        return False

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'index': self.index,
                'healthy': self.is_healthy,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'error_rate': self.error_count / max(self.request_count, 1),
                'idle_time': time.time() - self.last_used_time,
                'uptime': time.time() - self.created_time
            }


class ChannelPool:
    """
    gRPC Channel 连接池

    管理多个 gRPC Channel，使用轮询策略分配请求
    """

    def __init__(
        self,
        pool_size: int,
        server_address: str,
        channel_options: list,
        use_tls: bool,
        stub_class,
        logger
    ):
        """
        初始化连接池

        Args:
            pool_size: 连接池大小
            server_address: 服务器地址
            channel_options: gRPC channel 选项
            use_tls: 是否使用 TLS
            stub_class: gRPC Stub 类
            logger: 日志记录器
        """
        self.pool_size = pool_size
        self.server_address = server_address
        self.channel_options = channel_options
        self.use_tls = use_tls
        self.stub_class = stub_class
        self.logger = logger

        # 连接池
        self.channels: List[ChannelWrapper] = []
        self._current_index = 0
        self._lock = threading.Lock()

        # 初始化所有连接
        self._init_channels()

    def _init_channels(self):
        """初始化所有 Channel"""
        self.logger.info(
            f"🏊 Initializing connection pool with {self.pool_size} channels",
            extra={"log_type": "pool_init", "data": {"pool_size": self.pool_size}}
        )

        for i in range(self.pool_size):
            try:
                wrapper = self._create_channel(i)
                self.channels.append(wrapper)

                self.logger.debug(
                    f"✅ Channel #{i} created",
                    extra={"log_type": "pool_channel_created", "data": {"index": i}}
                )
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to create channel #{i}: {e}",
                    extra={"log_type": "pool_channel_failed", "data": {"index": i, "error": str(e)}}
                )
                # 创建失败不应阻止其他连接的创建
                continue

        if len(self.channels) == 0:
            raise Exception(f"Failed to create any channels in pool")

        self.logger.info(
            f"✅ Connection pool initialized: {len(self.channels)}/{self.pool_size} channels",
            extra={"log_type": "pool_ready", "data": {"active_channels": len(self.channels)}}
        )

    def _create_channel(self, index: int) -> ChannelWrapper:
        """
        创建单个 Channel

        Args:
            index: Channel 索引

        Returns:
            ChannelWrapper: Channel 包装器
        """
        if self.use_tls:
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(
                self.server_address,
                credentials,
                options=self.channel_options
            )
        else:
            channel = grpc.insecure_channel(
                f"dns:///{self.server_address}",
                options=self.channel_options
            )

        # 等待 channel 就绪（带超时）
        try:
            grpc.channel_ready_future(channel).result(timeout=10)
        except grpc.FutureTimeoutError:
            self.logger.warning(
                f"⚠️ Channel #{index} ready timeout, but will keep it",
                extra={"log_type": "pool_channel_timeout", "data": {"index": index}}
            )

        stub = self.stub_class(channel)
        return ChannelWrapper(index, channel, stub)

    def get_channel(self) -> grpc.Channel:
        """
        获取一个可用的 Channel

        使用轮询策略选择 Channel

        Returns:
            grpc.Channel: 可用的 Channel
        """
        wrapper = self._get_wrapper()
        wrapper.mark_used()
        return wrapper.channel

    def get_stub(self):
        """
        获取一个可用的 Stub

        Returns:
            Stub: gRPC Stub 实例
        """
        wrapper = self._get_wrapper()
        wrapper.mark_used()
        return wrapper.stub

    def _get_wrapper(self) -> ChannelWrapper:
        """
        使用轮询策略获取 ChannelWrapper

        优先选择健康的连接，如果都不健康则尝试恢复
        """
        with self._lock:
            # 尝试恢复不健康的连接
            for wrapper in self.channels:
                wrapper.try_recover()

            # 过滤健康的连接
            healthy_channels = [w for w in self.channels if w.is_healthy]

            if not healthy_channels:
                # 所有连接都不健康，记录警告并使用全部连接（让gRPC重试处理）
                self.logger.warning(
                    "⚠️ No healthy channels in pool, using all channels",
                    extra={"log_type": "pool_no_healthy", "data": {"total": len(self.channels)}}
                )
                healthy_channels = self.channels

            # 轮询选择
            wrapper = healthy_channels[self._current_index % len(healthy_channels)]
            self._current_index = (self._current_index + 1) % len(healthy_channels)

            return wrapper

    def record_error(self, error: grpc.RpcError):
        """
        记录错误到最近使用的 Channel

        注意：这是一个简化实现，记录到所有最近使用的 Channel
        实际应该记录到具体使用的那个 Channel，但那需要更复杂的追踪机制
        """
        # 简化实现：找到最近使用的 Channel
        with self._lock:
            if self.channels:
                # 找到最近使用的 channel（根据 last_used_time）
                recent_wrapper = max(self.channels, key=lambda w: w.last_used_time)
                recent_wrapper.mark_error(error)

    def close(self):
        """关闭所有 Channel"""
        self.logger.info(
            "🔒 Closing connection pool",
            extra={"log_type": "pool_close", "data": {"channels": len(self.channels)}}
        )

        for wrapper in self.channels:
            try:
                wrapper.channel.close()
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Error closing channel #{wrapper.index}: {e}",
                    extra={"log_type": "pool_close_error", "data": {"index": wrapper.index}}
                )

        self.channels.clear()

    def get_stats(self) -> dict:
        """获取连接池统计信息"""
        with self._lock:
            return {
                'pool_size': self.pool_size,
                'active_channels': len(self.channels),
                'healthy_count': sum(1 for w in self.channels if w.is_healthy),
                'channels': [w.get_stats() for w in self.channels]
            }
