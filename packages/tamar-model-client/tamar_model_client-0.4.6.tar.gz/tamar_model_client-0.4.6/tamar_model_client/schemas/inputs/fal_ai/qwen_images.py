from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class FalAIQwenImageEditInput(BaseModel):
    """Fal AI Qwen Image Edit Plus 请求参数"""

    image_urls: Union[List[str], List[TamarFileIdInput]]
    image_size: Optional[Union[
        Literal["square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"], Dict[
            str, Any]]] = None
    guidance_scale: Optional[float] = 1.0
    num_inference_steps: Optional[int] = 6
    acceleration: Optional[Literal["none", "regular"]] = "regular"
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    sync_mode: Optional[bool] = False
    enable_safety_checker: Optional[bool] = True
    output_format: Optional[Literal["png", "jpeg", "webp"]] = "png"
    num_images: Optional[int] = 1
    rotate_right_left: Optional[float] = 0.0
    move_forward: Optional[float] = 0.0
    vertical_angle: Optional[float] = 0.0
    wide_angle_lens: Optional[bool] = False
    lora_scale: Optional[float] = 1.25

    model_config = {
        "arbitrary_types_allowed": True
    }
