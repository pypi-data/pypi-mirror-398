#!/usr/bin/env python3
"""
BytePlus SeeDANCE 1.5 Pro 视频生成测试脚本
直接运行: python tests/byteplus/test_seedance.py
"""

import asyncio
import logging
import os

os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = os.getenv('MODEL_MANAGER_SERVER_ADDRESS', 'localhost:50052')
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = os.getenv('MODEL_MANAGER_SERVER_JWT_SECRET_KEY',
                                                              'model-manager-server-jwt-key')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from tamar_model_client import TamarModelClient, AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.schemas.inputs.byteplus import BytePlusSeeDANCEInput, ContentItem
from tamar_model_client.enums import ProviderType, InvokeType, Channel


def test_seedance_text_to_video():
    """测试 SeeDANCE Text-to-Video（文本生成视频）"""
    print("\n" + "=" * 60)
    print("🎬 测试 SeeDANCE Text-to-Video（文本生成视频）")
    print("=" * 60)

    try:
        client = TamarModelClient()
        # res = client.get_task_status("a5a47b7e-eec2-4ea9-9828-b0d8d3d58117")
        # print(res)
        # return True

        request = ModelRequest(
            provider=ProviderType.DOUBAO,
            channel=Channel.SEEDANCE,
            invoke_type=InvokeType.VIDEO_GENERATION,
            model="doubao-seedance-1-5-pro-251215",
            content=[
                {
                    "type": "text",
                    "text": "A serene landscape with mountains and a lake at sunset, cinematic lighting"
                }
            ],
            duration=5,
            ratio="16:9",
            resolution="720p",
            seed=42,
            enable_async_task=True,
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )
        response = client.invoke(request, timeout=18000.0)
        print(response)
        return True

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            print(f"   响应类型: {type(response)}")
            if response.content:
                print(f"   内容: {str(response.content)[:300]}...")
            if response.raw_response:
                print(f"   原始响应: {str(response.raw_response)[:200]}...")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_seedance_image_to_video():
    """测试 SeeDANCE Image-to-Video（图像生成视频）"""
    print("\n" + "=" * 60)
    print("🎬 测试 SeeDANCE Image-to-Video（图像生成视频）")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            channel=Channel.SEEDANCE,
            invoke_type=InvokeType.VIDEO_GENERATION,
            model="seedance-1.5-pro",
            content=[
                {
                    "type": "text",
                    "text": "Make the character wave their hand and smile"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://storage.googleapis.com/files.tamaredge.top/omnihuman/image%201.png"
                    }
                }
            ],
            duration=8,
            ratio="adaptive",
            resolution="720p",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送 Image-to-Video 请求...")
        print(f"   Prompt: {request.content[0]['text']}")
        print(f"   Image: {request.content[1]['image_url']['url']}")
        response = client.invoke(request, timeout=180.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            if response.usage:
                print(f"   使用信息: {response.usage}")
            if response.raw_response:
                print(f"   原始响应: {str(response.raw_response)[:300]}...")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_seedance_with_dynamic_params():
    """测试使用动态参数方式调用 SeeDANCE"""
    print("\n" + "=" * 60)
    print("🎬 测试 SeeDANCE 动态参数调用")
    print("=" * 60)

    try:
        client = TamarModelClient()

        # 直接使用字典参数
        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            channel=Channel.SEEDANCE,
            invoke_type=InvokeType.VIDEO_GENERATION,
            model="seedance-1.5-pro",
            content=[
                {
                    "type": "text",
                    "text": "A futuristic city at night with neon lights and flying cars"
                }
            ],
            generate_audio=True,
            duration=6,
            ratio="21:9",
            resolution="720p",
            seed=123,
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送动态参数请求...")
        response = client.invoke(request, timeout=180.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_seedance_with_callback():
    """测试带回调的 SeeDANCE 视频生成（异步任务）"""
    print("\n" + "=" * 60)
    print("🎬 测试 SeeDANCE 异步视频生成（带回调）")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            channel=Channel.SEEDANCE,
            invoke_type=InvokeType.VIDEO_GENERATION,
            model="seedance-1.5-pro",
            content=[
                {
                    "type": "text",
                    "text": "A peaceful forest with sunlight filtering through the trees"
                }
            ],
            duration=5,
            ratio="16:9",
            callback_url="https://example.com/webhook/seedance-callback",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送异步 SeeDANCE 视频生成请求...")
        response = client.invoke(request, timeout=30.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功（异步任务已提交）")
            print(f"   响应内容: {response.content[:200] if response.content else 'None'}...")

            # 检查是否返回了 task_id
            task_id = None
            if response.raw_response:
                import json
                try:
                    raw_data = json.loads(response.raw_response) if isinstance(response.raw_response, str) else response.raw_response
                    task_id = raw_data.get('task_id')
                    if task_id:
                        print(f"   📋 任务ID: {task_id}")
                        print(f"   💡 可使用 client.get_task_status('{task_id}') 查询状态")
                except:
                    pass

            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_seedance_advanced_options():
    """测试 SeeDANCE 高级选项"""
    print("\n" + "=" * 60)
    print("🎬 测试 SeeDANCE 高级选项")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            channel=Channel.SEEDANCE,
            invoke_type=InvokeType.VIDEO_GENERATION,
            model="seedance-1.5-pro",
            content=[
                {
                    "type": "text",
                    "text": "A dragon flying over a medieval castle"
                }
            ],
            duration=-1,  # 自动选择时长
            ratio="adaptive",  # 自适应宽高比
            resolution="1080p",
            camerafixed=True,  # 固定相机
            watermark=False,  # 不添加水印
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送高级选项请求...")
        print(f"   分辨率: 1080p")
        print(f"   固定相机: True")
        print(f"   无水印: True")
        response = client.invoke(request, timeout=180.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_seedance_async():
    """测试异步客户端 SeeDANCE 视频生成"""
    print("\n" + "=" * 60)
    print("🎬 测试异步客户端 SeeDANCE 视频生成")
    print("=" * 60)

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.BYTEPLUS,
                channel=Channel.SEEDANCE,
                invoke_type=InvokeType.VIDEO_GENERATION,
                model="seedance-1.5-pro",
                content=[
                    {
                        "type": "text",
                        "text": "A beautiful sunset over the ocean with waves crashing"
                    }
                ],
                duration=5,
                ratio="16:9",
                resolution="720p",
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                )
            )

            print("📤 发送异步 SeeDANCE 视频生成请求...")
            response = await client.invoke(request, timeout=180.0)

            if response.error:
                print(f"❌ 失败: {response.error}")
                return False
            else:
                print(f"✅ 成功")
                return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_task_status():
    """测试查询任务状态"""
    print("\n" + "=" * 60)
    print("🔍 测试查询 SeeDANCE 任务状态")
    print("=" * 60)

    try:
        client = TamarModelClient()

        # 替换为实际的 task_id
        task_id = "your-task-id-here"

        print(f"📤 查询任务状态: {task_id}")
        status_response = client.get_task_status(task_id)

        print(f"✅ 查询成功")
        print(f"   任务状态: {status_response.status}")
        print(f"   Provider: {status_response.provider}")
        print(f"   创建时间: {status_response.created_at}")
        if status_response.completed_at:
            print(f"   完成时间: {status_response.completed_at}")
        if status_response.result_data:
            print(f"   结果数据: {status_response.result_data}")
        if status_response.error_message:
            print(f"   错误信息: {status_response.error_message}")

        return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "🎬" * 30)
    print("BytePlus SeeDANCE 1.5 Pro 视频生成测试套件")
    print("🎬" * 30)

    results = []

    # 同步测试
    results.append(("Text-to-Video 基础测试", test_seedance_text_to_video()))
    # results.append(("Image-to-Video 测试", test_seedance_image_to_video()))
    # results.append(("动态参数调用测试", test_seedance_with_dynamic_params()))
    # results.append(("异步视频生成（带回调）", test_seedance_with_callback()))
    # results.append(("高级选项测试", test_seedance_advanced_options()))
    # results.append(("查询任务状态", test_get_task_status()))

    # 异步测试
    # results.append(("异步客户端视频生成", await test_seedance_async()))

    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {success_count}/{total_count} 通过")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
