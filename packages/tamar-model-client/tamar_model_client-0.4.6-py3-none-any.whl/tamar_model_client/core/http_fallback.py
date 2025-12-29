"""
HTTP fallback functionality for resilient clients

This module provides mixin classes for HTTP-based fallback when gRPC
connections fail, supporting both synchronous and asynchronous clients.
"""

import json
import logging
from typing import Optional, Iterator, AsyncIterator, Dict, Any, List

from . import generate_request_id, get_protected_logger
from ..schemas import ModelRequest, ModelResponse

logger = get_protected_logger(__name__)


def safe_serialize(obj: Any) -> Any:
    """
    安全地序列化对象，避免 Pydantic ValidatorIterator 序列化问题
    """
    if obj is None:
        return None
    
    # 处理基本类型
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # 处理列表
    if isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    
    # 处理字典
    if isinstance(obj, dict):
        return {key: safe_serialize(value) for key, value in obj.items()}
    
    # 处理 Pydantic 模型
    if hasattr(obj, 'model_dump'):
        try:
            return obj.model_dump(exclude_unset=True)
        except Exception:
            # 如果 model_dump 失败，尝试手动提取字段
            try:
                if hasattr(obj, '__dict__'):
                    return {k: safe_serialize(v) for k, v in obj.__dict__.items() 
                           if not k.startswith('_') and not callable(v)}
                elif hasattr(obj, '__slots__'):
                    return {slot: safe_serialize(getattr(obj, slot, None)) 
                           for slot in obj.__slots__ if hasattr(obj, slot)}
            except Exception:
                pass
    
    # 处理 Pydantic v1 模型
    if hasattr(obj, 'dict'):
        try:
            return obj.dict(exclude_unset=True)
        except Exception:
            pass
    
    # 处理枚举
    if hasattr(obj, 'value'):
        return obj.value
    
    # 最后的尝试：转换为字符串
    try:
        return str(obj)
    except Exception:
        return None


