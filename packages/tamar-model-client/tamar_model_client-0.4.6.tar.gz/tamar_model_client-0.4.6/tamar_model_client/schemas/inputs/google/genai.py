from google.genai import types
from pydantic import BaseModel
from typing import Optional, Union


class GoogleGenAiInput(BaseModel):
    model: str
    contents: Union[types.ContentListUnion, types.ContentListUnionDict]
    config: Optional[types.GenerateContentConfigOrDict] = None
    callback_url: Optional[str] = None  # 异步任务回调地址
    enable_async_task: bool = False  # 是否开启异步任务模式(默认True)

    model_config = {
        "arbitrary_types_allowed": True
    }
