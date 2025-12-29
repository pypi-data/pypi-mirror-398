#!/usr/bin/env python3
"""
熔断器测试脚本
专门用于测试熔断器和HTTP fallback功能
"""

import asyncio
import logging
import os
import sys
import time
from typing import List, Dict, Tuple

# 配置测试脚本专用的日志
test_logger = logging.getLogger('test_circuit_breaker')
test_logger.setLevel(logging.INFO)
test_logger.propagate = False

# 创建测试脚本专用的handler
test_handler = logging.StreamHandler()
test_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
test_logger.addHandler(test_handler)

logger = test_logger

# 导入客户端模块
try:
    from tamar_model_client import AsyncTamarModelClient
    from tamar_model_client.schemas import ModelRequest, UserContext
    from tamar_model_client.enums import ProviderType, InvokeType
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)


async def test_circuit_breaker_with_single_requests(num_requests: int = 10):
    """
    测试熔断器功能 - 使用单个请求触发熔断

    Args:
        num_requests: 要发送的请求数，默认10个
    """
    print(f"\n🔥 测试熔断器功能 - 单请求模式 ({num_requests} 个请求)...")

    # 保存原始环境变量
    original_env = {}
    env_vars = ['MODEL_CLIENT_RESILIENT_ENABLED', 'MODEL_CLIENT_HTTP_FALLBACK_URL',
                'MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD', 'MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT',
                'MODEL_MANAGER_SERVER_ADDRESS', 'MODEL_MANAGER_SERVER_GRPC_USE_TLS']
    for var in env_vars:
        original_env[var] = os.environ.get(var)

    # 设置环境变量以启用熔断器和HTTP fallback
    os.environ['MODEL_CLIENT_RESILIENT_ENABLED'] = 'true'
    os.environ['MODEL_CLIENT_HTTP_FALLBACK_URL'] = 'http://localhost:8000'  # 假设HTTP服务在8000端口
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD'] = '3'  # 3次失败后触发熔断
    os.environ['MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT'] = '30'  # 熔断器30秒后恢复

    # 使用一个不存在的服务器地址来触发连接错误
    os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = 'localhost:99999'  # 无效端口
    os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = 'false'

    # 调试：打印环境变量确认设置成功
    print(f"   环境变量设置:")
    print(f"   - MODEL_CLIENT_RESILIENT_ENABLED: {os.environ.get('MODEL_CLIENT_RESILIENT_ENABLED')}")
    print(f"   - MODEL_CLIENT_HTTP_FALLBACK_URL: {os.environ.get('MODEL_CLIENT_HTTP_FALLBACK_URL')}")
    print(f"   - 熔断阈值: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD')} 次失败")
    print(f"   - 熔断恢复时间: {os.environ.get('MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT')} 秒")
    print(f"   - gRPC服务器: {os.environ.get('MODEL_MANAGER_SERVER_ADDRESS')} (故意使用无效地址)")

    # 统计变量
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    http_fallback_requests = 0
    circuit_breaker_opened = False
    request_times: List[float] = []
    errors: Dict[str, int] = {}

    try:
        # 创建一个共享的异步客户端（启用熔断器）
        async with AsyncTamarModelClient() as client:
            print(f"\n   熔断器初始配置:")
            print(f"   - 启用状态: {getattr(client, 'resilient_enabled', False)}")
            print(f"   - HTTP Fallback URL: {getattr(client, 'http_fallback_url', 'None')}")

            # 获取初始熔断器状态
            if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                try:
                    metrics = client.get_resilient_metrics()
                    if metrics and 'circuit_breaker' in metrics:
                        print(f"   - 初始状态: {metrics['circuit_breaker']['state']}")
                        print(f"   - 失败阈值: {metrics['circuit_breaker']['failure_threshold']}")
                        print(f"   - 恢复超时: {metrics['circuit_breaker']['recovery_timeout']}秒")
                except Exception as e:
                    print(f"   - 获取初始状态失败: {e}")

            print(f"\n   开始发送请求...")

            for i in range(num_requests):
                start_time = time.time()
                request_num = i + 1

                try:
                    # 构建请求
                    request = ModelRequest(
                        provider=ProviderType.GOOGLE,
                        invoke_type=InvokeType.GENERATION,
                        model="tamar-google-gemini-flash-lite",
                        contents=f"测试请求 {request_num}: 1+1等于几？",
                        user_context=UserContext(
                            user_id=f"circuit_test_user_{i}",
                            org_id="circuit_test_org",
                            client_type="circuit_breaker_test"
                        ),
                        config={"temperature": 0.1, "maxOutputTokens": 10}
                    )

                    print(f"\n   📤 请求 {request_num}/{num_requests}...")

                    # 发送请求
                    response = await client.invoke(
                        request,
                        timeout=5000,  # 5秒超时
                        request_id=f"circuit_test_{i}"
                    )

                    duration = time.time() - start_time
                    request_times.append(duration)
                    total_requests += 1
                    successful_requests += 1

                    # 如果成功了，检查是否是通过HTTP fallback
                    if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                        metrics = client.get_resilient_metrics()
                        if metrics and metrics['circuit_breaker']['state'] == 'open':
                            http_fallback_requests += 1
                            print(f"   ✅ 请求 {request_num} 成功 (通过HTTP fallback) - 耗时: {duration:.2f}秒")
                        else:
                            print(f"   ✅ 请求 {request_num} 成功 (gRPC) - 耗时: {duration:.2f}秒")
                    else:
                        print(f"   ✅ 请求 {request_num} 成功 - 耗时: {duration:.2f}秒")

                    # 打印响应内容的前100个字符
                    if response.content:
                        print(f"      响应: {response.content[:100]}...")

                except Exception as e:
                    duration = time.time() - start_time
                    request_times.append(duration)
                    total_requests += 1
                    failed_requests += 1

                    error_type = type(e).__name__
                    error_msg = str(e)[:100]
                    errors[error_type] = errors.get(error_type, 0) + 1

                    print(f"   ❌ 请求 {request_num} 失败 - {error_type}: {error_msg}")
                    print(f"      耗时: {duration:.2f}秒")

                # 检查熔断器状态
                if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                    try:
                        metrics = client.get_resilient_metrics()
                        if metrics and 'circuit_breaker' in metrics:
                            cb_state = metrics['circuit_breaker']['state']
                            cb_failures = metrics['circuit_breaker']['failure_count']

                            print(f"      熔断器状态: {cb_state}, 失败计数: {cb_failures}")

                            if cb_state == 'open' and not circuit_breaker_opened:
                                circuit_breaker_opened = True
                                print(f"   🔻 熔断器已打开！后续请求将使用HTTP fallback")
                    except Exception as e:
                        print(f"      获取熔断器状态失败: {e}")

                # 请求之间短暂等待
                if i < num_requests - 1:
                    await asyncio.sleep(0.5)

            # 最终统计
            print(f"\n📊 熔断器测试结果:")
            print(f"   总请求数: {total_requests}")
            print(f"   成功请求: {successful_requests} ({successful_requests / total_requests * 100:.1f}%)")
            print(f"   失败请求: {failed_requests} ({failed_requests / total_requests * 100:.1f}%)")

            if request_times:
                avg_time = sum(request_times) / len(request_times)
                print(f"\n   请求耗时统计:")
                print(f"   - 平均: {avg_time:.3f} 秒")
                print(f"   - 最小: {min(request_times):.3f} 秒")
                print(f"   - 最大: {max(request_times):.3f} 秒")

            print(f"\n   🔥 熔断器统计:")
            print(f"   - 熔断器是否触发: {'是' if circuit_breaker_opened else '否'}")
            print(f"   - HTTP fallback请求数: {http_fallback_requests}")

            # 获取最终的熔断器状态
            if hasattr(client, 'resilient_enabled') and client.resilient_enabled:
                try:
                    final_metrics = client.get_resilient_metrics()
                    if final_metrics and 'circuit_breaker' in final_metrics:
                        print(f"   - 最终状态: {final_metrics['circuit_breaker']['state']}")
                        print(f"   - 总失败次数: {final_metrics['circuit_breaker']['failure_count']}")
                        print(f"   - 失败阈值: {final_metrics['circuit_breaker']['failure_threshold']}")
                        print(f"   - 恢复超时: {final_metrics['circuit_breaker']['recovery_timeout']}秒")
                except Exception as e:
                    print(f"   - 获取最终状态失败: {e}")

            if errors:
                print(f"\n   错误类型统计:")
                for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {error_type}: {count} 次")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 恢复原始环境变量
        print(f"\n   恢复环境变量...")
        for var, value in original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value


async def test_circuit_breaker_recovery():
    """测试熔断器恢复功能"""
    print(f"\n🔄 测试熔断器恢复功能...")

    # 这里可以先触发熔断，然后恢复正常服务，观察熔断器是否能自动恢复
    # 实现略...
    pass


async def main():
    """主函数"""
    print("🚀 熔断器功能测试")
    print("=" * 50)

    try:
        # 测试熔断器触发
        await test_circuit_breaker_with_single_requests(10)

        # 可选：测试熔断器恢复
        # await test_circuit_breaker_recovery()

        print("\n✅ 测试完成")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
    finally:
        print("🏁 程序已退出")