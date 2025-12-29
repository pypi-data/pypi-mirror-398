"""
Tamar Model Client 异常定义

提供了完整的错误分类体系，支持结构化错误信息和恢复策略。
"""

import grpc
from datetime import datetime
from typing import Optional, Dict, Any, Union
from collections import defaultdict


# ===== 错误分类定义 =====

# 错误类别映射
ERROR_CATEGORIES = {
    'NETWORK': [
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.DEADLINE_EXCEEDED,
        grpc.StatusCode.CANCELLED,      # 网络中断导致的取消
    ],
    'CONCURRENCY': [
        grpc.StatusCode.ABORTED,        # 并发冲突，单独分类便于监控
    ],
    'AUTH': [
        grpc.StatusCode.UNAUTHENTICATED,
        grpc.StatusCode.PERMISSION_DENIED,
    ],
    'VALIDATION': [
        grpc.StatusCode.INVALID_ARGUMENT,
        grpc.StatusCode.OUT_OF_RANGE,
        grpc.StatusCode.FAILED_PRECONDITION,
    ],
    'RESOURCE': [
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        grpc.StatusCode.NOT_FOUND,
        grpc.StatusCode.ALREADY_EXISTS,
    ],
    'PROVIDER': [
        grpc.StatusCode.INTERNAL,
        grpc.StatusCode.UNKNOWN,
        grpc.StatusCode.UNIMPLEMENTED,
    ],
    'DATA': [
        grpc.StatusCode.DATA_LOSS,
    ]
}

# 详细的重试策略
RETRY_POLICY = {
    grpc.StatusCode.UNAVAILABLE: {
        'retryable': True,
        'backoff': 'exponential',
        'max_attempts': 1  # 降低到 1 次重试（避免长时间累积等待）
    },
    grpc.StatusCode.DEADLINE_EXCEEDED: {
        'retryable': True, 
        'backoff': 'linear',
        'max_attempts': 3
    },
    grpc.StatusCode.RESOURCE_EXHAUSTED: {
        'retryable': True, 
        'backoff': 'exponential',
        'check_details': True,  # 检查具体错误信息
        'max_attempts': 3
    },
    grpc.StatusCode.INTERNAL: {
        'retryable': False,  # 内部错误通常不应重试
        'check_details': True,
        'max_attempts': 0
    },
    grpc.StatusCode.UNAUTHENTICATED: {
        'retryable': True,
        'action': 'refresh_token',  # 特殊动作
        'max_attempts': 1
    },
    grpc.StatusCode.CANCELLED: {
        'retryable': True,
        'backoff': 'linear',        # 线性退避，网络问题通常不需要指数退避
        'max_attempts': 5,          # 最大重试次数（不包括初始请求），总共会尝试6次
        'check_details': False      # 不检查详细信息，统一重试
    },
    grpc.StatusCode.ABORTED: {
        'retryable': True,
        'backoff': 'exponential',   # 指数退避，避免加剧并发竞争
        'max_attempts': 3,          # 适中的重试次数
        'jitter': True,             # 添加随机延迟，减少竞争
        'check_details': False
    },
    # 不可重试的错误
    grpc.StatusCode.INVALID_ARGUMENT: {'retryable': False},
    grpc.StatusCode.NOT_FOUND: {'retryable': False},
    grpc.StatusCode.ALREADY_EXISTS: {'retryable': False},
    grpc.StatusCode.PERMISSION_DENIED: {'retryable': False},
}


# ===== 错误上下文类 =====

