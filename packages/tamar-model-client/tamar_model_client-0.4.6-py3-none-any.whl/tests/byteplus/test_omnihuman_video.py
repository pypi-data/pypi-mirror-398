#!/usr/bin/env python3
"""
BytePlus OmniHuman 1.5 视频生成测试脚本
直接运行: python tests/byteplus/test_omnihuman_video.py
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
from tamar_model_client.enums import ProviderType, InvokeType


def test_omnihuman_video_basic():
    """测试基础 OmniHuman 视频生成"""
    print("\n" + "=" * 60)
    print("🎭 测试 BytePlus OmniHuman 基础视频生成")
    print("=" * 60)

    try:
        client = TamarModelClient()
        # res = client.get_task_status("6e7de53e-35ec-42f4-a0fc-630065812a02")
        # print(res)
        # return True

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            invoke_type=InvokeType.VIDEO_GENERATION,
            image_url="https://storage.googleapis.com/files.tamaredge.top/omnihuman/image%201.png",
            audio_url="https://storage.googleapis.com/files.tamaredge.top/omnihuman/Audio%201.MP3",
            prompt="The man walks forward first, then stops and puts his hands on his hips while speaking. Then, he turns around to look at the explosion behind him, showing his back. The clothes on his back have been blown to pieces.",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送 OmniHuman 视频生成请求...")
        response = client.invoke(request, timeout=120.0)
        print(response)

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


def test_omnihuman_video_with_mask():
    """测试带掩码的 OmniHuman 视频生成"""
    print("\n" + "=" * 60)
    print("🎭 测试 BytePlus OmniHuman 带掩码视频生成")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            invoke_type=InvokeType.OMNIHUMAN_VIDEO,
            image_url="https://example.com/portrait.jpg",
            audio_url="https://example.com/speech.mp3",
            mask_url="https://example.com/mask.png",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送带掩码的 OmniHuman 视频生成请求...")
        response = client.invoke(request, timeout=120.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            if response.usage:
                print(f"   使用信息: {response.usage}")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_omnihuman_video_with_callback():
    """测试带回调的 OmniHuman 视频生成（异步任务）"""
    print("\n" + "=" * 60)
    print("🎭 测试 BytePlus OmniHuman 异步视频生成（带回调）")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BYTEPLUS,
            invoke_type=InvokeType.OMNIHUMAN_VIDEO,
            image_url="https://example.com/portrait.jpg",
            audio_url="https://example.com/speech.mp3",
            callback_url="https://example.com/webhook/omnihuman-callback",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        print("📤 发送异步 OmniHuman 视频生成请求...")
        response = client.invoke(request, timeout=30.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功（异步任务已提交）")
            print(f"   响应内容: {response.content[:200] if response.content else 'None'}...")

            # 检查是否返回了 task_id
            task_id = None
            if response.raw_response and isinstance(response.raw_response, dict):
                task_id = response.raw_response.get('task_id')
                if task_id:
                    print(f"   📋 任务ID: {task_id}")
                    print(f"   💡 可使用 client.get_task_status('{task_id}') 查询状态")

                    # 演示查询任务状态
                    print("\n   🔍 查询任务状态...")
                    try:
                        status_response = client.get_task_status(task_id)
                        print(f"   ✅ 任务状态: {status_response.status}")
                        print(f"   - Provider: {status_response.provider}")
                        print(f"   - 创建时间: {status_response.created_at}")
                        if status_response.completed_at:
                            print(f"   - 完成时间: {status_response.completed_at}")
                        if status_response.result_data:
                            print(f"   - 结果数据: {status_response.result_data}")
                        if status_response.error_message:
                            print(f"   - 错误信息: {status_response.error_message}")
                    except Exception as status_error:
                        print(f"   ⚠️ 查询任务状态失败: {str(status_error)}")

            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_omnihuman_video_async():
    """测试异步客户端 OmniHuman 视频生成"""
    print("\n" + "=" * 60)
    print("🎭 测试异步客户端 OmniHuman 视频生成")
    print("=" * 60)

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.BYTEPLUS,
                invoke_type=InvokeType.OMNIHUMAN_VIDEO,
                image_url="https://example.com/portrait.jpg",
                audio_url="https://example.com/speech.mp3",
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                )
            )

            print("📤 发送异步 OmniHuman 视频生成请求...")
            response = await client.invoke(request, timeout=120.0)

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
    print("🔍 测试查询 OmniHuman 任务状态")
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
    print("\n" + "🎭" * 30)
    print("BytePlus OmniHuman 1.5 视频生成测试套件")
    print("🎭" * 30)

    results = []

    # 同步测试
    results.append(("基础视频生成", test_omnihuman_video_basic()))
    # results.append(("带掩码视频生成", test_omnihuman_video_with_mask()))
    # results.append(("异步视频生成（带回调）", test_omnihuman_video_with_callback()))
    # results.append(("查询任务状态", test_get_task_status()))

    # 异步测试
    # results.append(("异步客户端视频生成", await test_omnihuman_video_async()))

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
