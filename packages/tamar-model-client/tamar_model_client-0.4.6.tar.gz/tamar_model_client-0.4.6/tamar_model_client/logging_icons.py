"""
日志图标规范

本模块定义了统一的日志图标标准，确保整个项目中日志消息的视觉一致性。
"""

# 请求生命周期图标
REQUEST_START = "🔵"      # 请求开始
RESPONSE_SUCCESS = "✅"   # 响应成功
RESPONSE_ERROR = "❌"     # 响应错误

# 连接和网络图标
SECURE_CONNECTION = "🔐"  # 安全连接 (TLS)
INSECURE_CONNECTION = "🔓"  # 不安全连接 (无TLS)
CONNECTION_SUCCESS = "✅"  # 连接成功
CONNECTION_RETRY = "🔄"   # 连接重试
CONNECTION_ERROR = "❌"   # 连接错误

# 操作状态图标
SUCCESS = "✅"           # 成功
ERROR = "❌"             # 错误
WARNING = "⚠️"           # 警告
INFO = "ℹ️"              # 信息
RETRY = "🔄"             # 重试
PROCESSING = "⚙️"        # 处理中

# 流式响应图标
STREAM_SUCCESS = "✅"     # 流完成
STREAM_ERROR = "❌"       # 流错误
STREAM_CHUNK = "📦"       # 流数据块

# 批量操作图标
BATCH_START = "🔵"        # 批量开始
BATCH_SUCCESS = "✅"      # 批量成功
BATCH_ERROR = "❌"        # 批量错误

# 系统操作图标
INIT = "🚀"              # 初始化
CLOSE = "🔚"             # 关闭
CLEANUP = "🧹"           # 清理

def get_icon_for_log_type(log_type: str, is_success: bool = True) -> str:
    """
    根据日志类型和状态获取合适的图标
    
    Args:
        log_type: 日志类型 (request, response, info)
        is_success: 是否成功
    
    Returns:
        对应的图标字符串
    """
    if log_type == "request":
        return REQUEST_START
    elif log_type == "response":
        return RESPONSE_SUCCESS if is_success else RESPONSE_ERROR
    elif log_type == "info":
        return INFO if is_success else WARNING
    else:
        return INFO