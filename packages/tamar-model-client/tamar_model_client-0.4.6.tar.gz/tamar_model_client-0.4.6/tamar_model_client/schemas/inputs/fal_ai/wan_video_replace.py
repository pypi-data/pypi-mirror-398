from typing import Optional, Literal, Union
from pydantic import BaseModel

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class FalAIWanVideoReplaceInput(BaseModel):
    """Fal AI Wan Video Replace 请求参数

    Wan-Animate Replace 是一个可以将动画角色整合到参考视频中的模型，
    替换原始角色同时保留场景的光照和色调。
    """

    video_url: Union[str, TamarFileIdInput, dict]
    image_url: Union[str, TamarFileIdInput, dict]
    guidance_scale: Optional[float] = None
    resolution: Optional[Literal["480p", "580p", "720p"]] = None
    seed: Optional[int] = None
    num_inference_steps: Optional[int] = None
    enable_safety_checker: Optional[bool] = None
    enable_output_safety_checker: Optional[bool] = None
    shift: Optional[float] = None
    video_quality: Optional[Literal["low", "medium", "high", "maximum"]] = None
    video_write_mode: Optional[Literal["fast", "balanced", "small"]] = None
    return_frames_zip: Optional[bool] = None
    use_turbo: Optional[bool] = None
    model: Optional[str] = "wan-v2.2-14b"
    callback_url: Optional[str] = None

    model_config = {
        "arbitrary_types_allowed": True
    }
