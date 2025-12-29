#!/usr/bin/env python3
"""
流式响应挂起分析和解决方案演示

这个脚本模拟各种流式响应挂起场景，并展示解决方案。
"""

import asyncio
import time
import logging
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StreamingFailureType(Enum):
    """流式响应失败类型"""
    PARTIAL_DATA_THEN_HANG = "partial_data_then_hang"          # 发送部分数据后挂起
    NETWORK_INTERRUPTION = "network_interruption"              # 网络中断
    SERVER_CRASH = "server_crash"                              # 服务器崩溃
    SLOW_RESPONSE = "slow_response"                             # 响应过慢
    CONNECTION_RESET = "connection_reset"                       # 连接重置


@dataclass
class StreamChunk:
    """流式数据块"""
    content: str
    chunk_id: int
    is_last: bool = False
    error: Optional[str] = None


class MockStreamingServer:
    """模拟流式服务器的各种故障场景"""

    def __init__(self, failure_type: StreamingFailureType, failure_at_chunk: int = 3):
        self.failure_type = failure_type
        self.failure_at_chunk = failure_at_chunk
        self.chunks_sent = 0

    async def generate_stream(self) -> AsyncIterator[StreamChunk]:
        """生成流式数据"""
        try:
            while True:
                self.chunks_sent += 1

                # 正常发送数据
                if self.chunks_sent <= self.failure_at_chunk:
                    chunk = StreamChunk(
                        content=f"数据块 {self.chunks_sent}",
                        chunk_id=self.chunks_sent,
                        is_last=(self.chunks_sent == 10)  # 假设10个块就结束
                    )
                    logger.info(f"📦 发送数据块 {self.chunks_sent}: {chunk.content}")
                    yield chunk

                    # 模拟正常的块间延迟
                    await asyncio.sleep(0.1)

                    if chunk.is_last:
                        logger.info("✅ 流式传输正常完成")
                        return

                # 在指定位置触发故障
                elif self.chunks_sent == self.failure_at_chunk + 1:
                    await self._trigger_failure()
                    # 故障后就不再发送数据
                    return

        except Exception as e:
            logger.error(f"❌ 流式传输异常: {e}")
            yield StreamChunk(
                content="",
                chunk_id=self.chunks_sent,
                error=str(e)
            )

    async def _trigger_failure(self):
        """触发特定类型的故障"""
        logger.warning(f"⚠️ 触发故障类型: {self.failure_type.value}")

        if self.failure_type == StreamingFailureType.PARTIAL_DATA_THEN_HANG:
            logger.warning("🔄 服务器发送部分数据后挂起...")
            # 无限等待，模拟服务器挂起
            await asyncio.sleep(3600)  # 等待1小时（实际会被超时机制打断）

        elif self.failure_type == StreamingFailureType.NETWORK_INTERRUPTION:
            logger.warning("📡 模拟网络中断...")
            await asyncio.sleep(2)  # 短暂延迟后
            raise ConnectionError("网络连接中断")

        elif self.failure_type == StreamingFailureType.SERVER_CRASH:
            logger.warning("💥 模拟服务器崩溃...")
            raise RuntimeError("服务器内部错误")

        elif self.failure_type == StreamingFailureType.SLOW_RESPONSE:
            logger.warning("🐌 模拟服务器响应过慢...")
            await asyncio.sleep(30)  # 30秒延迟

        elif self.failure_type == StreamingFailureType.CONNECTION_RESET:
            logger.warning("🔌 模拟连接重置...")
            raise ConnectionResetError("连接被重置")


