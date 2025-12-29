import json
import logging
from datetime import datetime
from typing import Any

# 尝试导入 NotGiven，如果失败则定义一个占位类
try:
    from openai import NOT_GIVEN
    NotGiven = type(NOT_GIVEN)
except ImportError:
    class NotGiven:
        pass


class SafeJSONEncoder(json.JSONEncoder):
    """安全的 JSON 编码器，能处理特殊类型"""
    
    def default(self, obj):
        # 处理 NotGiven 类型
        if isinstance(obj, NotGiven):
            return None
        
        # 处理 datetime 类型
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # 处理 bytes 类型
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        
        # 处理其他不可序列化的对象
        try:
            return super().default(obj)
        except TypeError:
            # 返回对象的字符串表示
            return str(obj)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        # log_type 只能是 request、response 或 info
        log_type = getattr(record, "log_type", "info")
        if log_type not in ["request", "response", "info"]:
            log_type = "info"
            
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "type": log_type,
            "uri": getattr(record, "uri", None),
            "request_id": getattr(record, "request_id", None),
            "data": getattr(record, "data", None),
            "message": record.getMessage(),
            "duration": getattr(record, "duration", None),
        }
        # 增加 trace 支持
        if hasattr(record, "trace"):
            log_data["trace"] = getattr(record, "trace")
        
        # 添加异常信息（如果有的话）
        if record.exc_info:
            import traceback
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 使用安全的 JSON 编码器
        return json.dumps(log_data, ensure_ascii=False, cls=SafeJSONEncoder)