class ErrorContext:
    """增强的错误上下文信息"""
    
    def __init__(self, error: Optional[grpc.RpcError] = None, request_context: Optional[dict] = None):
        self.error_code = error.code() if error else None
        self.error_message = error.details() if error else ""
        self.error_debug_string = error.debug_error_string() if error and hasattr(error, 'debug_error_string') else ""
        
        # 请求上下文
        request_context = request_context or {}
        self.request_id = request_context.get('request_id')
        self.timestamp = datetime.utcnow().isoformat()
        self.provider = request_context.get('provider')
        self.model = request_context.get('model')
        self.method = request_context.get('method')
        
        # 重试信息
        self.retry_count = request_context.get('retry_count', 0)
        self.total_duration = request_context.get('duration')
        
        # 额外的诊断信息
        self.client_version = request_context.get('client_version')
        self.server_info = self._extract_server_info(error) if error else None
        
    def _extract_server_info(self, error) -> Optional[Dict[str, Any]]:
        """从错误中提取服务端信息"""
        try:
            # 尝试从 trailing metadata 获取服务端信息
            if hasattr(error, 'trailing_metadata') and error.trailing_metadata():
                metadata = {}
                for key, value in error.trailing_metadata():
                    metadata[key] = value
                return metadata
        except:
            pass
        return None
        
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'error_code': self.error_code.name if self.error_code else 'UNKNOWN',
            'error_message': self.error_message,
            'request_id': self.request_id,
            'timestamp': self.timestamp,
            'provider': self.provider,
            'model': self.model,
            'method': self.method,
            'retry_count': self.retry_count,
            'total_duration': self.total_duration,
            'category': self._get_error_category(),
            'is_retryable': self._is_retryable(),
            'suggested_action': self._get_suggested_action(),
            'debug_info': {
                'client_version': self.client_version,
                'server_info': self.server_info,
                'debug_string': self.error_debug_string
            }
        }
    
    def _get_error_category(self) -> str:
        """获取错误类别"""
        if not self.error_code:
            return 'UNKNOWN'
        for category, codes in ERROR_CATEGORIES.items():
            if self.error_code in codes:
                return category
        return 'UNKNOWN'
    
    def _is_retryable(self) -> bool:
        """判断是否可重试"""
        if not self.error_code:
            return False
        policy = RETRY_POLICY.get(self.error_code, {})
        return policy.get('retryable', False) == True
    
    def _get_suggested_action(self) -> str:
        """获取建议的处理动作"""
        suggestions = {
            'NETWORK': '检查网络连接，稍后重试',
            'CONCURRENCY': '并发冲突，系统会自动重试',
            'AUTH': '检查认证信息，可能需要刷新 Token',
            'VALIDATION': '检查请求参数是否正确',
            'RESOURCE': '检查资源限制或等待一段时间',
            'PROVIDER': '服务端错误，联系技术支持',
            'DATA': '数据损坏或丢失，请检查输入数据',
        }
        return suggestions.get(self._get_error_category(), '未知错误，请联系技术支持')
    
    def is_network_cancelled(self) -> bool:
        """
        判断 CANCELLED 错误是否由网络中断导致
        
        Returns:
            bool: 如果是网络中断导致的 CANCELLED 返回 True
        """
        if self.error_code != grpc.StatusCode.CANCELLED:
            return False
            
        # 检查错误消息中是否包含网络相关的关键词
        error_msg = (self.error_message or '').lower()
        debug_msg = (self.error_debug_string or '').lower()
        
        network_patterns = [
            'connection reset',
            'connection refused', 
            'connection closed',
            'network unreachable',
            'broken pipe',
            'socket closed',
            'eof',
            'transport'
        ]
        
        for pattern in network_patterns:
            if pattern in error_msg or pattern in debug_msg:
                return True
                
        return False


# ===== 异常类层级 =====

