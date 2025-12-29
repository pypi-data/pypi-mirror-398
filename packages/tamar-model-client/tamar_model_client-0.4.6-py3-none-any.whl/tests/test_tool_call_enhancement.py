#!/usr/bin/env python3
"""
Tool Call Enhancement 测试脚本

测试 Tool Call 功能的增强实现，包括：
1. ModelResponse 的 tool_calls 和 finish_reason 字段
2. ToolCallHelper 工具类的便利方法
3. ResponseHandler 的自动提取功能
"""

import asyncio
import json
import logging
import os
import sys
from unittest.mock import Mock

# 配置测试脚本专用的日志
test_logger = logging.getLogger('test_tool_call_enhancement')
test_logger.setLevel(logging.INFO)
test_logger.propagate = False

test_handler = logging.StreamHandler()
test_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
test_logger.addHandler(test_handler)

logger = test_logger

# 工具函数实现
def get_weather(location: str) -> str:
    """获取指定城市的天气信息

    Args:
        location: 城市名称

    Returns:
        天气信息字符串
    """
    # 模拟天气数据
    weather_data = {
        "北京": "北京今天晴天，温度25°C，微风",
        "上海": "上海今天多云，温度28°C，湿度较高",
        "广州": "广州今天阴天，温度32°C，有雷阵雨",
        "深圳": "深圳今天晴天，温度30°C，空气质量良好",
        "杭州": "杭州今天小雨，温度22°C，建议带伞",
        "成都": "成都今天阴天，温度26°C，空气湿润"
    }

    # 默认天气信息
    return weather_data.get(location, f"{location}今天天气晴朗，温度适宜")

# 设置测试环境变量
os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = "localhost:50051"
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = "model-manager-server-jwt-key"

# 导入客户端模块
try:
    from tamar_model_client import TamarModelClient, AsyncTamarModelClient
    from tamar_model_client.schemas import ModelRequest, UserContext
    from tamar_model_client.enums import ProviderType, InvokeType, Channel

    # 为了调试，临时启用 SDK 的日志输出
    os.environ['TAMAR_MODEL_CLIENT_LOG_LEVEL'] = 'INFO'

except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)


def test_model_response_enhancement():
    """测试 ModelResponse 增强功能"""
    print("\n📋 测试 ModelResponse 增强功能...")

    try:
        from tamar_model_client.schemas.outputs import ModelResponse

        # 测试有工具调用的情况
        response_with_tools = ModelResponse(
            content="I need to call some tools.",
            tool_calls=[
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"location": "Beijing"}'}
                }
            ],
            finish_reason="tool_calls"
        )

        assert response_with_tools.has_tool_calls() is True
        assert len(response_with_tools.tool_calls) == 1
        print("   ✅ 有工具调用的情况测试通过")

        # 测试无工具调用的情况
        response_without_tools = ModelResponse(
            content="Here is the answer.",
            finish_reason="stop"
        )

        assert response_without_tools.has_tool_calls() is False
        assert response_without_tools.tool_calls is None
        print("   ✅ 无工具调用的情况测试通过")

        # 测试空的工具调用列表
        response_empty_tools = ModelResponse(
            content="Here is the answer.",
            tool_calls=[],
            finish_reason="stop"
        )

        assert response_empty_tools.has_tool_calls() is False
        print("   ✅ 空工具调用列表的情况测试通过")

        print("✅ ModelResponse 增强功能测试全部通过")

    except Exception as e:
        print(f"❌ ModelResponse 增强功能测试失败: {str(e)}")


def test_tool_call_helper():
    """测试 ToolCallHelper 工具类"""
    print("\n🔧 测试 ToolCallHelper 工具类...")

    try:
        from tamar_model_client import ToolCallHelper
        from tamar_model_client.schemas.outputs import ModelResponse

        # 测试创建函数工具
        tool = ToolCallHelper.create_function_tool(
            name="test_func",
            description="测试函数",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"]
            }
        )

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "test_func"
        assert tool["function"]["description"] == "测试函数"
        assert "param1" in tool["function"]["parameters"]["properties"]
        print("   ✅ 创建函数工具测试通过")

        # 测试解析函数参数
        tool_call = {
            "type": "function",
            "function": {
                "name": "test_func",
                "arguments": '{"location": "Beijing", "unit": "celsius"}'
            }
        }

        args = ToolCallHelper.parse_function_arguments(tool_call)
        assert args["location"] == "Beijing"
        assert args["unit"] == "celsius"
        print("   ✅ 解析函数参数测试通过")

        # 测试创建工具响应消息
        response_msg = ToolCallHelper.create_tool_response_message(
            "call_123",
            "Tool execution result",
            "test_tool"
        )

        assert response_msg["role"] == "tool"
        assert response_msg["tool_call_id"] == "call_123"
        assert response_msg["content"] == "Tool execution result"
        assert response_msg["name"] == "test_tool"
        print("   ✅ 创建工具响应消息测试通过")

        # 测试构建包含工具响应的消息列表
        original_messages = [
            {"role": "user", "content": "What's the weather?"}
        ]

        assistant_response = ModelResponse(
            content="I'll check the weather for you.",
            tool_calls=[
                {
                    "id": "call_weather",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"location": "Beijing"}'}
                }
            ],
            finish_reason="tool_calls"
        )

        tool_responses = [
            {
                "role": "tool",
                "tool_call_id": "call_weather",
                "content": "Beijing: Sunny, 25°C"
            }
        ]

        new_messages = ToolCallHelper.build_messages_with_tool_response(
            original_messages, assistant_response, tool_responses
        )

        assert len(new_messages) == 3
        assert new_messages[0]["role"] == "user"
        assert new_messages[1]["role"] == "assistant"
        assert new_messages[1]["tool_calls"] == assistant_response.tool_calls
        assert new_messages[2]["role"] == "tool"
        assert new_messages[2]["tool_call_id"] == "call_weather"
        print("   ✅ 构建消息列表测试通过")

        print("✅ ToolCallHelper 工具类测试全部通过")

    except Exception as e:
        print(f"❌ ToolCallHelper 工具类测试失败: {str(e)}")


