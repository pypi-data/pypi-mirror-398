"""
Azure 专用 Schema 定义

Azure OpenAI 复用 OpenAI 的 Schema（gpt-image-1, dall-e-3, dall-e-2）
仅 Flux 系列为 Azure 独有
"""
from .images import (
    AzureFluxImageInput,
    AzureFluxImageEditInput,
)

__all__ = [
    "AzureFluxImageInput",
    "AzureFluxImageEditInput",
]
