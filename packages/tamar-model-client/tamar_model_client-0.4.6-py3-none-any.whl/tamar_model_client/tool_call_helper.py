"""
Tool Call 实用工具类

提供简化 Tool Call 使用的基础工具方法，减少常见错误和样板代码。
注意：本工具类仅提供数据处理便利，不包含自动执行功能。
"""

import json
from typing import List, Dict, Any, Optional

from .schemas.outputs import ModelResponse


class ToolCallHelper:
    """Tool Call 实用工具类

    提供基础的数据处理方法，对标 OpenAI SDK 的使用体验。
    """

    @staticmethod
    def create_function_tool(
        name: str,
        description: str,
        parameters: Dict[str, Any],
        strict: Optional[bool] = None
    ) -> Dict[str, Any]:
        """创建函数工具定义（对标 OpenAI SDK 的工具定义格式）

        Args:
            name: 函数名称
            description: 函数描述
            parameters: 函数参数的 JSON Schema
            strict: 是否启用严格模式（OpenAI Structured Outputs）

        Returns:
            ChatCompletionToolParam: 工具定义对象

        Example:
            >>> weather_tool = ToolCallHelper.create_function_tool(
            ...     name="get_weather",
            ...     description="获取指定城市的天气信息",
            ...     parameters={
            ...         "type": "object",
            ...         "properties": {
            ...             "location": {"type": "string", "description": "城市名称"}
            ...         },
            ...         "required": ["location"]
            ...     }
            ... )
        """
        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }

        if strict is not None:
            tool_def["function"]["strict"] = strict

        return tool_def

    @staticmethod
    def create_tool_response_message(
        tool_call_id: str,
        content: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建工具响应消息（对标 OpenAI SDK 的消息格式）

        Args:
            tool_call_id: 工具调用 ID
            content: 工具执行结果
            name: 工具名称（可选）

        Returns:
            ChatCompletionMessageParam: 工具响应消息

        Example:
            >>> tool_message = ToolCallHelper.create_tool_response_message(
            ...     tool_call_id="call_123",
            ...     content="北京今天晴天，25°C",
            ...     name="get_weather"
            ... )
        """
        message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        }

        if name:
            message["name"] = name

        return message

    @staticmethod
    def parse_function_arguments(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """安全解析函数参数（解决 OpenAI SDK 需要手动 json.loads 的痛点）

        Args:
            tool_call: 工具调用对象

        Returns:
            Dict[str, Any]: 解析后的参数字典

        Raises:
            ValueError: 不支持的工具类型或参数解析失败

        Example:
            >>> tool_call = response.tool_calls[0]
            >>> arguments = ToolCallHelper.parse_function_arguments(tool_call)
            >>> print(arguments["location"])  # "北京"
        """
        if tool_call.get("type") != "function":
            raise ValueError(f"不支持的工具类型: {tool_call.get('type')}")

        function = tool_call.get("function", {})
        arguments_str = function.get("arguments", "{}")

        try:
            return json.loads(arguments_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"解析工具参数失败: {arguments_str}") from e

    @staticmethod
    def build_messages_with_tool_response(
        original_messages: List[Dict[str, Any]],
        assistant_message: ModelResponse,
        tool_responses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """构建包含工具响应的消息列表（简化版工具方法）

        Args:
            original_messages: 原始消息列表
            assistant_message: 包含 tool calls 的助手响应
            tool_responses: 工具响应列表

        Returns:
            List[Dict[str, Any]]: 新的消息列表

        Example:
            >>> new_messages = ToolCallHelper.build_messages_with_tool_response(
            ...     original_messages=request.messages,
            ...     assistant_message=response,
            ...     tool_responses=[tool_message]
            ... )
            >>> # 然后开发者手动创建新请求发送
        """
        new_messages = list(original_messages)

        # 添加助手的响应消息
        assistant_msg = {
            "role": "assistant",
            "content": assistant_message.content or ""
        }

        # 如果有 tool calls，添加到消息中
        if assistant_message.has_tool_calls():
            assistant_msg["tool_calls"] = assistant_message.tool_calls

        new_messages.append(assistant_msg)

        # 添加工具响应消息
        new_messages.extend(tool_responses)

        return new_messages