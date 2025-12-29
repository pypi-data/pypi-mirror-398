from typing import Optional, Literal, Union
from pydantic import BaseModel

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class FalAIQwenImageLayeredInput(BaseModel):
    """Fal AI Qwen Image Layered 请求参数"""

    prompt: str
    image_url: Union[str, TamarFileIdInput]
    negative_prompt: Optional[str] = ""
    num_inference_steps: Optional[int] = 28
    guidance_scale: Optional[float] = 5.0
    seed: Optional[int] = None
    sync_mode: Optional[bool] = False
    num_layers: Optional[int] = 4
    enable_safety_checker: Optional[bool] = True
    output_format: Optional[Literal["png", "webp"]] = "png"
    acceleration: Optional[Literal["none", "regular", "high"]] = "regular"

    model_config = {
        "arbitrary_types_allowed": True
    }