class HttpFallbackMixin:
    """HTTP fallback functionality for synchronous clients
    
    This mixin requires the following attributes from the host class:
    - http_fallback_url: str - The HTTP fallback URL (from BaseClient._init_resilient_features)
    - jwt_token: Optional[str] - JWT token for authentication (from BaseClient)
    
    Usage:
        This mixin should be used with BaseClient or its subclasses that have
        initialized the resilient features with _init_resilient_features().
    """
    
    def _ensure_http_client(self) -> None:
        """Ensure HTTP client is initialized"""
        if not hasattr(self, '_http_client') or not self._http_client:
            import requests
            self._http_client = requests.Session()
            
            # Set authentication header if available
            # Note: JWT token will be set per request in headers
            
            # Set default headers
            self._http_client.headers.update({
                'User-Agent': 'TamarModelClient/1.0'
            })
    
    def _convert_to_http_format(self, model_request: ModelRequest) -> Dict[str, Any]:
        """Convert ModelRequest to HTTP payload format"""
        # Use safe serialization to avoid Pydantic ValidatorIterator issues
        payload = {
            "provider": safe_serialize(model_request.provider),
            "model": safe_serialize(model_request.model),
            "user_context": safe_serialize(model_request.user_context),
            "stream": safe_serialize(model_request.stream)
        }
        
        # Add provider-specific fields
        if hasattr(model_request, 'messages') and model_request.messages:
            payload['messages'] = safe_serialize(model_request.messages)
        if hasattr(model_request, 'contents') and model_request.contents:
            payload['contents'] = safe_serialize(model_request.contents)
        
        # Add optional fields
        if model_request.channel:
            payload['channel'] = safe_serialize(model_request.channel)
        if model_request.invoke_type:
            payload['invoke_type'] = safe_serialize(model_request.invoke_type)
            
        # Add config parameters safely
        if hasattr(model_request, 'config') and model_request.config:
            payload['config'] = safe_serialize(model_request.config)
        
        # Add extra parameters safely
        if hasattr(model_request, 'model_extra') and model_request.model_extra:
            serialized_extra = safe_serialize(model_request.model_extra)
            if isinstance(serialized_extra, dict):
                for key, value in serialized_extra.items():
                    if key not in payload:
                        payload[key] = value
                
        return payload
    
    def _handle_http_stream(self, url: str, payload: Dict[str, Any], 
                           timeout: Optional[float], request_id: str, headers: Dict[str, str]) -> Iterator[ModelResponse]:
        """Handle HTTP streaming response"""
        import requests
        
        response = self._http_client.post(
            url,
            json=payload,
            timeout=timeout or 30,
            headers=headers,
            stream=True
        )
        response.raise_for_status()
        
        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        yield ModelResponse(**data)
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Failed to parse streaming response: {data_str}")
    
    def _invoke_http_fallback(self, model_request: ModelRequest, 
                             timeout: Optional[float] = None,
                             request_id: Optional[str] = None,
                             origin_request_id: Optional[str] = None) -> Any:
        """HTTP fallback implementation"""
        # Check if http_fallback_url is available
        if not hasattr(self, 'http_fallback_url') or not self.http_fallback_url:
            raise RuntimeError("HTTP fallback URL not configured. Please set MODEL_CLIENT_HTTP_FALLBACK_URL environment variable.")
        
        self._ensure_http_client()
        
        # Generate request ID if not provided
        if not request_id:
            request_id = generate_request_id()
        
        # Log fallback usage
        logger.warning(
            f"🔻 Using HTTP fallback for request",
            extra={
                "log_type": "info",
                "request_id": request_id,
                "data": {
                    "origin_request_id": origin_request_id,
                    "provider": model_request.provider.value,
                    "model": model_request.model,
                    "fallback_url": self.http_fallback_url
                }
            }
        )
        
        # Convert to HTTP format
        http_payload = self._convert_to_http_format(model_request)
        
        # Construct URL
        url = f"{self.http_fallback_url}/v1/invoke"
        
        # Build headers with authentication and request tracking
        headers = {
            'X-Request-ID': request_id,
            'Content-Type': 'application/json',
            'User-Agent': 'TamarModelClient/1.0'
        }
        
        # Add origin request ID if provided
        if origin_request_id:
            headers['X-Origin-Request-ID'] = origin_request_id
        
        # Add JWT authentication if available
        if hasattr(self, 'jwt_token') and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        if model_request.stream:
            # Return streaming iterator
            return self._handle_http_stream(url, http_payload, timeout, request_id, headers)
        else:
            # Non-streaming request
            response = self._http_client.post(
                url,
                json=http_payload,
                timeout=timeout or 30,
                headers=headers
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return ModelResponse(**data)
    
    def _invoke_batch_http_fallback(self, batch_request: 'BatchModelRequest',
                                   timeout: Optional[float] = None,
                                   request_id: Optional[str] = None,
                                   origin_request_id: Optional[str] = None) -> List['BatchModelResponse']:
        """HTTP batch fallback implementation"""
        # Import here to avoid circular import
        from ..schemas import BatchModelRequest, BatchModelResponse
        
        # Check if http_fallback_url is available
        if not hasattr(self, 'http_fallback_url') or not self.http_fallback_url:
            raise RuntimeError("HTTP fallback URL not configured. Please set MODEL_CLIENT_HTTP_FALLBACK_URL environment variable.")
        
        self._ensure_http_client()
        
        # Generate request ID if not provided
        if not request_id:
            request_id = generate_request_id()
        
        # Log fallback usage
        logger.warning(
            f"🔻 Using HTTP fallback for batch request",
            extra={
                "log_type": "info",
                "request_id": request_id,
                "data": {
                    "origin_request_id": origin_request_id,
                    "batch_size": len(batch_request.items),
                    "fallback_url": self.http_fallback_url
                }
            }
        )
        
        # Convert to HTTP format
        http_payload = {
            "user_context": batch_request.user_context.model_dump(),
            "items": []
        }
        
        # Convert each item
        for item in batch_request.items:
            item_payload = self._convert_to_http_format(item)
            if hasattr(item, 'custom_id') and item.custom_id:
                item_payload['custom_id'] = item.custom_id
            if hasattr(item, 'priority') and item.priority is not None:
                item_payload['priority'] = item.priority
            http_payload['items'].append(item_payload)
        
        # Construct URL
        url = f"{self.http_fallback_url}/v1/batch-invoke"
        
        # Build headers with authentication and request tracking
        headers = {
            'X-Request-ID': request_id,
            'Content-Type': 'application/json',
            'User-Agent': 'TamarModelClient/1.0'
        }
        
        # Add origin request ID if provided
        if origin_request_id:
            headers['X-Origin-Request-ID'] = origin_request_id
        
        # Add JWT authentication if available
        if hasattr(self, 'jwt_token') and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        # Send batch request
        response = self._http_client.post(
            url,
            json=http_payload,
            timeout=timeout or 120,  # Longer timeout for batch requests
            headers=headers
        )
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        results = []
        for item_data in data.get('results', []):
            results.append(BatchModelResponse(**item_data))
        
        return results


class AsyncHttpFallbackMixin:
    """HTTP fallback functionality for asynchronous clients
    
    This mixin requires the following attributes from the host class:
    - http_fallback_url: str - The HTTP fallback URL (from BaseClient._init_resilient_features)
    - jwt_token: Optional[str] - JWT token for authentication (from BaseClient)
    
    Usage:
        This mixin should be used with BaseClient or its subclasses that have
        initialized the resilient features with _init_resilient_features().
    """
    
    async def _ensure_http_client(self) -> None:
        """Ensure async HTTP client is initialized in the correct event loop"""
        import asyncio
        import aiohttp
        
        # Get current event loop
        current_loop = asyncio.get_running_loop()
        
        # Check if we need to recreate the session
        need_new_session = False
        
        if not hasattr(self, '_http_session') or not self._http_session:
            need_new_session = True
        elif hasattr(self, '_http_session_loop') and self._http_session_loop != current_loop:
            # Session was created in a different event loop
            logger.warning("🔄 HTTP session bound to different event loop, recreating...")
            # Close old session if possible
            try:
                await self._http_session.close()
            except Exception as e:
                logger.debug(f"Error closing old session: {e}")
            need_new_session = True
            
        if need_new_session:
            self._http_session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'AsyncTamarModelClient/1.0'
                }
            )
            self._http_session_loop = current_loop
            
            # Note: JWT token will be set per request in headers
    
    def _convert_to_http_format(self, model_request: ModelRequest) -> Dict[str, Any]:
        """Convert ModelRequest to HTTP payload format (reuse sync version)"""
        # This method doesn't need to be async, so we can reuse the sync version
        return HttpFallbackMixin._convert_to_http_format(self, model_request)
    
    async def _handle_http_stream(self, url: str, payload: Dict[str, Any],
                                 timeout: Optional[float], request_id: str, headers: Dict[str, str]) -> AsyncIterator[ModelResponse]:
        """Handle async HTTP streaming response"""
        import aiohttp
        
        timeout_obj = aiohttp.ClientTimeout(total=timeout or 30) if timeout else None
        
        async with self._http_session.post(
            url,
            json=payload,
            timeout=timeout_obj,
            headers=headers
        ) as response:
            response.raise_for_status()
            
            # Parse SSE stream
            async for line_bytes in response.content:
                if line_bytes:
                    line_str = line_bytes.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            yield ModelResponse(**data)
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Failed to parse streaming response: {data_str}")
    
    async def _invoke_http_fallback(self, model_request: ModelRequest,
                                   timeout: Optional[float] = None,
                                   request_id: Optional[str] = None,
                                   origin_request_id: Optional[str] = None) -> Any:
        """Async HTTP fallback implementation"""
        # Check if http_fallback_url is available
        if not hasattr(self, 'http_fallback_url') or not self.http_fallback_url:
            raise RuntimeError("HTTP fallback URL not configured. Please set MODEL_CLIENT_HTTP_FALLBACK_URL environment variable.")
        
        await self._ensure_http_client()
        
        # Generate request ID if not provided
        if not request_id:
            request_id = generate_request_id()
        
        # Log fallback usage
        logger.warning(
            f"🔻 Using HTTP fallback for request",
            extra={
                "log_type": "info",
                "request_id": request_id,
                "data": {
                    "origin_request_id": origin_request_id,
                    "provider": model_request.provider.value,
                    "model": model_request.model,
                    "fallback_url": self.http_fallback_url
                }
            }
        )
        
        # Convert to HTTP format
        http_payload = self._convert_to_http_format(model_request)
        print(http_payload)
        
        # Construct URL
        url = f"{self.http_fallback_url}/v1/invoke"
        
        # Build headers with authentication and request tracking
        headers = {
            'X-Request-ID': request_id,
            'Content-Type': 'application/json',
            'User-Agent': 'AsyncTamarModelClient/1.0'
        }
        
        # Add origin request ID if provided
        if origin_request_id:
            headers['X-Origin-Request-ID'] = origin_request_id
        
        # Add JWT authentication if available
        if hasattr(self, 'jwt_token') and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        if model_request.stream:
            # Return async streaming iterator
            return self._handle_http_stream(url, http_payload, timeout, request_id, headers)
        else:
            # Non-streaming request
            import aiohttp
            timeout_obj = aiohttp.ClientTimeout(total=timeout or 30) if timeout else None
            
            async with self._http_session.post(
                url,
                json=http_payload,
                timeout=timeout_obj,
                headers=headers
            ) as response:
                response.raise_for_status()
                
                # Parse response
                data = await response.json()
                return ModelResponse(**data)
    
    async def _invoke_batch_http_fallback(self, batch_request: 'BatchModelRequest',
                                         timeout: Optional[float] = None,
                                         request_id: Optional[str] = None,
                                         origin_request_id: Optional[str] = None) -> List['BatchModelResponse']:
        """Async HTTP batch fallback implementation"""
        # Import here to avoid circular import
        from ..schemas import BatchModelRequest, BatchModelResponse
        
        # Check if http_fallback_url is available
        if not hasattr(self, 'http_fallback_url') or not self.http_fallback_url:
            raise RuntimeError("HTTP fallback URL not configured. Please set MODEL_CLIENT_HTTP_FALLBACK_URL environment variable.")
        
        await self._ensure_http_client()
        
        # Generate request ID if not provided
        if not request_id:
            request_id = generate_request_id()
        
        # Log fallback usage
        logger.warning(
            f"🔻 Using HTTP fallback for batch request",
            extra={
                "log_type": "info",
                "request_id": request_id,
                "data": {
                    "origin_request_id": origin_request_id,
                    "batch_size": len(batch_request.items),
                    "fallback_url": self.http_fallback_url
                }
            }
        )
        
        # Convert to HTTP format
        http_payload = {
            "user_context": batch_request.user_context.model_dump(),
            "items": []
        }
        
        # Convert each item
        for item in batch_request.items:
            item_payload = self._convert_to_http_format(item)
            if hasattr(item, 'custom_id') and item.custom_id:
                item_payload['custom_id'] = item.custom_id
            if hasattr(item, 'priority') and item.priority is not None:
                item_payload['priority'] = item.priority
            http_payload['items'].append(item_payload)
        
        # Construct URL
        url = f"{self.http_fallback_url}/v1/batch-invoke"
        
        # Build headers with authentication and request tracking
        headers = {
            'X-Request-ID': request_id,
            'Content-Type': 'application/json',
            'User-Agent': 'AsyncTamarModelClient/1.0'
        }
        
        # Add origin request ID if provided
        if origin_request_id:
            headers['X-Origin-Request-ID'] = origin_request_id
        
        # Add JWT authentication if available
        if hasattr(self, 'jwt_token') and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        # Send batch request
        import aiohttp
        timeout_obj = aiohttp.ClientTimeout(total=timeout or 120) if timeout else None
        
        async with self._http_session.post(
            url,
            json=http_payload,
            timeout=timeout_obj,
            headers=headers
        ) as response:
            response.raise_for_status()
            
            # Parse response
            data = await response.json()
            results = []
            for item_data in data.get('results', []):
                results.append(BatchModelResponse(**item_data))
            
            return results
    
    async def _cleanup_http_session(self) -> None:
        """Clean up HTTP session"""
        if hasattr(self, '_http_session') and self._http_session:
            await self._http_session.close()
            self._http_session = None
        if hasattr(self, '_http_session_loop'):
            self._http_session_loop = None