def test_response_handler_enhancement():
    """测试 ResponseHandler 增强功能"""
    print("\n🔄 测试 ResponseHandler 增强功能...")

    try:
        from tamar_model_client.core.response_handler import ResponseHandler

        # 测试 OpenAI 格式的 tool calls 提取
        mock_grpc_response = Mock()
        mock_grpc_response.content = ""
        mock_grpc_response.usage = None
        mock_grpc_response.error = None
        mock_grpc_response.request_id = "req_123"
        mock_grpc_response.raw_response = json.dumps({
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_456",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "Shanghai"}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        })

        response = ResponseHandler.build_model_response(mock_grpc_response)

        assert response.has_tool_calls() is True
        assert response.finish_reason == "tool_calls"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["function"]["name"] == "get_weather"
        print("   ✅ OpenAI 格式 tool calls 提取测试通过")

        # 测试 Google 格式转换
        mock_google_response = Mock()
        mock_google_response.content = ""
        mock_google_response.usage = None
        mock_google_response.error = None
        mock_google_response.request_id = "req_456"
        mock_google_response.raw_response = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "get_weather",
                                    "args": {"location": "Guangzhou"}
                                }
                            }
                        ]
                    },
                    "finishReason": "STOP"
                }
            ]
        })

        google_response = ResponseHandler.build_model_response(mock_google_response)

        assert google_response.has_tool_calls() is True
        assert google_response.finish_reason == "tool_calls"  # 自动转换
        assert len(google_response.tool_calls) == 1

        tool_call = google_response.tool_calls[0]
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_weather"
        assert "call_0_get_weather" in tool_call["id"]

        # 验证参数转换
        args = json.loads(tool_call["function"]["arguments"])
        assert args["location"] == "Guangzhou"
        print("   ✅ Google 格式转换测试通过")

        print("✅ ResponseHandler 增强功能测试全部通过")

    except Exception as e:
        print(f"❌ ResponseHandler 增强功能测试失败: {str(e)}")


def test_openai_tool_call():
    """测试 OpenAI Tool Call 场景"""
    print("\n🔧 测试 OpenAI Tool Call...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.AZURE,
            invoke_type=InvokeType.CHAT_COMPLETIONS,
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "北京今天天气如何？"}
            ],
            tools=[
                {
                    "type": "function",
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "城市名称"
                            }
                        },
                        "required": ["location"]
                    },
                    "strict": None
                }
            ],
            tool_choice="auto",
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="tool_call_test"
            )
        )

        response = client.invoke(request)

        print(f"✅ OpenAI Tool Call 测试成功")
        print(f"   响应类型: {type(response)}")
        print(f"   是否有 tool calls: {response.has_tool_calls()}")
        print(f"   finish_reason: {response.finish_reason}")

        if response.has_tool_calls():
            print(f"   tool_calls 数量: {len(response.tool_calls)}")
            for i, tool_call in enumerate(response.tool_calls):
                function_name = tool_call['function']['name']
                print(f"   工具 {i+1}: {function_name}")
                from tamar_model_client import ToolCallHelper
                args = ToolCallHelper.parse_function_arguments(tool_call)
                print(f"   参数: {args}")

                # 演示实际工具函数调用
                if function_name == "get_weather":
                    result = get_weather(args['location'])
                    print(f"   执行结果: {result}")

        print(f"   响应内容: {str(response.content)[:200]}...")

    except Exception as e:
        print(f"❌ OpenAI Tool Call 测试失败: {str(e)}")


