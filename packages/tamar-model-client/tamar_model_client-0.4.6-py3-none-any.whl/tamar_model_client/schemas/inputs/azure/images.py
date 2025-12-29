"""
Azure 图片生成/编辑 Schema 定义

Azure OpenAI 支持的模型：
1. gpt-image-1: 复用 OpenAI 的 Schema（图片生成）
2. FLUX-1.1-pro: Azure 独有 Flux 模型（图片生成）
3. FLUX.1-Kontext-pro: Azure 独有 Flux 模型（图片编辑）

注意：dall-e-3/dall-e-2 已不推荐使用，推荐使用 gpt-image-1
"""
from typing import Optional, Literal, Union, List

import httpx
from openai import Omit, omit
from openai._types import Headers, Query, Body, NotGiven, not_given, FileTypes, SequenceNotStr
from openai.types import ImageModel
from pydantic import BaseModel, Field, field_validator

from tamar_model_client.schemas.inputs.base import TamarFileIdInput
from tamar_model_client.utils import convert_file_field


# ========================================
# Flux 专用 Schema（Azure 独有）
# ========================================

class AzureFluxImageInput(BaseModel):
    """
    FLUX-1.1-pro 图片生成专用 Schema（Azure 独有）

    官方文档参数：
    - prompt: 正向提示词（必填）
    - aspect_ratio: 宽高比（可选，默认 1:1）
    - output_format: 输出格式（可选，默认 jpg）
    - seed: 随机种子（可选，范围 -1 到 2147483647）
    - enable_base64_output: 是否返回 BASE64 编码（可选，默认 false）
    """
    prompt: str = Field(..., description="正向提示词")
    aspect_ratio: Optional[Literal["1:1", "16:9", "9:16", "4:3", "3:4"]] | Omit = Field(
        omit,
        description="宽高比，默认 1:1"
    )
    output_format: Optional[Literal["jpg", "png"]] | Omit = Field(
        omit,
        description="输出格式，默认 jpg"
    )
    seed: Optional[int] | Omit = Field(
        omit,
        description="随机种子，范围 -1 到 2147483647"
    )
    enable_base64_output: Optional[bool] | Omit = Field(
        omit,
        description="是否返回 BASE64 编码，默认 false"
    )
    model: Union[str, ImageModel, None] | Omit = omit
    user: str | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    # 异步任务控制参数
    callback_url: Optional[str] = Field(None, description="异步任务完成后的回调地址")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


class AzureFluxImageEditInput(BaseModel):
    """
    FLUX.1-Kontext-pro 图片编辑专用 Schema（Azure 独有）

    官方文档参数：
    - prompt: 正向提示词（必填）
    - image: 要编辑的图片（必填）
    - guidance_scale: 引导比例（可选，默认 3.5，范围 1.0-20.0）
    - aspect_ratio: 宽高比（可选）
    - enable_sync_mode: 是否启用同步模式（可选，默认 false）
    """
    prompt: str = Field(..., description="正向提示词")
    image: Union[FileTypes, SequenceNotStr[FileTypes], TamarFileIdInput, List[TamarFileIdInput]] = Field(
        ...,
        description="要编辑的图片"
    )
    guidance_scale: Optional[float] | Omit = Field(
        omit,
        description="引导比例，默认 3.5，范围 1.0-20.0"
    )
    aspect_ratio: Optional[Literal["21:9", "16:9", "4:3", "3:2", "1:1", "2:3", "3:4", "9:16", "9:21"]] | Omit = Field(
        omit,
        description="宽高比"
    )
    enable_sync_mode: Optional[bool] | Omit = Field(
        omit,
        description="是否启用同步模式，默认 false"
    )
    model: Union[str, ImageModel, None] | Omit = omit
    user: str | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    # 异步任务控制参数
    callback_url: Optional[str] = Field(None, description="异步任务完成后的回调地址")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("image", mode="before")
    @classmethod
    def validate_image(cls, v):
        return convert_file_field(v)