class StreamConsumer:
    """流式数据消费者，演示不同的处理策略"""

    def __init__(self, name: str):
        self.name = name
        self.chunks_received = 0
        self.start_time = time.time()

    async def consume_stream_basic(self, stream: AsyncIterator[StreamChunk]) -> bool:
        """基础流消费（容易挂起的版本）"""
        logger.info(f"🔄 {self.name}: 开始基础流消费...")

        try:
            async for chunk in stream:
                self.chunks_received += 1
                logger.info(f"📥 {self.name}: 收到数据块 {chunk.chunk_id}: {chunk.content}")

                if chunk.error:
                    logger.error(f"❌ {self.name}: 数据块包含错误: {chunk.error}")
                    return False

                if chunk.is_last:
                    logger.info(f"✅ {self.name}: 流正常结束")
                    return True

            logger.warning(f"⚠️ {self.name}: 流意外结束")
            return False

        except Exception as e:
            logger.error(f"❌ {self.name}: 流消费异常: {e}")
            return False

    async def consume_stream_with_timeout(self, stream: AsyncIterator[StreamChunk],
                                        chunk_timeout: float = 5.0) -> bool:
        """带超时保护的流消费"""
        logger.info(f"🔄 {self.name}: 开始带超时保护的流消费 (块超时: {chunk_timeout}s)...")

        try:
            # 注意：这种方法仍然有问题，因为 async for 本身不能被超时保护
            async for chunk in stream:
                self.chunks_received += 1
                logger.info(f"📥 {self.name}: 收到数据块 {chunk.chunk_id}: {chunk.content}")

                if chunk.error:
                    logger.error(f"❌ {self.name}: 数据块包含错误: {chunk.error}")
                    return False

                if chunk.is_last:
                    logger.info(f"✅ {self.name}: 流正常结束")
                    return True

            logger.warning(f"⚠️ {self.name}: 流意外结束")
            return False

        except asyncio.TimeoutError:
            logger.error(f"⏰ {self.name}: 流消费超时")
            return False
        except Exception as e:
            logger.error(f"❌ {self.name}: 流消费异常: {e}")
            return False

    async def consume_stream_with_chunk_timeout(self, stream: AsyncIterator[StreamChunk],
                                              chunk_timeout: float = 5.0,
                                              total_timeout: float = 60.0) -> bool:
        """正确的超时保护方案"""
        logger.info(f"🔄 {self.name}: 开始改进的流消费 (块超时: {chunk_timeout}s, 总超时: {total_timeout}s)...")

        stream_iter = stream.__aiter__()
        overall_start = time.time()

        try:
            while True:
                # 检查总体超时
                if time.time() - overall_start > total_timeout:
                    logger.error(f"⏰ {self.name}: 总体超时 ({total_timeout}s)")
                    return False

                # 对单个数据块获取进行超时保护
                try:
                    chunk = await asyncio.wait_for(
                        stream_iter.__anext__(),
                        timeout=chunk_timeout
                    )

                    self.chunks_received += 1
                    logger.info(f"📥 {self.name}: 收到数据块 {chunk.chunk_id}: {chunk.content}")

                    if chunk.error:
                        logger.error(f"❌ {self.name}: 数据块包含错误: {chunk.error}")
                        return False

                    if chunk.is_last:
                        logger.info(f"✅ {self.name}: 流正常结束")
                        return True

                except asyncio.TimeoutError:
                    logger.error(f"⏰ {self.name}: 等待下一个数据块超时 ({chunk_timeout}s)")
                    return False

                except StopAsyncIteration:
                    logger.warning(f"⚠️ {self.name}: 流意外结束")
                    return False

        except Exception as e:
            logger.error(f"❌ {self.name}: 流消费异常: {e}")
            return False

    async def consume_stream_with_heartbeat(self, stream: AsyncIterator[StreamChunk],
                                          heartbeat_interval: float = 2.0) -> bool:
        """带心跳检测的流消费"""
        logger.info(f"🔄 {self.name}: 开始带心跳检测的流消费...")

        stream_iter = stream.__aiter__()
        last_heartbeat = time.time()

        async def heartbeat_monitor():
            """心跳监控任务"""
            while True:
                await asyncio.sleep(heartbeat_interval)
                if time.time() - last_heartbeat > heartbeat_interval * 3:
                    logger.warning(f"💓 {self.name}: 心跳超时，可能存在问题")

        # 启动心跳监控
        heartbeat_task = asyncio.create_task(heartbeat_monitor())

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        stream_iter.__anext__(),
                        timeout=10.0  # 10秒超时
                    )

                    last_heartbeat = time.time()  # 更新心跳时间
                    self.chunks_received += 1
                    logger.info(f"📥 {self.name}: 收到数据块 {chunk.chunk_id}: {chunk.content}")

                    if chunk.error:
                        logger.error(f"❌ {self.name}: 数据块包含错误: {chunk.error}")
                        return False

                    if chunk.is_last:
                        logger.info(f"✅ {self.name}: 流正常结束")
                        return True

                except asyncio.TimeoutError:
                    logger.error(f"⏰ {self.name}: 等待数据块超时")
                    return False

                except StopAsyncIteration:
                    logger.warning(f"⚠️ {self.name}: 流意外结束")
                    return False

        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


