"""
Schema definitions for the API
"""

from .inputs import UserContext, ModelRequest, BatchModelRequestItem, BatchModelRequest, TamarFileIdInput
from .outputs import ModelResponse, BatchModelResponse, TaskStatusResponse, BatchTaskStatusResponse

__all__ = [
    # Model Inputs
    "TamarFileIdInput",
    "UserContext",
    "ModelRequest",
    "BatchModelRequestItem",
    "BatchModelRequest",
    # Model Outputs
    "ModelResponse",
    "BatchModelResponse",
    "TaskStatusResponse",
    "BatchTaskStatusResponse",
]
