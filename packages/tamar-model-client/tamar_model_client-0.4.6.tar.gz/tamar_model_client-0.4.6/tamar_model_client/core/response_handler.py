"""
Response handling logic for Tamar Model Client

This module provides utilities for processing gRPC responses and
converting them to client response objects.
"""

import json
from typing import Optional, Dict, Any

from ..schemas import ModelResponse, BatchModelResponse, TaskStatusResponse, BatchTaskStatusResponse


class ResponseHandler:
    """
    响应处理器
    
    负责将 gRPC 响应转换为客户端响应对象，
    包括 JSON 解析、错误处理和数据结构转换。
    """
    
    @staticmethod
    def build_model_response(grpc_response) -> ModelResponse:
        """
        从 gRPC 响应构建增强的 ModelResponse 对象
        
        新增功能：
        1. 自动提取 tool_calls（对标 OpenAI SDK）
        2. 提取 finish_reason（对标 OpenAI SDK）
        3. 支持多种 provider 格式转换
        
        Args:
            grpc_response: gRPC 服务返回的响应对象
            
        Returns:
            ModelResponse: 增强的客户端响应对象
        """
        raw_response = ResponseHandler._parse_json_field(grpc_response.raw_response)
        
        # 提取 tool_calls 和 finish_reason
        tool_calls = None
        finish_reason = None
        
        if raw_response and isinstance(raw_response, dict):
            # OpenAI/Azure OpenAI 格式
            if 'choices' in raw_response and raw_response['choices']:
                choice = raw_response['choices'][0]
                
                # 提取 tool_calls
                if 'message' in choice and 'tool_calls' in choice['message']:
                    tool_calls = choice['message']['tool_calls']
                
                # 提取 finish_reason
                if 'finish_reason' in choice:
                    finish_reason = choice['finish_reason']
            
            # Google AI 格式适配
            elif 'candidates' in raw_response and raw_response['candidates']:
                candidate = raw_response['candidates'][0]

                # Google 格式的 function calls 映射
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    google_tool_calls = []

                    # 检查 parts 是否为 None（某些情况下如 IMAGE_SAFETY 过滤时会返回 None）
                    if parts is not None:
                        for i, part in enumerate(parts):
                            if 'functionCall' in part:
                                # 转换为 OpenAI 兼容格式
                                function_call = part['functionCall']
                                google_tool_calls.append({
                                    'id': f"call_{i}_{function_call.get('name', 'unknown')}",
                                    'type': 'function',
                                    'function': {
                                        'name': function_call.get('name', ''),
                                        'arguments': json.dumps(function_call.get('args', {}))
                                    }
                                })

                        if google_tool_calls:
                            tool_calls = google_tool_calls
                
                # Google 的 finish_reason
                if 'finishReason' in candidate:
                    # 映射 Google 格式到标准格式
                    google_reason = candidate['finishReason']
                    finish_reason_mapping = {
                        'STOP': 'stop',
                        'MAX_TOKENS': 'length',
                        'SAFETY': 'content_filter',
                        'RECITATION': 'content_filter'
                    }
                    finish_reason = finish_reason_mapping.get(google_reason, google_reason.lower())
                    
                    # 如果有工具调用，设置 finish_reason 为 tool_calls
                    if tool_calls:
                        finish_reason = 'tool_calls'
        
        return ModelResponse(
            content=grpc_response.content,
            usage=ResponseHandler._parse_json_field(grpc_response.usage),
            error=grpc_response.error or None,
            raw_response=raw_response,
            request_id=grpc_response.request_id if grpc_response.request_id else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason
        )
    
    @staticmethod
    def build_batch_response(grpc_response) -> BatchModelResponse:
        """
        从 gRPC 批量响应构建 BatchModelResponse 对象
        
        Args:
            grpc_response: gRPC 服务返回的批量响应对象
            
        Returns:
            BatchModelResponse: 客户端批量响应对象
        """
        responses = []
        for response_item in grpc_response.items:
            model_response = ResponseHandler.build_model_response(response_item)
            responses.append(model_response)
        
        return BatchModelResponse(
            responses=responses,
            request_id=grpc_response.request_id if grpc_response.request_id else None
        )
    
    @staticmethod
    def _parse_json_field(json_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        安全地解析 JSON 字符串
        
        Args:
            json_str: 待解析的 JSON 字符串
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的字典，或 None（如果输入为空）
        """
        if not json_str:
            return None
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果解析失败，返回原始字符串作为错误信息
            return {"error": "JSON parse error", "raw": json_str}
    
    @staticmethod
    def build_task_status_response(grpc_response) -> TaskStatusResponse:
        """
        从 gRPC 响应构建 TaskStatusResponse 对象

        Args:
            grpc_response: gRPC 服务返回的任务状态响应对象

        Returns:
            TaskStatusResponse: 客户端任务状态响应对象
        """
        result_data = None
        if grpc_response.result_data:
            try:
                result_data = json.loads(grpc_response.result_data)
            except:
                result_data = {"raw": grpc_response.result_data}

        return TaskStatusResponse(
            task_id=grpc_response.task_id,
            provider=grpc_response.provider or None,
            channel=grpc_response.channel or None,
            invoke_type=grpc_response.invoke_type or None,
            model=grpc_response.model or None,
            status=grpc_response.status,
            created_at=grpc_response.created_at or None,
            completed_at=grpc_response.completed_at or None,
            result_data=result_data,
            error_message=grpc_response.error_message or None
        )

    @staticmethod
    def build_batch_task_status_response(grpc_response) -> BatchTaskStatusResponse:
        """
        从 gRPC 批量任务状态响应构建 BatchTaskStatusResponse 对象

        Args:
            grpc_response: gRPC 服务返回的批量任务状态响应对象

        Returns:
            BatchTaskStatusResponse: 客户端批量任务状态响应对象
        """
        tasks = []
        for task_response in grpc_response.tasks:
            task_status = ResponseHandler.build_task_status_response(task_response)
            tasks.append(task_status)

        return BatchTaskStatusResponse(tasks=tasks)

    @staticmethod
    def build_log_data(
        model_request,
        response: Optional[ModelResponse] = None,
        duration: Optional[float] = None,
        error: Optional[Exception] = None,
        stream_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建日志数据
        
        为请求和响应日志构建结构化的数据字典。
        
        Args:
            model_request: 原始请求对象
            response: 响应对象（可选）
            duration: 请求持续时间（秒）
            error: 错误对象（可选）
            stream_stats: 流式响应统计信息（可选）
            
        Returns:
            Dict[str, Any]: 日志数据字典
        """
        data = {
            "provider": model_request.provider.value,
            "invoke_type": model_request.invoke_type.value,
            "model": getattr(model_request, 'model', None),
            "stream": getattr(model_request, 'stream', False),
        }
        
        # 添加用户上下文信息（如果有）
        if hasattr(model_request, 'user_context'):
            data.update({
                "org_id": model_request.user_context.org_id,
                "user_id": model_request.user_context.user_id,
                "client_type": model_request.user_context.client_type
            })
        
        # 添加请求中的 tool 信息
        if hasattr(model_request, 'tools') and model_request.tools:
            data["tools_count"] = len(model_request.tools) if isinstance(model_request.tools, list) else 1
            data["has_tools"] = True
        
        if hasattr(model_request, 'tool_choice') and model_request.tool_choice:
            data["tool_choice"] = str(model_request.tool_choice)
        
        # 添加响应信息
        if response:
            if hasattr(response, 'content') and response.content:
                data["content_length"] = len(response.content)
            if hasattr(response, 'usage'):
                data["usage"] = response.usage
            
            # 新增：tool_calls 相关日志
            if hasattr(response, 'tool_calls') and response.tool_calls:
                data["tool_calls_count"] = len(response.tool_calls)
                data["has_tool_calls"] = True
                
            if hasattr(response, 'finish_reason') and response.finish_reason:
                data["finish_reason"] = response.finish_reason
        
        # 添加流式响应统计
        if stream_stats:
            data.update(stream_stats)
        
        # 添加错误信息
        if error:
            data["error_type"] = type(error).__name__
            data["error_message"] = str(error)
        
        return data