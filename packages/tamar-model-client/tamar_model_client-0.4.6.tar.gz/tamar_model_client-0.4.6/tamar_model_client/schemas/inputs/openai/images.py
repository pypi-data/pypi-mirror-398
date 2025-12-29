from typing import Optional, Literal, Union, List

import httpx
from openai import Omit, omit
from openai._types import Headers, Query, Body, NotGiven, not_given, FileTypes, SequenceNotStr
from openai.types import ImageModel
from pydantic import BaseModel, field_validator

from tamar_model_client.schemas.inputs.base import TamarFileIdInput
from tamar_model_client.utils import convert_file_field


class OpenAIImagesInput(BaseModel):
    prompt: str
    background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit
    model: Union[str, ImageModel, None] | Omit = omit
    moderation: Optional[Literal["low", "auto"]] | Omit = omit
    n: Optional[int] | Omit = omit
    output_compression: Optional[int] | Omit = omit
    output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit
    partial_images: Optional[int] | Omit = omit
    quality: Optional[Literal["standard", "hd", "low", "medium", "high", "auto"]] | Omit = omit
    response_format: Optional[Literal["url", "b64_json"]] | Omit = omit
    size: Optional[Literal[
        "auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"]] | Omit = omit
    stream: Optional[Literal[False]] | Literal[True] | Omit = omit
    style: Optional[Literal["vivid", "natural"]] | Omit = omit
    user: str | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    # 异步任务控制参数（Azure OpenAI 支持）
    callback_url: Optional[str] = None
    enable_async_task: bool = False

    model_config = {
        "arbitrary_types_allowed": True
    }


class OpenAIImagesEditInput(BaseModel):
    image: Union[FileTypes, SequenceNotStr[FileTypes], TamarFileIdInput, List[TamarFileIdInput]]
    prompt: str
    background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit
    input_fidelity: Optional[Literal["high", "low"]] | Omit = omit
    mask: FileTypes | Omit = omit
    model: Union[str, ImageModel, None] | Omit = omit
    n: Optional[int] | Omit = omit
    output_compression: Optional[int] | Omit = omit
    output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit
    partial_images: Optional[int] | Omit = omit
    quality: Optional[Literal["standard", "low", "medium", "high", "auto"]] | Omit = omit
    response_format: Optional[Literal["url", "b64_json"]] | Omit = omit
    size: Optional[Literal["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"]] | Omit = omit
    stream: Optional[Literal[False]] | Literal[True] | Omit = omit
    user: str | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    # 异步任务控制参数（Azure OpenAI 支持）
    callback_url: Optional[str] = None
    enable_async_task: bool = False

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("image", mode="before")
    @classmethod
    def validate_image(cls, v):
        return convert_file_field(v)

    @field_validator("mask", mode="before")
    @classmethod
    def validate_mask(cls, v):
        return convert_file_field(v)
