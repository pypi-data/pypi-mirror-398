"""
Core components for Tamar Model Client

This package contains shared components used by both sync and async clients.
"""

from .utils import (
    is_effective_value,
    serialize_value,
    remove_none_from_dict,
    generate_request_id,
    set_request_id,
    get_request_id,
    set_origin_request_id,
    get_origin_request_id
)

from .logging_setup import (
    setup_logger,
    RequestIdFilter,
    TamarLoggerAdapter,
    get_protected_logger,
    reset_logger_config,
    MAX_MESSAGE_LENGTH
)

from .request_id_manager import RequestIdManager

__all__ = [
    # Utils
    'is_effective_value',
    'serialize_value',
    'remove_none_from_dict',
    'generate_request_id',
    'set_request_id',
    'get_request_id',
    'set_origin_request_id',
    'get_origin_request_id',
    # Logging
    'setup_logger',
    'RequestIdFilter',
    'TamarLoggerAdapter',
    'get_protected_logger',
    'reset_logger_config',
    'MAX_MESSAGE_LENGTH',
    # Request ID Management
    'RequestIdManager',
]