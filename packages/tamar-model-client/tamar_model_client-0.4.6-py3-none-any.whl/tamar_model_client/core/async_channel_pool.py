"""
Async gRPC Channel Pool Implementation

异步版本的连接池实现，用于管理多个 gRPC channel 以提升并发性能和稳定性。

核心特性：
- 多连接并发：避免单连接阻塞和超时
- 被动健康检查：基于错误自动标记不健康连接
- Round-robin 负载均衡：均匀分配请求
- 自动恢复：不健康连接30秒后自动重试

设计原则：
- 使用 asyncio.Lock 替代 threading.Lock
- 支持 async context manager
- 与 sync channel_pool 保持 API 一致性
"""

import asyncio
import time
from typing import List, Optional
import grpc

from .logging_setup import get_protected_logger

logger = get_protected_logger(__name__)


class AsyncChannelWrapper:
    """
    异步 Channel 包装器

    管理单个 gRPC channel 的健康状态和使用统计

    Attributes:
        index: 连接在池中的索引
        channel: gRPC 异步 channel
        stub: gRPC 服务存根
        request_count: 总请求次数
        error_count: 错误次数
        is_healthy: 健康状态
        last_error_time: 最后错误时间
    """

    # 健康恢复时间（秒）- 标记为不健康后多久可以重试
    HEALTH_RECOVERY_TIMEOUT = 30

    def __init__(self, index: int, channel: grpc.aio.Channel, stub):
        """
        初始化 Channel 包装器

        Args:
            index: 连接索引
            channel: gRPC 异步 channel
            stub: gRPC 服务存根
        """
        self.index = index
        self.channel = channel
        self.stub = stub
        self.request_count = 0
        self.error_count = 0
        self.is_healthy = True
        self.last_error_time = None
        self._lock = asyncio.Lock()

        logger.debug(
            f"Async channel #{index} created",
            extra={
                "log_type": "channel_pool",
                "data": {"index": index, "type": "async"}
            }
        )

    async def mark_used(self):
        """标记连接被使用（线程安全）"""
        async with self._lock:
            self.request_count += 1

    async def mark_error(self, error: grpc.RpcError):
        """
        标记连接错误

        对于严重错误（UNAVAILABLE, CANCELLED, DEADLINE_EXCEEDED），
        将连接标记为不健康，暂时不再使用。

        Args:
            error: gRPC 错误对象
        """
        async with self._lock:
            self.error_count += 1
            self.last_error_time = time.time()

            # 严重错误导致连接不健康
            if error.code() in [
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.CANCELLED,
                grpc.StatusCode.DEADLINE_EXCEEDED
            ]:
                self.is_healthy = False
                logger.warning(
                    f"⚠️ Async channel #{self.index} marked as UNHEALTHY due to {error.code().name}",
                    extra={
                        "log_type": "channel_pool",
                        "data": {
                            "index": self.index,
                            "error_code": error.code().name,
                            "error_count": self.error_count,
                            "request_count": self.request_count,
                            "type": "async"
                        }
                    }
                )

    async def try_recover(self):
        """
        尝试恢复不健康的连接

        如果连接标记为不健康超过恢复超时时间，则重新标记为健康
        """
        async with self._lock:
            if not self.is_healthy and self.last_error_time:
                if time.time() - self.last_error_time > self.HEALTH_RECOVERY_TIMEOUT:
                    self.is_healthy = True
                    logger.info(
                        f"✅ Async channel #{self.index} recovered to HEALTHY",
                        extra={
                            "log_type": "channel_pool",
                            "data": {
                                "index": self.index,
                                "downtime": time.time() - self.last_error_time,
                                "type": "async"
                            }
                        }
                    )

    async def get_stats(self) -> dict:
        """获取连接统计信息（线程安全）"""
        async with self._lock:
            return {
                "index": self.index,
                "is_healthy": self.is_healthy,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "last_error_time": self.last_error_time
            }

    async def close(self):
        """关闭连接"""
        try:
            await self.channel.close()
            logger.debug(
                f"Async channel #{self.index} closed",
                extra={"log_type": "channel_pool"}
            )
        except Exception as e:
            logger.warning(
                f"Error closing async channel #{self.index}: {e}",
                extra={"log_type": "channel_pool"}
            )


