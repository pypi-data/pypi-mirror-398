from google.genai import types
from pydantic import BaseModel
from typing import Optional


class GoogleGenAIImagesInput(BaseModel):
    model: str
    prompt: str
    config: Optional[types.GenerateImagesConfigOrDict] = None
    callback_url: Optional[str] = None  # 异步任务回调地址
    enable_async_task: bool = True  # 是否开启异步任务模式(默认True)

    model_config = {
        "arbitrary_types_allowed": True
    }
