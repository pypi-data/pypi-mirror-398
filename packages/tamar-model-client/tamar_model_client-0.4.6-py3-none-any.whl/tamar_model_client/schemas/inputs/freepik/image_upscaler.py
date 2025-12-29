from pydantic import BaseModel
from typing import Optional, Literal


class FreepikImageUpscalerInput(BaseModel):
    image: str
    scale_factor: int = 2
    sharpen: int = 7
    smart_grain: int = 7
    ultra_detail: int = 30
    flavor: Literal["sublime", "photo", "photo_denoiser"] = "sublime"
    callback_url: Optional[str] = None
