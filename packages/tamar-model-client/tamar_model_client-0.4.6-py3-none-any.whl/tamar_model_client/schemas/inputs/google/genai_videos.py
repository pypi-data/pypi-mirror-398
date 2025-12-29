from google.genai import types
from pydantic import BaseModel
from typing import Any, Optional


class GoogleGenAiVideosInput(BaseModel):
    model: str
    prompt: Optional[str] = None
    image: Optional[types.ImageOrDict] = None
    video: Optional[types.VideoOrDict] = None
    source: Optional[Any] = None  # GenerateVideosSourceOrDict (if available)
    config: Optional[types.GenerateVideosConfigOrDict] = None
    callback_url: Optional[str] = None  # 异步任务回调地址

    model_config = {
        "arbitrary_types_allowed": True
    }