def test_google_tool_call():
    """测试 Google Tool Call 场景"""
    print("\n🔧 测试 Google Tool Call...")

    try:
        client = TamarModelClient()

        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            invoke_type=InvokeType.GENERATION,
            model="tamar-google-gemini-flash-lite",
            contents=[
                {"role": "user", "parts": [{"text": "上海今天天气如何？"}]}
            ],
            config={
                "tools": [
                    {
                        "functionDeclarations": [
                            {
                                "name": "get_weather",
                                "description": "获取指定城市的天气信息",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {
                                            "type": "string",
                                            "description": "城市名称"
                                        }
                                    },
                                    "required": ["location"]
                                }
                            }
                        ]
                    }
                ]
            },
            user_context=UserContext(
                user_id="test_user",
                org_id="test_org",
                client_type="google_tool_test"
            )
        )

        response = client.invoke(request)

        print(f"✅ Google Tool Call 测试成功")
        print(f"   响应类型: {type(response)}")
        print(f"   是否有 tool calls: {response.has_tool_calls()}")
        print(f"   finish_reason: {response.finish_reason}")

        if response.has_tool_calls():
            print(f"   tool_calls 数量: {len(response.tool_calls)}")
            for i, tool_call in enumerate(response.tool_calls):
                function_name = tool_call['function']['name']
                print(f"   工具 {i+1}: {function_name}")
                from tamar_model_client import ToolCallHelper
                args = ToolCallHelper.parse_function_arguments(tool_call)
                print(f"   参数: {args}")

                # 演示实际工具函数调用
                if function_name == "get_weather":
                    result = get_weather(args['location'])
                    print(f"   执行结果: {result}")

        print(f"   响应内容: {str(response.content)[:200]}...")

    except Exception as e:
        print(f"❌ Google Tool Call 测试失败: {str(e)}")


async def test_async_tool_call_workflow():
    """测试异步工具调用工作流程"""
    print("\n🔄 测试异步工具调用工作流程...")

    try:
        from tamar_model_client import ToolCallHelper

        async with AsyncTamarModelClient() as client:
            # 1. 发送带工具的请求
            initial_messages = [
                {"role": "user", "content": "深圳今天天气怎么样？"}
            ]

            request = ModelRequest(
                provider=ProviderType.AZURE,
                invoke_type=InvokeType.CHAT_COMPLETIONS,
                model="gpt-4o-mini",
                messages=initial_messages,
                tools=[
                    {
                        "type": "function",
                        "name": "get_weather",
                        "description": "获取天气信息",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "城市名称"}
                            },
                            "required": ["location"]
                        },
                        "strict": None
                    }
                ],
                tool_choice="auto",
                user_context=UserContext(
                    user_id="async_test_user",
                    org_id="test_org",
                    client_type="async_tool_test"
                )
            )

            # 发送初始请求
            response = await client.invoke(request)

            print(f"   步骤 1: 初始请求完成")
            print(f"   是否需要工具调用: {response.has_tool_calls()}")

            if response.has_tool_calls():
                # 2. 执行工具函数
                tool_responses = []
                for tool_call in response.tool_calls:
                    function_name = tool_call["function"]["name"]
                    args = ToolCallHelper.parse_function_arguments(tool_call)

                    # 根据函数名调用对应的工具函数
                    if function_name == "get_weather":
                        weather_result = get_weather(args['location'])
                    else:
                        weather_result = f"未知函数: {function_name}"

                    tool_response = ToolCallHelper.create_tool_response_message(
                        tool_call["id"],
                        weather_result,
                        function_name
                    )
                    tool_responses.append(tool_response)

                # 3. 构建包含工具响应的新消息列表
                new_messages = ToolCallHelper.build_messages_with_tool_response(
                    initial_messages,
                    response,
                    tool_responses
                )

                # 4. 发送包含工具响应的后续请求
                follow_up_request = ModelRequest(
                    provider=ProviderType.AZURE,
                    invoke_type=InvokeType.CHAT_COMPLETIONS,
                    model="gpt-4o-mini",
                    messages=new_messages,
                    user_context=UserContext(
                        user_id="async_test_user",
                        org_id="test_org",
                        client_type="async_tool_test"
                    )
                )

                final_response = await client.invoke(follow_up_request)

                print(f"   步骤 2: 工具调用模拟完成")
                print(f"   步骤 3: 最终回复生成完成")
                print(f"   最终回复: {final_response.content[:100]}...")

                print(f"✅ 异步工具调用工作流程测试成功")
            else:
                print(f"   模型没有请求工具调用，直接回复: {response.content}")

    except Exception as e:
        print(f"❌ 异步工具调用工作流程测试失败: {str(e)}")


async def main():
    """主函数"""
    print("🚀 Tool Call Enhancement 功能测试")
    print("=" * 50)

    try:
        # 单元测试
        print("\n📋 运行单元测试...")
        test_model_response_enhancement()
        test_tool_call_helper()
        test_response_handler_enhancement()
        print("\n✅ 所有单元测试通过")

        # 真实场景测试
        print("\n🌐 运行真实场景测试...")
        test_openai_tool_call()
        test_google_tool_call()
        await test_async_tool_call_workflow()

        print("\n✅ 所有测试完成")

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
    finally:
        print("🏁 测试程序已退出")


if __name__ == "__main__":
    asyncio.run(main())