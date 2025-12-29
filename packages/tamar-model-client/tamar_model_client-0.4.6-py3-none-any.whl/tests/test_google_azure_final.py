#!/usr/bin/env python3
"""
简化版的 Google/Azure 场景测试脚本
只保留基本调用和打印功能
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple

# 配置测试脚本专用的日志
# 使用特定的logger名称，避免影响客户端日志
test_logger = logging.getLogger('test_google_azure_final')
test_logger.setLevel(logging.INFO)
test_logger.propagate = False  # 不传播到根logger

# 创建测试脚本专用的handler
test_handler = logging.StreamHandler()
test_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
test_logger.addHandler(test_handler)

logger = test_logger

os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = "localhost:50052"
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = "model-manager-server-jwt-key"

# 导入客户端模块
try:
    from tamar_model_client import TamarModelClient, AsyncTamarModelClient
    from tamar_model_client.schemas import ModelRequest, UserContext
    from tamar_model_client.enums import ProviderType, InvokeType, Channel
    from google.genai import types

    # 为了调试，临时启用 SDK 的日志输出
    # 注意：这会输出 JSON 格式的日志
    import os

    os.environ['TAMAR_MODEL_CLIENT_LOG_LEVEL'] = 'INFO'

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
            model="tamar-google-gemini-flash-lite",
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
        print(response)
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
            model="tamar-google-gemini-flash-lite",
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
        )

        response = client.invoke(request)
        print(f"✅ Azure OpenAI 成功")
        print(f"   响应内容: {response.model_dump_json()}...")

    except Exception as e:
        print(f"❌ Azure OpenAI 失败: {str(e)}")


def test_google_genai_image_generation():
    """测试 Google GenAI 图像生成"""
    print("\n🎨 测试 Google GenAI 图像生成...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            channel=Channel.AI_STUDIO,
            invoke_type=InvokeType.IMAGE_GENERATION_GENAI,
            model="imagen-3.0-generate-002",
            prompt="一只可爱的小猫咪在花园里玩耍，阳光透过树叶洒下斑驳的光影",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)
        print(f"✅ Google GenAI 图像生成调用成功")
        print(f"   响应类型: {type(response)}")
        
        # 检查图像数据：raw_response中应该包含image_bytes
        has_image_data = False
        if response.raw_response and isinstance(response.raw_response, list):
            for item in response.raw_response:
                if isinstance(item, dict) and 'image_bytes' in item and item['image_bytes']:
                    has_image_data = True
                    print(f"   图像数据长度: {len(item['image_bytes'])}")
                    break
        
        if has_image_data:
            print(f"   ✅ 图像生成成功！")
        elif response.content:
            print(f"   文本内容长度: {len(str(response.content[:200]))}")
        else:
            print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ Google GenAI 图像生成失败: {str(e)}")


def test_google_vertex_ai_image_generation():
    """测试 Google Vertex AI 图像生成 (对比)"""
    print("\n🎨 测试 Google Vertex AI 图像生成...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            channel=Channel.VERTEXAI,
            invoke_type=InvokeType.IMAGE_GENERATION,
            model="imagegeneration@006",
            prompt="一座雄伟的雪山在黄昏时分",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)
        print(f"✅ Google Vertex AI 图像生成调用成功")
        print(f"   响应类型: {type(response)}")
        
        # 检查图像数据：raw_response中应该包含image_bytes
        has_image_data = False
        if response.raw_response and isinstance(response.raw_response, list):
            for item in response.raw_response:
                if isinstance(item, dict) and 'image_bytes' in item and item['image_bytes']:
                    has_image_data = True
                    print(f"   图像数据长度: {len(item['image_bytes'])}")
                    break
        
        if has_image_data:
            print(f"   ✅ 图像生成成功！")
        elif response.content:
            print(f"   文本内容长度: {len(str(response.content[:200]))}")
        else:
            print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ Google Vertex AI 图像生成失败: {str(e)}")


async def test_google_streaming():
    """测试 Google 流式响应"""
    print("\n📡 测试 Google 流式响应...")

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.AI_STUDIO,
                invoke_type=InvokeType.GENERATION,
                model="tamar-google-gemini-flash-lite",
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
                print(f"   数据块 {chunk_count}: {type(chunk)} - {chunk.model_dump_json()}...")
                if chunk_count >= 3:  # 只显示前3个数据块
                    break

    except Exception as e:
        print(f"❌ Google 流式响应失败: {str(e)}")


async def test_azure_streaming():
    """测试 Azure 流式响应"""
    print("\n📡 测试 Azure 流式响应...")

    try:
        async with AsyncTamarModelClient() as client:
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
                stream=True  # 添加流式参数
            )

            response_gen = await client.invoke(request)
            print(f"✅ Azure 流式调用成功")
            print(f"   响应类型: {type(response_gen)}")

            chunk_count = 0
            async for chunk in response_gen:
                chunk_count += 1
                print(f"   数据块 {chunk_count}: {type(chunk)} - {chunk.model_dump_json()}...")
                if chunk_count >= 3:  # 只显示前3个数据块
                    break

    except Exception as e:
        print(f"❌ Azure 流式响应失败: {str(e)}")


async def test_google_genai_image_generation_async():
    """测试异步 Google GenAI 图像生成"""
    print("\n🎨 测试异步 Google GenAI 图像生成...")

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.AI_STUDIO,
                invoke_type=InvokeType.IMAGE_GENERATION_GENAI,
                model="imagen-3.0-generate-002",
                prompt="现代城市夜景，霓虹灯闪烁，繁华热闹的街道",
                user_context=UserContext(
                    user_id="test_user_async",
                    org_id="test_org",
                    client_type="test_client_async"
                )
            )

            response = await client.invoke(request, timeout=60000.0)
            print(f"✅ 异步 Google GenAI 图像生成调用成功")
            print(f"   响应类型: {type(response)}")

            # 检查图像数据：raw_response中应该包含image_bytes
            has_image_data = False
            if response.raw_response and isinstance(response.raw_response, list):
                for item in response.raw_response:
                    if isinstance(item, dict) and 'image_bytes' in item and item['image_bytes']:
                        has_image_data = True
                        print(f"   图像数据长度: {len(item['image_bytes'])}")
                        break
            
            if has_image_data:
                print(f"   ✅ 图像生成成功！")
            elif response.content:
                print(f"   文本内容长度: {len(str(response.content[:200]))}")
                print(f"   ✅ 图像生成成功！")
            elif response.error:
                print(f"   错误: {response.error}")
            else:
                print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ 异步 Google GenAI 图像生成失败: {str(e)}")


async def test_google_vertex_ai_image_generation_async():
    """测试异步 Google Vertex AI 图像生成 (对比)"""
    print("\n🎨 测试异步 Google Vertex AI 图像生成...")

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.VERTEXAI,
                invoke_type=InvokeType.IMAGE_GENERATION,
                model="imagegeneration@006",
                prompt="宁静的湖泊倒映着夕阳，周围环绕着青山绿树",
                user_context=UserContext(
                    user_id="test_user_async",
                    org_id="test_org",
                    client_type="test_client_async"
                )
            )

            response = await client.invoke(request, timeout=60000.0)
            print(f"✅ 异步 Google Vertex AI 图像生成调用成功")
            print(f"   响应类型: {type(response)}")

            # 检查图像数据：raw_response中应该包含image_bytes
            has_image_data = False
            if response.raw_response and isinstance(response.raw_response, list):
                for item in response.raw_response:
                    if isinstance(item, dict) and 'image_bytes' in item and item['image_bytes']:
                        has_image_data = True
                        print(f"   图像数据长度: {len(item['image_bytes'])}")
                        break
            
            if has_image_data:
                print(f"   ✅ 图像生成成功！")
            elif response.content:
                print(f"   文本内容长度: {len(str(response.content))}")
                print(f"   ✅ 图像生成成功！")
            elif response.error:
                print(f"   错误: {response.error}")
            else:
                print(f"   响应内容: {str(response)[:200]}...")

    except Exception as e:
        print(f"❌ 异步 Google Vertex AI 图像生成失败: {str(e)}")


def test_sync_batch_requests():
    """测试同步批量请求"""
    print("\n📦 测试同步批量请求...")

    try:
        from tamar_model_client.schemas import BatchModelRequest, BatchModelRequestItem

        with TamarModelClient() as client:
            # 构建批量请求，包含 Google 和 Azure 的多个请求
            batch_request = BatchModelRequest(
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                ),
                items=[
                    # Google AI Studio 请求
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=[
                            {"role": "user", "parts": [{"text": "Hello from sync batch - Google AI Studio"}]}
                        ],
                        custom_id="sync-google-ai-studio-1",
                    ),
                    # Azure OpenAI 请求
                    BatchModelRequestItem(
                        provider=ProviderType.AZURE,
                        invoke_type=InvokeType.CHAT_COMPLETIONS,
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": "Hello from sync batch - Azure OpenAI"}
                        ],
                        custom_id="sync-azure-openai-1",
                    ),
                    # 再添加一个 Azure 请求
                    BatchModelRequestItem(
                        provider=ProviderType.AZURE,
                        invoke_type=InvokeType.CHAT_COMPLETIONS,
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": "What is 2+2?"}
                        ],
                        custom_id="sync-azure-openai-2",
                    )
                ]
            )

            # 执行批量请求
            batch_response = client.invoke_batch(batch_request)

            print(f"✅ 同步批量请求成功")
            print(f"   请求数量: {len(batch_request.items)}")
            print(f"   响应数量: {len(batch_response.responses)}")
            print(f"   批量请求ID: {batch_response.request_id}")

            # 显示每个响应的结果
            for i, response in enumerate(batch_response.responses):
                print(f"\n   响应 {i + 1}:")
                print(f"   - custom_id: {response.custom_id}")
                print(f"   - 内容长度: {len(response.content) if response.content else 0}")
                print(f"   - 有错误: {'是' if response.error else '否'}")
                if response.content:
                    print(f"   - 内容预览: {response.content[:100]}...")
                if response.error:
                    print(f"   - 错误信息: {response.error}")
                if response.raw_response:
                    print(f"   - 原信息: {json.dumps(response.raw_response)}")

    except Exception as e:
        print(f"❌ 同步批量请求失败: {str(e)}")


async def test_batch_requests():
    """测试异步批量请求"""
    print("\n📦 测试异步批量请求...")

    try:
        from tamar_model_client.schemas import BatchModelRequest, BatchModelRequestItem

        async with AsyncTamarModelClient() as client:
            # 构建批量请求，包含 Google 和 Azure 的多个请求
            batch_request = BatchModelRequest(
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                ),
                items=[
                    # Google AI Studio 请求
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=[
                            {"role": "user", "parts": [{"text": "Hello from Google AI Studio"}]}
                        ],
                        custom_id="google-ai-studio-1",
                    ),
                    # Google Vertex AI 请求
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.VERTEXAI,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=[
                            {"role": "user", "parts": [{"text": "Hello from Google Vertex AI"}]}
                        ],
                        custom_id="google-vertex-ai-1",
                    ),
                    # Google GenAI 图像生成请求
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.AI_STUDIO,
                        invoke_type=InvokeType.IMAGE_GENERATION_GENAI,
                        model="imagen-3.0-generate-002",
                        prompt="一朵美丽的玫瑰花在阳光下绽放",
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="1:1"
                        ),
                        custom_id="google-genai-image-1",
                    ),
                    # Azure OpenAI 请求
                    BatchModelRequestItem(
                        provider=ProviderType.AZURE,
                        invoke_type=InvokeType.CHAT_COMPLETIONS,
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": "Hello from Azure OpenAI"}
                        ],
                        custom_id="azure-openai-1",
                    ),
                    # 再添加一个 Azure 请求
                    BatchModelRequestItem(
                        provider=ProviderType.AZURE,
                        invoke_type=InvokeType.CHAT_COMPLETIONS,
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": "What is the capital of France?"}
                        ],
                        custom_id="azure-openai-2",
                    )
                ]
            )

            # 执行批量请求
            batch_response = await client.invoke_batch(batch_request)

            print(f"✅ 批量请求成功")
            print(f"   请求数量: {len(batch_request.items)}")
            print(f"   响应数量: {len(batch_response.responses)}")
            print(f"   批量请求ID: {batch_response.request_id}")

            # 显示每个响应的结果
            for i, response in enumerate(batch_response.responses):
                print(f"\n   响应 {i + 1}:")
                print(f"   - custom_id: {response.custom_id}")
                print(f"   - 内容长度: {len(response.content) if response.content else 0}")
                print(f"   - 有错误: {'是' if response.error else '否'}")
                if response.content:
                    print(f"   - 内容预览: {response.content[:100]}...")
                if response.error:
                    print(f"   - 错误信息: {response.error}")
                if response.raw_response:
                    print(f"   - 原信息: {json.dumps(response.raw_response)[:100]}")

    except Exception as e:
        print(f"❌ 批量请求失败: {str(e)}")


async def test_image_generation_batch():
    """测试图像生成批量请求 - 同时测试 GenAI、Vertex AI 图像生成"""
    print("\n🖼️  测试图像生成批量请求...")

    try:
        from tamar_model_client.schemas import BatchModelRequest, BatchModelRequestItem

        async with AsyncTamarModelClient() as client:
            # 构建图像生成批量请求
            batch_request = BatchModelRequest(
                user_context=UserContext(
                    user_id="test_image_batch",
                    org_id="test_org",
                    client_type="image_test_client"
                ),
                items=[
                    # Google GenAI 图像生成请求 1
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.AI_STUDIO,
                        invoke_type=InvokeType.IMAGE_GENERATION_GENAI,
                        model="imagen-3.0-generate-002",
                        prompt="一只可爱的小狗在公园里奔跑",
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="1:1",
                        ),
                        custom_id="genai-dog-1",
                    ),
                    # Google GenAI 图像生成请求 2
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.AI_STUDIO,
                        invoke_type=InvokeType.IMAGE_GENERATION_GENAI,
                        model="imagen-3.0-generate-002",
                        prompt="美丽的樱花盛开在春天的公园里",
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9"
                        ),
                        custom_id="genai-sakura-1",
                    ),
                    # Google Vertex AI 图像生成请求 1
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.VERTEXAI,
                        invoke_type=InvokeType.IMAGE_GENERATION,
                        model="imagen-3.0-generate-002",
                        prompt="壮丽的山峦在夕阳西下时的景色",
                        number_of_images=1,
                        aspect_ratio="16:9",
                        safety_filter_level="block_some",
                        custom_id="vertex-mountain-1",
                    ),
                    # Google Vertex AI 图像生成请求 2
                    BatchModelRequestItem(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.VERTEXAI,
                        invoke_type=InvokeType.IMAGE_GENERATION,
                        model="imagen-3.0-generate-002",
                        prompt="宁静的海滩上有椰子树和海浪",
                        number_of_images=1,
                        aspect_ratio="1:1",
                        safety_filter_level="block_some",
                        custom_id="vertex-beach-1",
                    )
                ]
            )

            # 执行批量图像生成请求
            print(f"   发送批量图像生成请求 (共{len(batch_request.items)}个)...")
            batch_response = await client.invoke_batch(batch_request, timeout=60000.0)

            print(f"✅ 批量图像生成请求成功")
            print(f"   请求数量: {len(batch_request.items)}")
            print(f"   响应数量: {len(batch_response.responses)}")
            print(f"   批量请求ID: {batch_response.request_id}")

            # 详细显示每个图像生成结果
            genai_success = 0
            vertex_success = 0
            total_errors = 0

            for i, response in enumerate(batch_response.responses):
                print(f"\n   图像生成 {i + 1}:")
                print(f"   - custom_id: {response.custom_id}")
                print(f"   - 有错误: {'是' if response.error else '否'}")

                if response.error:
                    total_errors += 1
                    print(f"   - 错误信息: {response.error}")
                else:
                    # 检查图像数据：raw_response中应该包含_image_bytes
                    has_image_data = False
                    if response.raw_response and isinstance(response.raw_response, list):
                        print(f"   - raw_response类型: {type(response.raw_response)}, 长度: {len(response.raw_response)}")
                        for idx, item in enumerate(response.raw_response):
                            print(f"   - item[{idx}]类型: {type(item)}")
                            if isinstance(item, dict):
                                print(f"   - item[{idx}]键: {list(item.keys())}")
                                if 'image_bytes' in item:
                                    image_data = item['image_bytes']
                                    if image_data:
                                        has_image_data = True
                                        print(f"   - 图像数据长度: {len(image_data)}")
                                        break
                                    else:
                                        print(f"   - image_bytes字段为空")
                                elif '_image_bytes' in item:
                                    image_data = item['_image_bytes']
                                    if image_data:
                                        has_image_data = True
                                        print(f"   - 图像数据长度: {len(image_data)}")
                                        break
                                    else:
                                        print(f"   - _image_bytes字段为空")
                                else:
                                    print(f"   - 没有找到image_bytes或者_image_bytes字段")
                    
                    if has_image_data:
                        print(f"   - ✅ 图像生成成功！")
                    elif response.content:
                        print(f"   - 文本内容长度: {len(str(response.content))}")
                        print(f"   - ✅ 图像生成成功！")
                    else:
                        print(f"   - 响应预览: {str(response)[:100]}...")
                        print(f"   - ⚠️ 图像生成可能成功但数据格式异常")

                    # 统计不同类型的成功数（只要没有error就算成功）
                    # 如果custom_id存在，使用它来判断类型
                    if response.custom_id:
                        if "genai" in response.custom_id:
                            genai_success += 1
                        elif "vertex" in response.custom_id:
                            vertex_success += 1
                    else:
                        # 如果custom_id为None，根据响应索引判断类型
                        # 前2个是GenAI请求，后2个是Vertex AI请求
                        if i < 2:  # GenAI 请求 (索引 0, 1)
                            genai_success += 1
                            print(f"   - 根据索引判断为GenAI请求")
                        else:  # Vertex AI 请求 (索引 2, 3)
                            vertex_success += 1
                            print(f"   - 根据索引判断为Vertex AI请求")

            print(f"\n📊 图像生成批量测试统计:")
            print(f"   - GenAI 图像生成成功: {genai_success}/2")
            print(f"   - Vertex AI 图像生成成功: {vertex_success}/2")
            print(f"   - 总错误数: {total_errors}")

    except Exception as e:
        print(f"❌ 批量图像生成请求失败: {str(e)}")


def test_concurrent_requests(num_requests: int = 150):
    """测试并发请求
    
    Args:
        num_requests: 要发送的总请求数，默认150个
    """
    print(f"\n🚀 测试并发请求 ({num_requests} 个请求)...")

    # 统计变量
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    request_times: List[float] = []
    errors: Dict[str, int] = {}

    # 线程安全的锁
    stats_lock = threading.Lock()

    def make_single_request(request_id: int) -> Tuple[bool, float, str]:
        """执行单个请求并返回结果
        
        Returns:
            (success, duration, error_msg)
        """
        start_time = time.time()
        try:
            # 每个线程创建自己的客户端实例
            client = TamarModelClient()

            # Google Vertex AI
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.VERTEXAI,
                invoke_type=InvokeType.GENERATION,
                model="tamar-google-gemini-flash-lite",
                contents="1+1等于几？",
                user_context=UserContext(
                    user_id=f"{os.environ.get('INSTANCE_ID', '0')}_{request_id:03d}",
                    org_id="test_org",
                    client_type="concurrent_test"
                ),
                config={"temperature": 0.1}
            )

            response = client.invoke(request, timeout=300000.0)
            duration = time.time() - start_time
            return (True, duration, "")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            return (False, duration, error_msg)

    def worker(request_id: int):
        """工作线程函数"""
        nonlocal total_requests, successful_requests, failed_requests

        success, duration, error_msg = make_single_request(request_id)

        with stats_lock:
            total_requests += 1
            request_times.append(duration)

            if success:
                successful_requests += 1
            else:
                failed_requests += 1
                # 统计错误类型
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg[:50]
                errors[error_type] = errors.get(error_type, 0) + 1

            # 每20个请求输出一次进度
            if total_requests % 20 == 0:
                print(
                    f"   进度: {total_requests}/{num_requests} (成功: {successful_requests}, 失败: {failed_requests})")

    # 使用线程池执行并发请求
    start_time = time.time()

    # 使用线程池，最多50个并发线程
    with ThreadPoolExecutor(max_workers=50) as executor:
        # 提交所有任务
        futures = [executor.submit(worker, i) for i in range(num_requests)]

        # 等待所有任务完成
        for future in futures:
            future.result()

    total_duration = time.time() - start_time

    # 计算统计信息
    avg_request_time = sum(request_times) / len(request_times) if request_times else 0
    min_request_time = min(request_times) if request_times else 0
    max_request_time = max(request_times) if request_times else 0

    # 输出结果
    print(f"\n📊 并发测试结果:")
    print(f"   总请求数: {total_requests}")
    print(f"   成功请求: {successful_requests} ({successful_requests / total_requests * 100:.1f}%)")
    print(f"   失败请求: {failed_requests} ({failed_requests / total_requests * 100:.1f}%)")
    print(f"   总耗时: {total_duration:.2f} 秒")
    print(f"   平均QPS: {total_requests / total_duration:.2f}")
    print(f"\n   请求耗时统计:")
    print(f"   - 平均: {avg_request_time:.3f} 秒")
    print(f"   - 最小: {min_request_time:.3f} 秒")
    print(f"   - 最大: {max_request_time:.3f} 秒")

    if errors:
        print(f"\n   错误统计:")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {error_type}: {count} 次")

    return {
        "total": total_requests,
        "successful": successful_requests,
        "failed": failed_requests,
        "duration": total_duration,
        "qps": total_requests / total_duration
    }


async def test_async_concurrent_requests(num_requests: int = 150):
    """测试异步并发请求
    
    Args:
        num_requests: 要发送的总请求数，默认150个
    """
    print(f"\n🚀 测试异步并发请求 ({num_requests} 个请求)...")

    # 统计变量
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    request_times: List[float] = []
    errors: Dict[str, int] = {}
    trace_id = "88888888888888888333333888888883333388888"

    # 异步锁
    stats_lock = asyncio.Lock()

    async def make_single_async_request(client: AsyncTamarModelClient, request_id: int) -> Tuple[bool, float, str]:
        """执行单个异步请求并返回结果
        
        Returns:
            (success, duration, error_msg)
        """
        start_time = time.time()
        try:
            # 根据请求ID选择不同的provider，以增加测试多样性
            # Google Vertex AI
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.VERTEXAI,
                invoke_type=InvokeType.GENERATION,
                model="tamar-google-gemini-flash-lite",
                contents="1+1等于几？",
                user_context=UserContext(
                    user_id=f"{os.environ.get('INSTANCE_ID', '0')}_{request_id:03d}",
                    org_id="test_org",
                    client_type="async_concurrent_test"
                ),
                config={"temperature": 0.1}
            )

            response = await client.invoke(request, timeout=300000.0, request_id=trace_id)
            duration = time.time() - start_time
            return (True, duration, "")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            return (False, duration, error_msg)

    async def async_worker(client: AsyncTamarModelClient, request_id: int):
        """异步工作协程"""
        nonlocal total_requests, successful_requests, failed_requests

        success, duration, error_msg = await make_single_async_request(client, request_id)

        async with stats_lock:
            total_requests += 1
            request_times.append(duration)

            if success:
                successful_requests += 1
            else:
                failed_requests += 1
                # 统计错误类型
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg[:50]
                errors[error_type] = errors.get(error_type, 0) + 1

            # 每20个请求输出一次进度
            if total_requests % 20 == 0:
                print(
                    f"   进度: {total_requests}/{num_requests} (成功: {successful_requests}, 失败: {failed_requests})")

    # 使用异步客户端执行并发请求
    start_time = time.time()

    # 创建一个共享的异步客户端
    async with AsyncTamarModelClient() as client:
        # 创建所有任务，但限制并发数
        semaphore = asyncio.Semaphore(50)  # 限制最多50个并发请求

        async def limited_worker(request_id: int):
            async with semaphore:
                await async_worker(client, request_id)

        # 创建所有任务
        tasks = [limited_worker(i) for i in range(num_requests)]

        # 等待所有任务完成
        await asyncio.gather(*tasks)

    total_duration = time.time() - start_time

    # 计算统计信息
    avg_request_time = sum(request_times) / len(request_times) if request_times else 0
    min_request_time = min(request_times) if request_times else 0
    max_request_time = max(request_times) if request_times else 0

    # 输出结果
    print(f"\n📊 异步并发测试结果:")
    print(f"   总请求数: {total_requests}")
    print(f"   成功请求: {successful_requests} ({successful_requests / total_requests * 100:.1f}%)")
    print(f"   失败请求: {failed_requests} ({failed_requests / total_requests * 100:.1f}%)")
    print(f"   总耗时: {total_duration:.2f} 秒")
    print(f"   平均QPS: {total_requests / total_duration:.2f}")
    print(f"\n   请求耗时统计:")
    print(f"   - 平均: {avg_request_time:.3f} 秒")
    print(f"   - 最小: {min_request_time:.3f} 秒")
    print(f"   - 最大: {max_request_time:.3f} 秒")

    if errors:
        print(f"\n   错误统计:")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {error_type}: {count} 次")

    return {
        "total": total_requests,
        "successful": successful_requests,
        "failed": failed_requests,
        "duration": total_duration,
        "qps": total_requests / total_duration
    }


async def test_async_batch_with_circuit_breaker_v2(num_requests: int = 10):
    """
    测试熔断器功能 - 使用单个请求而不是批量请求
    
    通过发送多个单独的请求来触发熔断器，因为批量请求中的单个失败不会触发熔断。
    
    Args:
        num_requests: 要发送的请求数，默认10个
    """
    print(f"\n🔥 测试熔断器功能 - 改进版 ({num_requests} 个独立请求)...")

    # 保存原始环境变量
    import os
    original_env = {}
    env_vars = ['MODEL_CLIENT_RESILIENT_ENABLED', 'MODEL_CLIENT_HTTP_FALLBACK_URL',
                'MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', 'MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT']
    for var in env_vars:
        original_env[var] = os.environ.get(var)

    # 设置环境变量以启用熔断器和HTTP fallback
    os.environ['MODEL_CLIENT_RESILIENT_ENABLED'] = 'true'
    os.environ['MODEL_CLIENT_HTTP_FALLBACK_URL'] = 'http://localhost:8000'
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD'] = '3'  # 3次失败后触发熔断
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT'] = '30'  # 熔断器30秒后恢复

    print(f"   环境变量设置:")
    print(f"   - MODEL_CLIENT_RESILIENT_ENABLED: {os.environ.get('MODEL_CLIENT_RESILIENT_ENABLED')}")
    print(f"   - MODEL_CLIENT_HTTP_FALLBACK_URL: {os.environ.get('MODEL_CLIENT_HTTP_FALLBACK_URL')}")
    print(f"   - 熔断阈值: 3 次失败")

    # 统计变量
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    circuit_breaker_opened = False
    http_fallback_used = 0
    request_times: List[float] = []
    errors: Dict[str, int] = {}

    try:
        # 创建一个共享的异步客户端（启用熔断器）
        async with AsyncTamarModelClient() as client:
            print(f"\n   熔断器配置:")
            print(f"   - 启用状态: {getattr(client, 'resilient_enabled', False)}")
            print(f"   - HTTP Fallback URL: {getattr(client, 'http_fallback_url', 'None')}")

            for i in range(num_requests):
                start_time = time.time()

                try:
                    # 前4个请求使用错误的model来触发失败
                    if i < 4:
                        request = ModelRequest(
                            provider=ProviderType.GOOGLE,
                            invoke_type=InvokeType.GENERATION,
                            model="invalid-model-to-trigger-error",  # 无效模型
                            contents=f"测试失败请求 {i + 1}",
                            user_context=UserContext(
                                user_id=f"circuit_test_{i}",
                                org_id="test_org_circuit",
                                client_type="circuit_test"
                            )
                        )
                    else:
                        # 后续请求使用正确的model
                        request = ModelRequest(
                            provider=ProviderType.GOOGLE,
                            invoke_type=InvokeType.GENERATION,
                            model="tamar-google-gemini-flash-lite",
                            contents=f"测试请求 {i + 1}: 计算 {i} + {i}",
                            user_context=UserContext(
                                user_id=f"circuit_test_{i}",
                                org_id="test_org_circuit",
                                client_type="circuit_test"
                            ),
                            config={"temperature": 0.1}
                        )

                    print(f"\n   📤 发送请求 {i + 1}/{num_requests}...")
                    response = await client.invoke(request, timeout=10000)

                    duration = time.time() - start_time
                    request_times.append(duration)
                    total_requests += 1
                    successful_requests += 1

                    print(f"   ✅ 请求 {i + 1} 成功 - 耗时: {duration:.2f}秒")

                    # 检查是否通过HTTP fallback
                    if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                        try:
                            metrics = client.get_resilient_metrics()
                            if metrics and metrics['circuit_breaker']['state'] == 'open':
                                http_fallback_used += 1
                                print(f"      (通过HTTP fallback)")
                        except:
                            pass

                except Exception as e:
                    duration = time.time() - start_time
                    request_times.append(duration)
                    total_requests += 1
                    failed_requests += 1

                    error_type = type(e).__name__
                    errors[error_type] = errors.get(error_type, 0) + 1

                    print(f"   ❌ 请求 {i + 1} 失败: {error_type} - {str(e)[:100]}")
                    print(f"      耗时: {duration:.2f}秒")

                # 检查熔断器状态
                if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                    try:
                        metrics = client.get_resilient_metrics()
                        if metrics and 'circuit_breaker' in metrics:
                            state = metrics['circuit_breaker']['state']
                            failures = metrics['circuit_breaker']['failure_count']

                            if state == 'open' and not circuit_breaker_opened:
                                circuit_breaker_opened = True
                                print(f"   🔻 熔断器已打开！失败次数: {failures}")

                            print(f"      熔断器: {state}, 失败计数: {failures}")
                    except Exception as e:
                        print(f"      获取熔断器状态失败: {e}")

                # 请求之间短暂等待
                await asyncio.sleep(0.2)

            # 最终统计
            print(f"\n📊 熔断器测试结果:")
            print(f"   总请求数: {total_requests}")
            print(f"   成功请求: {successful_requests}")
            print(f"   失败请求: {failed_requests}")

            print(f"\n   🔥 熔断器统计:")
            print(f"   - 熔断器是否触发: {'是' if circuit_breaker_opened else '否'}")
            print(f"   - HTTP fallback使用次数: {http_fallback_used}")

            # 获取最终状态
            if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                try:
                    final_metrics = client.get_resilient_metrics()
                    if final_metrics and 'circuit_breaker' in final_metrics:
                        print(f"   - 最终状态: {final_metrics['circuit_breaker']['state']}")
                        print(f"   - 总失败次数: {final_metrics['circuit_breaker']['failure_count']}")
                except Exception as e:
                    print(f"   - 获取最终状态失败: {e}")

            if errors:
                print(f"\n   错误统计:")
                for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {error_type}: {count} 次")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 恢复原始环境变量
        for var, value in original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value


async def test_async_batch_with_circuit_breaker(batch_size: int = 10, num_batches: int = 5):
    """测试异步批量请求 - 触发熔断器使用HTTP fallback
    
    这个测试会复用一个AsyncTamarModelClient，通过发送多个批量请求来触发熔断器，
    使其自动切换到HTTP fallback模式。
    
    Args:
        batch_size: 每个批量请求包含的请求数，默认10个
        num_batches: 要发送的批量请求数，默认5个
    """
    print(f"\n🔥 测试异步批量请求 - 熔断器模式 ({num_batches} 个批量，每批 {batch_size} 个请求)...")

    # 保存原始环境变量
    import os
    original_env = {}
    env_vars = ['MODEL_CLIENT_RESILIENT_ENABLED', 'MODEL_CLIENT_HTTP_FALLBACK_URL',
                'MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', 'MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT']
    for var in env_vars:
        original_env[var] = os.environ.get(var)

    # 设置环境变量以启用熔断器和HTTP fallback
    os.environ['MODEL_CLIENT_RESILIENT_ENABLED'] = 'true'
    os.environ['MODEL_CLIENT_HTTP_FALLBACK_URL'] = 'http://localhost:8000'
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD'] = '3'  # 3次失败后触发熔断
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT'] = '60'  # 熔断器60秒后恢复

    # 调试：打印环境变量确认设置成功
    print(f"   环境变量设置:")
    print(f"   - MODEL_CLIENT_RESILIENT_ENABLED: {os.environ.get('MODEL_CLIENT_RESILIENT_ENABLED')}")
    print(f"   - MODEL_CLIENT_HTTP_FALLBACK_URL: {os.environ.get('MODEL_CLIENT_HTTP_FALLBACK_URL')}")

    # 统计变量
    total_batches = 0
    successful_batches = 0
    failed_batches = 0
    circuit_breaker_opened = False
    http_fallback_used = 0
    batch_times: List[float] = []
    errors: Dict[str, int] = {}

    try:
        from tamar_model_client.schemas import BatchModelRequest, BatchModelRequestItem

        # 创建一个共享的异步客户端（启用熔断器）
        async with AsyncTamarModelClient() as client:
            print(f"   熔断器配置:")
            print(f"   - 启用状态: {getattr(client, 'resilient_enabled', False)}")
            print(f"   - HTTP Fallback URL: {getattr(client, 'http_fallback_url', 'None')}")
            if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                try:
                    metrics = client.get_resilient_metrics()
                    if metrics and 'circuit_breaker' in metrics:
                        print(f"   - 熔断阈值: {metrics['circuit_breaker'].get('failure_threshold', 'Unknown')} 次失败")
                        print(f"   - 熔断恢复时间: {metrics['circuit_breaker'].get('recovery_timeout', 'Unknown')} 秒")
                    else:
                        print(f"   - 熔断阈值: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', '5')} 次失败")
                        print(f"   - 熔断恢复时间: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT', '60')} 秒")
                except:
                    print(f"   - 熔断阈值: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', '5')} 次失败")
                    print(f"   - 熔断恢复时间: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT', '60')} 秒")
            else:
                print(f"   - 熔断器未启用")

            for batch_num in range(num_batches):
                start_time = time.time()

                try:
                    # 构建批量请求
                    items = []
                    for i in range(batch_size):
                        request_idx = batch_num * batch_size + i

                        # 混合使用不同的provider和model
                        if request_idx % 4 == 0:
                            # Google Vertex AI
                            item = BatchModelRequestItem(
                                provider=ProviderType.GOOGLE,
                                channel=Channel.VERTEXAI,
                                invoke_type=InvokeType.GENERATION,
                                model="tamar-google-gemini-flash-lite",
                                contents=f"计算 {request_idx} * 2 的结果",
                                custom_id=f"batch-{batch_num}-google-vertex-{i}",
                                config={"temperature": 0.1}
                            )
                        elif request_idx % 4 == 1:
                            # Google AI Studio
                            item = BatchModelRequestItem(
                                provider=ProviderType.GOOGLE,
                                channel=Channel.AI_STUDIO,
                                invoke_type=InvokeType.GENERATION,
                                model="tamar-google-gemini-flash-lite",
                                contents=f"解释数字 {request_idx} 的含义",
                                custom_id=f"batch-{batch_num}-google-studio-{i}",
                                config={"temperature": 0.2, "maxOutputTokens": 50}
                            )
                        elif request_idx % 4 == 2:
                            # Azure OpenAI
                            item = BatchModelRequestItem(
                                provider=ProviderType.AZURE,
                                invoke_type=InvokeType.CHAT_COMPLETIONS,
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": f"数字 {request_idx} 是奇数还是偶数？"}],
                                custom_id=f"batch-{batch_num}-azure-{i}",
                                config={"temperature": 0.1, "max_tokens": 30}
                            )
                        else:
                            # 故意使用错误的model来触发失败（帮助触发熔断）
                            if batch_num < 2:  # 前两个批次使用错误model
                                item = BatchModelRequestItem(
                                    provider=ProviderType.GOOGLE,
                                    invoke_type=InvokeType.GENERATION,
                                    model="invalid-model-to-trigger-error",
                                    contents=f"测试错误 {request_idx}",
                                    custom_id=f"batch-{batch_num}-error-{i}",
                                )
                            else:
                                # 后续批次使用正确的model
                                item = BatchModelRequestItem(
                                    provider=ProviderType.GOOGLE,
                                    invoke_type=InvokeType.GENERATION,
                                    model="tamar-google-gemini-flash-lite",
                                    contents=f"Hello from batch {batch_num}, item {i}",
                                    custom_id=f"batch-{batch_num}-recovery-{i}",
                                )

                        items.append(item)

                    batch_request = BatchModelRequest(
                        user_context=UserContext(
                            user_id=f"circuit_breaker_test_batch_{batch_num}",
                            org_id="test_org_circuit_breaker",
                            client_type="async_batch_circuit_test"
                        ),
                        items=items
                    )

                    # 执行批量请求
                    print(f"\n   📦 发送批量请求 {batch_num + 1}/{num_batches}...")
                    batch_response = await client.invoke_batch(
                        batch_request,
                        timeout=300000.0,
                        request_id=f"circuit_breaker_test_{batch_num}"
                    )

                    duration = time.time() - start_time
                    batch_times.append(duration)
                    total_batches += 1
                    successful_batches += 1

                    # 统计结果
                    success_count = sum(1 for r in batch_response.responses if not r.error)
                    error_count = sum(1 for r in batch_response.responses if r.error)

                    print(f"   ✅ 批量请求 {batch_num + 1} 完成")
                    print(f"      - 耗时: {duration:.2f} 秒")
                    print(f"      - 成功: {success_count}/{batch_size}")
                    print(f"      - 失败: {error_count}/{batch_size}")

                    # 检查熔断器状态
                    if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                        try:
                            breaker_status = client.get_resilient_metrics()
                            if breaker_status and 'circuit_breaker' in breaker_status:
                                if breaker_status['circuit_breaker']['state'] == 'OPEN':
                                    if not circuit_breaker_opened:
                                        circuit_breaker_opened = True
                                        print(f"   🔻 熔断器已打开！将使用HTTP fallback")
                                    http_fallback_used += 1

                                print(f"      - 熔断器状态: {breaker_status['circuit_breaker']['state']}")
                                print(f"      - 失败计数: {breaker_status['circuit_breaker']['failure_count']}")
                        except Exception as e:
                            print(f"      - 获取熔断器状态失败: {e}")

                except Exception as e:
                    duration = time.time() - start_time
                    batch_times.append(duration)
                    total_batches += 1
                    failed_batches += 1

                    error_type = str(e).split(':')[0] if ':' in str(e) else str(e)[:50]
                    errors[error_type] = errors.get(error_type, 0) + 1

                    print(f"   ❌ 批量请求 {batch_num + 1} 失败: {error_type}")
                    print(f"      - 耗时: {duration:.2f} 秒")

                # 批次之间短暂等待
                if batch_num < num_batches - 1:
                    await asyncio.sleep(0.5)

            # 最终统计
            print(f"\n📊 批量请求测试结果 (熔断器模式):")
            print(f"   总批次数: {total_batches}")
            print(f"   成功批次: {successful_batches} ({successful_batches / total_batches * 100:.1f}%)")
            print(f"   失败批次: {failed_batches} ({failed_batches / total_batches * 100:.1f}%)")

            if batch_times:
                avg_batch_time = sum(batch_times) / len(batch_times)
                print(f"\n   批次耗时统计:")
                print(f"   - 平均: {avg_batch_time:.3f} 秒")
                print(f"   - 最小: {min(batch_times):.3f} 秒")
                print(f"   - 最大: {max(batch_times):.3f} 秒")

            print(f"\n   🔥 熔断器统计:")
            print(f"   - 熔断器是否触发: {'是' if circuit_breaker_opened else '否'}")
            print(f"   - HTTP fallback使用次数: {http_fallback_used}")

            # 获取最终的熔断器状态
            if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                try:
                    final_metrics = client.get_resilient_metrics()
                    if final_metrics and 'circuit_breaker' in final_metrics:
                        print(f"   - 最终状态: {final_metrics['circuit_breaker']['state']}")
                        print(f"   - 总失败次数: {final_metrics['circuit_breaker']['failure_count']}")
                        print(f"   - 失败阈值: {final_metrics['circuit_breaker']['failure_threshold']}")
                        print(f"   - 恢复超时: {final_metrics['circuit_breaker']['recovery_timeout']}秒")
                    else:
                        print(f"   - 无法获取熔断器指标")
                except Exception as e:
                    print(f"   - 获取熔断器指标失败: {e}")

            if errors:
                print(f"\n   错误统计:")
                for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {error_type}: {count} 次")

    except Exception as e:
        print(f"❌ 批量测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 恢复原始环境变量
        for var, value in original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value


async def test_async_concurrent_requests_independent_clients(num_requests: int = 150):
    """测试异步并发请求 - 每个请求使用独立的AsyncTamarModelClient
    
    每个请求都会创建一个新的AsyncTamarModelClient实例，不复用连接，
    这种方式可以测试客户端的连接管理和资源清理能力。
    
    Args:
        num_requests: 要发送的总请求数，默认150个
    """
    print(f"\n🚀 测试异步并发请求 - 独立客户端模式 ({num_requests} 个请求)...")

    # 统计变量
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    request_times: List[float] = []
    errors: Dict[str, int] = {}
    trace_id = "9999999999999999933333999999993333399999"

    # 异步锁
    stats_lock = asyncio.Lock()

    async def make_single_async_request_with_independent_client(request_id: int) -> Tuple[bool, float, str]:
        """使用独立的AsyncTamarModelClient执行单个异步请求
        
        Returns:
            (success, duration, error_msg)
        """
        start_time = time.time()
        try:
            # 每个请求创建独立的客户端实例
            async with AsyncTamarModelClient() as client:
                # 根据请求ID选择不同的provider和model，增加测试多样性
                if request_id % 3 == 0:
                    # Google Vertex AI
                    request = ModelRequest(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.VERTEXAI,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=f"请计算 {request_id % 10} + {(request_id + 1) % 10} 等于多少？",
                        user_context=UserContext(
                            user_id=f"{os.environ.get('INSTANCE_ID', '0')}_independent_{request_id:03d}",
                            org_id="test_org_independent",
                            client_type="async_independent_test"
                        ),
                        config={"temperature": 0.1}
                    )
                elif request_id % 3 == 1:
                    # Google AI Studio
                    request = ModelRequest(
                        provider=ProviderType.GOOGLE,
                        channel=Channel.AI_STUDIO,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=f"什么是人工智能？请简要回答。(请求ID: {request_id})",
                        user_context=UserContext(
                            user_id=f"{os.environ.get('INSTANCE_ID', '0')}_independent_{request_id:03d}",
                            org_id="test_org_independent",
                            client_type="async_independent_test"
                        ),
                        config={"temperature": 0.3, "maxOutputTokens": 100}
                    )
                else:
                    # Azure OpenAI
                    request = ModelRequest(
                        provider=ProviderType.AZURE,
                        invoke_type=InvokeType.CHAT_COMPLETIONS,
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": f"请简单解释什么是云计算？(请求{request_id})"}
                        ],
                        user_context=UserContext(
                            user_id=f"{os.environ.get('INSTANCE_ID', '0')}_independent_{request_id:03d}",
                            org_id="test_org_independent",
                            client_type="async_independent_test"
                        ),
                        config={"temperature": 0.2, "max_tokens": 100}
                    )

                response = await client.invoke(request, timeout=300000.0, request_id=f"{trace_id}_{request_id}")
                duration = time.time() - start_time
                return (True, duration, "")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            return (False, duration, error_msg)

    async def async_independent_worker(request_id: int):
        """独立异步工作协程 - 每个请求使用独立的客户端"""
        nonlocal total_requests, successful_requests, failed_requests

        success, duration, error_msg = await make_single_async_request_with_independent_client(request_id)

        async with stats_lock:
            total_requests += 1
            request_times.append(duration)

            if success:
                successful_requests += 1
            else:
                failed_requests += 1
                # 统计错误类型
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg[:50]
                errors[error_type] = errors.get(error_type, 0) + 1

            # 每20个请求输出一次进度
            if total_requests % 20 == 0:
                print(
                    f"   进度: {total_requests}/{num_requests} (成功: {successful_requests}, 失败: {failed_requests})")

    # 使用独立客户端执行并发请求
    start_time = time.time()

    # 限制并发数，避免创建过多连接
    semaphore = asyncio.Semaphore(30)  # 降低并发数，因为每个请求都要创建新连接

    async def limited_independent_worker(request_id: int):
        async with semaphore:
            await async_independent_worker(request_id)

    # 创建所有任务
    tasks = [limited_independent_worker(i) for i in range(num_requests)]

    # 等待所有任务完成
    await asyncio.gather(*tasks)

    total_duration = time.time() - start_time

    # 计算统计信息
    avg_request_time = sum(request_times) / len(request_times) if request_times else 0
    min_request_time = min(request_times) if request_times else 0
    max_request_time = max(request_times) if request_times else 0

    # 输出结果
    print(f"\n📊 异步并发测试结果 (独立客户端模式):")
    print(f"   总请求数: {total_requests}")
    print(f"   成功请求: {successful_requests} ({successful_requests / total_requests * 100:.1f}%)")
    print(f"   失败请求: {failed_requests} ({failed_requests / total_requests * 100:.1f}%)")
    print(f"   总耗时: {total_duration:.2f} 秒")
    print(f"   平均QPS: {total_requests / total_duration:.2f}")
    print(f"\n   请求耗时统计:")
    print(f"   - 平均: {avg_request_time:.3f} 秒")
    print(f"   - 最小: {min_request_time:.3f} 秒")
    print(f"   - 最大: {max_request_time:.3f} 秒")

    print(f"\n   🔍 测试特点:")
    print(f"   - 每个请求使用独立的AsyncTamarModelClient实例")
    print(f"   - 不复用连接，测试连接管理能力")
    print(f"   - 限制并发数为30个，避免过多连接")
    print(f"   - 使用多种Provider (Google Vertex AI, AI Studio, Azure OpenAI)")

    if errors:
        print(f"\n   错误统计:")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {error_type}: {count} 次")

    return {
        "total": total_requests,
        "successful": successful_requests,
        "failed": failed_requests,
        "duration": total_duration,
        "qps": total_requests / total_duration
    }


async def main():
    """主函数"""
    print("🚀 简化版 Google/Azure 测试")
    print("=" * 50)

    try:
        # 同步测试
        test_google_ai_studio()
        test_google_vertex_ai()
        test_azure_openai()

        # 新增：图像生成测试
        test_google_genai_image_generation()
        test_google_vertex_ai_image_generation()

        # 同步批量测试
        test_sync_batch_requests()

        # 异步流式测试
        await asyncio.wait_for(test_google_streaming(), timeout=60.0)
        await asyncio.wait_for(test_azure_streaming(), timeout=60.0)

        # ：异步图像生成测试
        await asyncio.wait_for(test_google_genai_image_generation_async(), timeout=120.0)
        await asyncio.wait_for(test_google_vertex_ai_image_generation_async(), timeout=120.0)

        # 异步批量测试
        await asyncio.wait_for(test_batch_requests(), timeout=120.0)

        # 新增：图像生成批量测试
        await asyncio.wait_for(test_image_generation_batch(), timeout=180.0)
        #
        # # 同步并发测试
        # test_concurrent_requests(2)  # 测试150个并发请求
        #
        # # 异步并发测试
        # await test_async_concurrent_requests(2)  # 测试50个异步并发请求（复用连接）

        print("\n✅ 测试完成")

    except asyncio.TimeoutError:
        print("\n⏰ 测试超时")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
    finally:
        # 简单优雅的任务清理
        print("📝 清理异步任务...")
        try:
            # 短暂等待让正在完成的任务自然结束
            await asyncio.sleep(0.5)

            # 检查是否还有未完成的任务
            current_task = asyncio.current_task()
            tasks = [task for task in asyncio.all_tasks()
                     if not task.done() and task != current_task]

            if tasks:
                print(f"   发现 {len(tasks)} 个未完成任务，等待自然完成...")
                # 简单等待，不强制取消
                try:
                    await asyncio.wait_for(
                        asyncio.sleep(2.0),  # 给任务2秒时间自然完成
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    pass

            print("   任务清理完成")

        except Exception as e:
            print(f"   ⚠️ 任务清理时出现异常: {e}")

        print("🔚 程序即将退出")


if __name__ == "__main__":
    try:
        # 临时降低 asyncio 日志级别，减少任务取消时的噪音
        asyncio_logger = logging.getLogger('asyncio')
        original_level = asyncio_logger.level
        asyncio_logger.setLevel(logging.ERROR)

        try:
            asyncio.run(main())
        finally:
            # 恢复原始日志级别
            asyncio_logger.setLevel(original_level)

    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
    finally:
        print("🏁 程序已退出")
