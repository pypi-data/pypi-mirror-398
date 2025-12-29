#!/usr/bin/env python3
"""
简化版的 Google/Azure 场景测试脚本
只保留基本调用和打印功能
"""

import asyncio
import logging
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = "localhost:50051"
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = "model-manager-server-jwt-key"

# 导入客户端模块
try:
    from tamar_model_client import TamarModelClient, AsyncTamarModelClient
    from tamar_model_client.schemas import ModelRequest, UserContext
    from tamar_model_client.enums import ProviderType, InvokeType, Channel
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)


def test_google_ai_studio():
    """测试 Google AI Studio"""
    print("\n🔍 测试 Google AI Studio...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            channel=Channel.AI_STUDIO,
            invoke_type=InvokeType.GENERATION,
            model="gemini-pro",
            contents=[
                {"role": "user", "parts": [{"text": "Hello, how are you?"}]}
            ],
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            config={
                "temperature": 0.7,
                "maxOutputTokens": 100
            }
        )

        response = client.invoke(request)
        print(f"✅ Google AI Studio 成功")
        print(f"   响应类型: {type(response)}")
        print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ Google AI Studio 失败: {str(e)}")


def test_google_vertex_ai():
    """测试 Google Vertex AI"""
    print("\n🔍 测试 Google Vertex AI...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            channel=Channel.VERTEXAI,
            invoke_type=InvokeType.GENERATION,
            model="gemini-1.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": "What is AI?"}]}
            ],
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            config={
                "temperature": 0.5
            }
        )

        response = client.invoke(request)
        print(f"✅ Google Vertex AI 成功")
        print(f"   响应类型: {type(response)}")
        print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ Google Vertex AI 失败: {str(e)}")


def test_azure_openai():
    """测试 Azure OpenAI"""
    print("\n☁️  测试 Azure OpenAI...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.AZURE,
            channel=Channel.OPENAI,
            invoke_type=InvokeType.CHAT_COMPLETIONS,
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            temperature=0.7,
            max_tokens=100
        )

        response = client.invoke(request)
        print(f"✅ Azure OpenAI 成功")
        print(f"   响应类型: {type(response)}")
        print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ Azure OpenAI 失败: {str(e)}")


async def test_google_streaming():
    """测试 Google 流式响应"""
    print("\n📡 测试 Google 流式响应...")

    try:
        client = AsyncTamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            channel=Channel.AI_STUDIO,
            invoke_type=InvokeType.GENERATION,
            model="gemini-pro",
            contents=[
                {"role": "user", "parts": [{"text": "Count 1 to 5"}]}
            ],
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            stream=True,
            config={
                "temperature": 0.1,
                "maxOutputTokens": 50
            }
        )

        response_gen = await client.invoke(request)
        print(f"✅ Google 流式调用成功")
        print(f"   响应类型: {type(response_gen)}")

        chunk_count = 0
        async for chunk in response_gen:
            chunk_count += 1
            print(f"   数据块 {chunk_count}: {type(chunk)} - {str(chunk)[:100]}...")
            if chunk_count >= 3:  # 只显示前3个数据块
                break

    except Exception as e:
        print(f"❌ Google 流式响应失败: {str(e)}")


async def test_azure_streaming():
    """测试 Azure 流式响应"""
    print("\n📡 测试 Azure 流式响应...")

    try:
        client = AsyncTamarModelClient()

        request = ModelRequest(
            provider=ProviderType.AZURE,
            channel=Channel.OPENAI,
            invoke_type=InvokeType.CHAT_COMPLETIONS,
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Count 1 to 5"}
            ],
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            stream=True,
            temperature=0.1,
            max_tokens=50
        )

        response_gen = await client.invoke(request)
        print(f"✅ Azure 流式调用成功")
        print(f"   响应类型: {type(response_gen)}")

        chunk_count = 0
        async for chunk in response_gen:
            chunk_count += 1
            print(f"   数据块 {chunk_count}: {type(chunk)} - {str(chunk)[:100]}...")
            if chunk_count >= 3:  # 只显示前3个数据块
                break

    except Exception as e:
        print(f"❌ Azure 流式响应失败: {str(e)}")


async def main():
    """主函数"""
    print("🚀 简化版 Google/Azure 测试")
    print("=" * 50)

    # 同步测试
    test_google_ai_studio()
    test_google_vertex_ai()
    test_azure_openai()

    # 异步流式测试
    await test_google_streaming()
    await test_azure_streaming()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())