class TamarModelException(Exception):
    """Tamar Model Client 基础异常类"""
    
    def __init__(self, error_context: Union[ErrorContext, str, Exception]):
        if isinstance(error_context, str):
            # 简单字符串消息
            self.context = ErrorContext()
            self.context.error_message = error_context
            super().__init__(error_context)
        elif isinstance(error_context, Exception):
            # 从其他异常创建
            self.context = ErrorContext()
            self.context.error_message = str(error_context)
            super().__init__(str(error_context))
        else:
            # ErrorContext 对象
            self.context = error_context
            super().__init__(error_context.error_message)
    
    @property
    def request_id(self) -> Optional[str]:
        """获取请求ID"""
        return self.context.request_id
    
    @property
    def error_code(self) -> Optional[grpc.StatusCode]:
        """获取错误码"""
        return self.context.error_code
    
    @property
    def category(self) -> str:
        """获取错误类别"""
        return self.context._get_error_category()
    
    @property
    def is_retryable(self) -> bool:
        """是否可重试"""
        return self.context._is_retryable()
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return self.context.to_dict()


# ===== 网络相关异常 =====

class NetworkException(TamarModelException):
    """网络相关异常基类"""
    pass


class ConnectionException(NetworkException):
    """连接异常"""
    pass


class TimeoutException(NetworkException):
    """超时异常"""
    pass


class DNSException(NetworkException):
    """DNS 解析异常"""
    pass


# ===== 认证相关异常 =====

class AuthenticationException(TamarModelException):
    """认证相关异常基类"""
    pass


class TokenExpiredException(AuthenticationException):
    """Token 过期异常"""
    pass


class InvalidTokenException(AuthenticationException):
    """无效 Token 异常"""
    pass


class PermissionDeniedException(AuthenticationException):
    """权限拒绝异常"""
    pass


# ===== 限流相关异常 =====

class RateLimitException(TamarModelException):
    """限流相关异常基类"""
    pass


class QuotaExceededException(RateLimitException):
    """配额超限异常"""
    pass


class TooManyRequestsException(RateLimitException):
    """请求过多异常"""
    pass


# ===== 服务商相关异常 =====

class ProviderException(TamarModelException):
    """服务商相关异常基类"""
    pass


class ModelNotFoundException(ProviderException):
    """模型未找到异常"""
    pass


class ProviderUnavailableException(ProviderException):
    """服务商不可用异常"""
    pass


class InvalidResponseException(ProviderException):
    """无效响应异常"""
    pass


# ===== 验证相关异常 =====

class ValidationException(TamarModelException):
    """验证相关异常基类"""
    pass


class InvalidParameterException(ValidationException):
    """无效参数异常"""
    pass


class MissingParameterException(ValidationException):
    """缺少参数异常"""
    pass


# ===== 向后兼容的别名 =====

# 保持与原有代码的兼容性
ModelManagerClientError = TamarModelException
ConnectionError = ConnectionException
ValidationError = ValidationException


# ===== 错误处理工具函数 =====

def categorize_grpc_error(error_code: grpc.StatusCode) -> str:
    """根据 gRPC 错误码分类错误"""
    for category, codes in ERROR_CATEGORIES.items():
        if error_code in codes:
            return category
    return 'UNKNOWN'


def is_retryable_error(error_code: grpc.StatusCode) -> bool:
    """判断 gRPC 错误是否可重试"""
    policy = RETRY_POLICY.get(error_code, {})
    return policy.get('retryable', False) == True


def get_retry_policy(error_code: grpc.StatusCode) -> Dict[str, Any]:
    """获取错误的重试策略"""
    return RETRY_POLICY.get(error_code, {'retryable': False})


# ===== 错误统计 =====

class ErrorStats:
    """错误统计工具"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.category_counts = defaultdict(int)
        self.total_errors = 0
    
    def record_error(self, error_code: grpc.StatusCode):
        """记录错误统计"""
        self.error_counts[error_code.name] += 1
        self.category_counts[categorize_grpc_error(error_code)] += 1
        self.total_errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_errors': self.total_errors,
            'error_counts': dict(self.error_counts),
            'category_counts': dict(self.category_counts)
        }
    
    def reset(self):
        """重置统计"""
        self.error_counts.clear()
        self.category_counts.clear()
        self.total_errors = 0