"""
测试批量查询异步任务状态功能

演示如何使用 batch_get_task_status 方法查询多个任务的状态
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 同步客户端示例
def test_sync_batch_get_task_status():
    """测试同步客户端批量查询任务状态"""
    from tamar_model_client import TamarModelClient

    # 示例任务ID列表
    task_ids = [
        "task_123456",
        "task_789012",
        "task_345678"
    ]

    with TamarModelClient() as client:
        try:
            # 批量查询任务状态
            response = client.batch_get_task_status(task_ids, timeout=30.0)

            print(f"\n✅ 批量查询成功，共查询 {len(response.tasks)} 个任务")

            # 遍历每个任务的状态
            for task in response.tasks:
                print(f"\n任务ID: {task.task_id}")
                print(f"  状态: {task.status}")
                print(f"  Provider: {task.provider}")
                print(f"  Model: {task.model}")
                print(f"  创建时间: {task.created_at}")

                if task.status == "completed":
                    print(f"  完成时间: {task.completed_at}")
                    print(f"  结果数据: {task.result_data}")
                elif task.status == "failed":
                    print(f"  错误信息: {task.error_message}")

        except Exception as e:
            print(f"❌ 批量查询失败: {e}")


# 异步客户端示例
async def test_async_batch_get_task_status():
    """测试异步客户端批量查询任务状态"""
    from tamar_model_client import AsyncTamarModelClient

    # 示例任务ID列表
    task_ids = [
        "task_123456",
        "task_789012",
        "task_345678"
    ]

    async with AsyncTamarModelClient() as client:
        try:
            # 批量查询任务状态
            response = await client.batch_get_task_status(task_ids, timeout=30.0)

            print(f"\n✅ 批量查询成功，共查询 {len(response.tasks)} 个任务")

            # 统计各状态的任务数量
            status_counts = {
                "processing": 0,
                "completed": 0,
                "failed": 0
            }

            for task in response.tasks:
                status_counts[task.status] = status_counts.get(task.status, 0) + 1

                print(f"\n任务ID: {task.task_id}")
                print(f"  状态: {task.status}")
                print(f"  Provider: {task.provider}")
                print(f"  Model: {task.model}")

                if task.status == "completed" and task.result_data:
                    print(f"  GCS URI: {task.result_data.get('gcs_uri', 'N/A')}")

            print(f"\n📊 状态统计:")
            print(f"  处理中: {status_counts['processing']}")
            print(f"  已完成: {status_counts['completed']}")
            print(f"  失败: {status_counts['failed']}")

        except Exception as e:
            print(f"❌ 批量查询失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试批量查询异步任务状态功能")
    print("=" * 60)

    # 测试同步客户端
    print("\n【同步客户端测试】")
    test_sync_batch_get_task_status()

    # 测试异步客户端
    print("\n\n【异步客户端测试】")
    import asyncio
    asyncio.run(test_async_batch_get_task_status())