async def test_streaming_failure_scenario(failure_type: StreamingFailureType):
    """测试特定的流式失败场景"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 测试场景: {failure_type.value}")
    logger.info(f"{'='*60}")

    # 创建模拟服务器
    server = MockStreamingServer(failure_type, failure_at_chunk=3)

    # 创建不同策略的消费者
    consumers = [
        ("基础消费者", "consume_stream_basic"),
        ("改进的超时消费者", "consume_stream_with_chunk_timeout"),
        ("心跳检测消费者", "consume_stream_with_heartbeat")
    ]

    for consumer_name, method_name in consumers:
        logger.info(f"\n🔍 测试 {consumer_name}...")

        consumer = StreamConsumer(consumer_name)
        stream = server.generate_stream()

        start_time = time.time()

        try:
            # 根据方法名调用不同的消费策略
            method = getattr(consumer, method_name)

            if method_name == "consume_stream_basic":
                # 基础方法需要额外的超时保护
                success = await asyncio.wait_for(method(stream), timeout=15.0)
            else:
                success = await method(stream)

            duration = time.time() - start_time

            if success:
                logger.info(f"✅ {consumer_name} 成功完成，耗时: {duration:.2f}s，收到 {consumer.chunks_received} 个数据块")
            else:
                logger.warning(f"⚠️ {consumer_name} 未能成功完成，耗时: {duration:.2f}s，收到 {consumer.chunks_received} 个数据块")

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"⏰ {consumer_name} 超时，耗时: {duration:.2f}s，收到 {consumer.chunks_received} 个数据块")

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {consumer_name} 异常: {e}，耗时: {duration:.2f}s，收到 {consumer.chunks_received} 个数据块")

        # 重置服务器状态进行下一个测试
        server = MockStreamingServer(failure_type, failure_at_chunk=3)


async def main():
    """主测试函数"""
    logger.info("🚀 开始流式响应挂起分析...")

    # 测试各种失败场景
    failure_scenarios = [
        StreamingFailureType.PARTIAL_DATA_THEN_HANG,
        StreamingFailureType.NETWORK_INTERRUPTION,
        StreamingFailureType.SERVER_CRASH,
        StreamingFailureType.SLOW_RESPONSE,
    ]

    for scenario in failure_scenarios:
        try:
            await test_streaming_failure_scenario(scenario)
        except Exception as e:
            logger.error(f"❌ 测试场景 {scenario.value} 时出错: {e}")

    logger.info(f"\n{'='*60}")
    logger.info("🎯 分析结论:")
    logger.info("1. 基础的 async for 循环容易在流中断时挂起")
    logger.info("2. 需要对单个数据块的获取进行超时保护")
    logger.info("3. 心跳检测可以提供额外的监控能力")
    logger.info("4. 总体超时 + 块超时的双重保护最为可靠")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断测试")
    finally:
        logger.info("🏁 流式响应分析完成")