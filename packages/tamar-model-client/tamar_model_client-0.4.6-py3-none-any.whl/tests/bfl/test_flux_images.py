#!/usr/bin/env python3
"""
BFL Flux 测试脚本
直接运行: python tests/bfl/test_flux_images.py
"""

import asyncio
import logging
import os

# 配置环境变量
os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = os.getenv('MODEL_MANAGER_SERVER_ADDRESS', 'localhost:50052')
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = os.getenv('MODEL_MANAGER_SERVER_JWT_SECRET_KEY',
                                                              'model-manager-server-jwt-key')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from tamar_model_client import TamarModelClient, AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext, TamarFileIdInput
from tamar_model_client.enums import ProviderType, InvokeType
from tamar_model_client.schemas.inputs.bfl import BFLInput


def test_flux_2_pro():
    """测试 FLUX.2 [PRO] 基本文本生成图像"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL FLUX.2 [PRO] (Text-to-Image)")
    print("=" * 60)

    try:
        client = TamarModelClient()
        # res = client.batch_get_task_status(["896f6ec7-d324-4d30-a570-709ea767ad2e"])
        # print(res.model_dump_json())
        # return True

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_GENERATION,
            model="flux.2-pro",
            prompt="A majestic lion standing on a cliff at sunset, photorealistic, 8k quality",
            width=3840,
            height=2160,
            safety_tolerance="2",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)
        print(response)
        return True

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            print(f"   响应类型: {type(response)}")
            if response.content:
                print(f"   内容: {response.content}")
            if response.raw_response:
                import json
                data = json.loads(response.raw_response)
                print(f"   Task ID: {data.get('task_id')}")
                print(f"   Operation ID: {data.get('operation_id')}")
                print(f"   Status: {data.get('status')}")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_flux_2_flex():
    """测试 FLUX.2 [FLEX] 带引导参数和步骤数"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL FLUX.2 [FLEX] (带引导参数)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_GENERATION,
            model="flux.2-flex",
            prompt="A serene Japanese garden with cherry blossoms, traditional architecture, peaceful atmosphere",
            width=1024,
            height=1024,
            guidance=3.5,
            steps=40,
            safety_tolerance="2",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            if response.raw_response:
                import json
                data = json.loads(response.raw_response)
                print(f"   Task ID: {data.get('task_id')}")
                print(f"   使用 guidance={3.5}, steps={40}")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_flux_kontext_pro():
    """测试 FLUX KONTEXT PRO 多图参考"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL FLUX KONTEXT PRO (多图参考)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        # 使用 BFLInput 创建多图参考请求
        request_input = BFLInput(
            prompt="A fantasy landscape combining elements from all reference images",
            input_image="https://example.com/image1.jpg",
            input_image_2="https://example.com/image2.jpg",
            input_image_3="https://example.com/image3.jpg",
            aspect_ratio="16:9",
            safety_tolerance="2",
            model="flux-kontext-pro"
        )

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_GENERATION,
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            **request_input.model_dump()
        )

        response = client.invoke(request, timeout=60000.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            print(f"   使用了 3 张参考图像")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_flux_1_1_pro_with_image_prompt():
    """测试 FLUX 1.1 [PRO] 带图像提示词"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL FLUX 1.1 [PRO] (图像提示词)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_GENERATION,
            model="flux.1.1-pro",
            prompt="Create an image in the style of the reference",
            image_prompt="https://example.com/style-reference.jpg",
            width=1024,
            height=768,
            safety_tolerance="2",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            print(f"   使用图像提示词: image_prompt")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_flux_image_edit():
    """测试图像编辑"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL Flux (图像编辑)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_EDIT_GENERATION,
            model="flux.2-pro",
            prompt="Add a rainbow in the sky, enhance colors",
            input_image="https://example.com/original-image.jpg",
            width=1024,
            height=768,
            safety_tolerance="2",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)

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
        return False


def test_flux_with_tamar_file_id():
    """测试使用 Tamar File ID"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL Flux (Tamar File ID)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        # 使用 BFLInput 创建带 TamarFileIdInput 的请求
        request_input = BFLInput(
            prompt="Transform this image into a painting style",
            input_image=TamarFileIdInput(file_id="image_file_123456_example"),
            width=1024,
            height=1024,
            safety_tolerance="2",
            model="flux.2-pro"
        )

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_EDIT_GENERATION,
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            ),
            **request_input.model_dump()
        )

        response = client.invoke(request, timeout=60000.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_flux_with_webhook():
    """测试 Webhook 回调"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL Flux (Webhook 回调)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.BFL,
            invoke_type=InvokeType.IMAGE_GENERATION,
            model="flux.2-pro",
            prompt="A futuristic cityscape at night",
            width=1024,
            height=768,
            webhook_url="https://your-server.com/webhook",
            webhook_secret="your-secret-key",
            safety_tolerance="2",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="test_client"
            )
        )

        response = client.invoke(request, timeout=60000.0)

        if response.error:
            print(f"❌ 失败: {response.error}")
            return False
        else:
            print(f"✅ 成功")
            print(f"   Webhook URL: https://your-server.com/webhook")
            return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


async def test_flux_async():
    """测试异步图像生成"""
    print("\n" + "=" * 60)
    print("🎨 测试异步 BFL Flux")
    print("=" * 60)

    try:
        async with AsyncTamarModelClient() as client:
            request = ModelRequest(
                provider=ProviderType.BFL,
                invoke_type=InvokeType.IMAGE_GENERATION,
                model="flux.2-pro",
                prompt="A beautiful mountain landscape with a lake reflection",
                width=1024,
                height=768,
                safety_tolerance="2",
                user_context=UserContext(
                    user_id="test_user",
                    org_id="test_org",
                    client_type="test_client"
                )
            )

            response = await client.invoke(request, timeout=60000.0)

            if response.error:
                print(f"❌ 失败: {response.error}")
                return False
            else:
                print(f"✅ 成功")
                return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_flux_check_status():
    """测试查询任务状态"""
    print("\n" + "=" * 60)
    print("🎨 测试 BFL Flux (查询状态)")
    print("=" * 60)

    try:
        client = TamarModelClient()

        # 假设已经有一个任务 ID（替换为实际的任务ID）
        task_id = "your-task-id-here"

        response = client.get_task_status(task_id)
        print(f"任务状态: {response}")

        return True

    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


async def main():
    """主函数"""
    print("\n" + "🚀" * 30)
    print("BFL Flux 测试套件")
    print("🚀" * 30)

    results = []

    # 同步测试
    results.append(("FLUX.2 [PRO]", test_flux_2_pro()))
    # results.append(("FLUX.2 [FLEX]", test_flux_2_flex()))
    # results.append(("FLUX KONTEXT PRO", test_flux_kontext_pro()))
    # results.append(("FLUX 1.1 [PRO]", test_flux_1_1_pro_with_image_prompt()))
    # results.append(("图像编辑", test_flux_image_edit()))
    # results.append(("Tamar File ID", test_flux_with_tamar_file_id()))
    # results.append(("Webhook 回调", test_flux_with_webhook()))

    # 异步测试
    # results.append(("异步调用", await test_flux_async()))

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
