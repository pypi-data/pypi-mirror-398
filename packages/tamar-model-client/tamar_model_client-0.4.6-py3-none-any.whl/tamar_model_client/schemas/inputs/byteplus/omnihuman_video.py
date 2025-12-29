from pydantic import BaseModel
from typing import Optional


class BytePlusOmniHumanVideoInput(BaseModel):
    """BytePlus OmniHuman 1.5 Video Generation 请求参数

    基于单张图像、音频文件生成多角色交互视频
    """
    image_url: str
    audio_url: str
    mask_url: Optional[str] = None
    seed: Optional[int] = None
    prompt: Optional[str] = None
    pe_fast_mode: Optional[bool] = None
    callback_url: Optional[str] = None