class AsyncChannelPool:
    """
    异步 gRPC Channel 连接池

    管理多个 gRPC channel 以提升并发性能和连接稳定性。

    特性：
    - Round-robin 负载均衡
    - 被动健康检查（基于错误自动标记）
    - 自动恢复机制
    - 异步线程安全

    使用示例：
        pool = AsyncChannelPool(
            pool_size=5,
            server_address="localhost:50051",
            channel_options=[...],
            use_tls=False,
            stub_class=ModelServiceStub,
            logger=logger
        )
        await pool.initialize()

        # 使用连接池
        stub = await pool.get_stub()
        response = await stub.Invoke(request)

        # 记录错误
        await pool.record_error(error)

        # 关闭连接池
        await pool.close()
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
            server_address: gRPC 服务器地址
            channel_options: gRPC channel 配置选项
            use_tls: 是否使用 TLS
            stub_class: gRPC 存根类
            logger: 日志记录器
        """
        self.pool_size = pool_size
        self.server_address = server_address
        self.channel_options = channel_options
        self.use_tls = use_tls
        self.stub_class = stub_class
        self.logger = logger

        self.channels: List[AsyncChannelWrapper] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._initialized = False

        logger.info(
            f"🏊 Initializing async connection pool with {pool_size} channels",
            extra={
                "log_type": "pool_init",
                "data": {
                    "pool_size": pool_size,
                    "server_address": server_address,
                    "use_tls": use_tls,
                    "type": "async"
                }
            }
        )

    async def initialize(self):
        """初始化所有连接"""
        if self._initialized:
            return

        success_count = 0
        for i in range(self.pool_size):
            try:
                wrapper = await self._create_channel(i)
                self.channels.append(wrapper)
                success_count += 1
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to create async channel #{i}: {e}",
                    extra={"log_type": "pool_init", "data": {"index": i}}
                )

        self._initialized = True

        if success_count > 0:
            self.logger.info(
                f"✅ Async connection pool initialized: {success_count}/{self.pool_size} channels",
                extra={
                    "log_type": "pool_init",
                    "data": {
                        "success_count": success_count,
                        "pool_size": self.pool_size,
                        "type": "async"
                    }
                }
            )
        else:
            self.logger.error(
                f"❌ Async connection pool initialization failed: 0/{self.pool_size} channels",
                extra={"log_type": "pool_init"}
            )
            raise ConnectionError(f"Failed to initialize async connection pool: no channels available")

    async def _create_channel(self, index: int) -> AsyncChannelWrapper:
        """
        创建单个 gRPC channel

        Args:
            index: 连接索引

        Returns:
            AsyncChannelWrapper: 创建的连接包装器
        """
        if self.use_tls:
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.aio.secure_channel(
                self.server_address,
                credentials,
                options=self.channel_options
            )
        else:
            channel = grpc.aio.insecure_channel(
                f"dns:///{self.server_address}",
                options=self.channel_options
            )

        # 等待连接就绪
        await channel.channel_ready()

        stub = self.stub_class(channel)
        wrapper = AsyncChannelWrapper(index, channel, stub)

        return wrapper

    async def get_stub(self):
        """
        获取可用的 gRPC stub (Round-robin)

        使用 round-robin 策略选择连接，优先选择健康的连接。
        如果所有连接都不健康，则从所有连接中选择。

        Returns:
            gRPC stub
        """
        if not self._initialized:
            await self.initialize()

        wrapper = await self._get_wrapper()
        await wrapper.mark_used()
        return wrapper.stub

    async def _get_wrapper(self) -> AsyncChannelWrapper:
        """
        获取连接包装器（内部方法）

        Returns:
            AsyncChannelWrapper: 选中的连接包装器
        """
        async with self._lock:
            # 尝试恢复不健康的连接
            for wrapper in self.channels:
                await wrapper.try_recover()

            # 筛选健康连接
            healthy_channels = [w for w in self.channels if w.is_healthy]

            # 如果没有健康连接，使用所有连接
            if not healthy_channels:
                self.logger.warning(
                    "⚠️ No healthy async channels available, using all channels",
                    extra={"log_type": "channel_pool"}
                )
                healthy_channels = self.channels

            # Round-robin 选择
            wrapper = healthy_channels[self._current_index % len(healthy_channels)]
            self._current_index = (self._current_index + 1) % len(healthy_channels)

            return wrapper

    async def record_error(self, error: grpc.RpcError):
        """
        记录错误到当前使用的连接

        注意：由于异步特性，无法精确追踪是哪个连接产生的错误，
        因此这个方法是最佳努力（best effort）。

        Args:
            error: gRPC 错误对象
        """
        # 获取最近使用的连接（最佳努力）
        if self.channels:
            async with self._lock:
                # 使用上一次选择的连接索引
                last_index = (self._current_index - 1) % len(self.channels)
                wrapper = self.channels[last_index]
                await wrapper.mark_error(error)

    async def get_stats(self) -> dict:
        """
        获取连接池统计信息

        Returns:
            dict: 包含所有连接的统计信息
        """
        stats = {
            "pool_size": self.pool_size,
            "server_address": self.server_address,
            "channels": []
        }

        for wrapper in self.channels:
            channel_stats = await wrapper.get_stats()
            stats["channels"].append(channel_stats)

        # 计算健康连接数
        stats["healthy_count"] = sum(1 for ch in stats["channels"] if ch["is_healthy"])
        stats["total_requests"] = sum(ch["request_count"] for ch in stats["channels"])
        stats["total_errors"] = sum(ch["error_count"] for ch in stats["channels"])

        return stats

    async def close(self):
        """关闭所有连接"""
        self.logger.info(
            f"🔒 Closing async connection pool ({len(self.channels)} channels)",
            extra={"log_type": "pool_close"}
        )

        for wrapper in self.channels:
            await wrapper.close()

        self.channels.clear()
        self._initialized = False
