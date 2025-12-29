from typing import Optional

import httpx
from openai import Omit, omit
from openai._types import FileTypes, Headers, Query, Body, NotGiven, not_given
from openai.types import VideoModel, VideoSeconds, VideoSize
from pydantic import BaseModel, Field

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class OpenAIVideosInput(BaseModel):
    prompt: str
    input_reference: FileTypes | TamarFileIdInput | Omit = omit
    model: VideoModel | Omit = omit
    seconds: VideoSeconds | Omit = omit
    size: VideoSize | Omit = omit
    extra_headers: Headers | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    # 回调
    enable_async_task: bool = True
    callback_url: Optional[str] = Field(None, description="异步任务完成后的回调地址")

    model_config = {
        "arbitrary_types_allowed": True
    }
