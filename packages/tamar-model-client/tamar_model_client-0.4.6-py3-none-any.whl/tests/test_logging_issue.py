#!/usr/bin/env python3
"""
测试日志格式问题
"""

import asyncio
import logging
import os
import sys

# 设置环境变量
os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = "localhost:50051"
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = "model-manager-server-jwt-key"

# 先导入 SDK
from tamar_model_client import AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel

# 检查 SDK 的日志配置
print("=== SDK Logger Configuration ===")
sdk_loggers = [
    'tamar_model_client',
    'tamar_model_client.async_client',
    'tamar_model_client.error_handler',
    'tamar_model_client.core.base_client'
]

for logger_name in sdk_loggers:
    logger = logging.getLogger(logger_name)
    print(f"\nLogger: {logger_name}")
    print(f"  Level: {logging.getLevelName(logger.level)}")
    print(f"  Handlers: {len(logger.handlers)}")
    for i, handler in enumerate(logger.handlers):
        print(f"    Handler {i}: {type(handler).__name__}")
        if hasattr(handler, 'formatter'):
            print(f"      Formatter: {type(handler.formatter).__name__ if handler.formatter else 'None'}")
    print(f"  Propagate: {logger.propagate}")


async def test_error_logging():
    """测试错误日志格式"""
    print("\n=== Testing Error Logging ===")

    try:
        async with AsyncTamarModelClient() as client:
            # 故意创建一个会失败的请求
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.VERTEXAI,
                invoke_type=InvokeType.GENERATION,
                model="invalid-model",
                contents="test",
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                )
            )

            response = await client.invoke(request, timeout=5.0)
            print(f"Response: {response}")

    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {str(e)}")


async def main():
    await test_error_logging()


if __name__ == "__main__":
    print("Starting logging test...")
    asyncio.run(main())