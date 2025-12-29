from typing import Optional, Literal, Union, List
from pydantic import BaseModel, Field

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class KlingVideoElement(BaseModel):
    """Kling Video 元素配置 - 用于 O1 Reference-to-Video 指定视频中的角色或物体

    Reference in prompt as @Element1, @Element2, etc.
    Maximum 7 total (elements + reference images + start image).
    """

    reference_image_urls: List[Union[str, TamarFileIdInput, dict]] = Field(
        description="参考图像 URL 列表，用于定义角色或物体的外观"
    )
    frontal_image_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="正面图像 URL，用于更精确的角色识别"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }


class DynamicMask(BaseModel):
    """动态遮罩配置 - 用于运动笔刷控制"""

    mask_url: Union[str, TamarFileIdInput, dict] = Field(
        description="动态笔刷应用区域的遮罩图像 URL"
    )
    trajectories: Optional[List[dict]] = Field(
        default=None,
        description="运动轨迹列表，每个轨迹包含 x, y 坐标"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }


class FalAIKlingVideoInput(BaseModel):
    """Fal AI Kling Video 统一请求参数

    支持多种 Kling Video 模型：
    - O1 Reference-to-Video: 使用 prompt, image_urls, elements
    - Text-to-Video (v1/v2/v2.1/v2.5): 使用 prompt, duration, aspect_ratio, negative_prompt, cfg_scale
    - Image-to-Video (v1/v2/v2.1/v2.5): 使用 prompt, image_url, duration, negative_prompt, cfg_scale
    - Pro Image-to-Video: 额外支持 tail_image_url
    - Advanced: 支持 static_mask_url, dynamic_masks, camera_control
    """

    # === 核心参数（所有模型通用）===
    prompt: str = Field(
        description="视频生成的详细文本描述。对于 O1 模型，使用 @Element1, @Image1 等引用元素和图像"
    )

    # === O1 Reference-to-Video 专用参数 ===
    image_urls: Optional[List[Union[str, TamarFileIdInput, dict]]] = Field(
        default=None,
        description="[O1] 参考图像 URL 列表，在 prompt 中引用为 @Image1, @Image2 等。最多7张（elements + images）"
    )
    elements: Optional[List[KlingVideoElement]] = Field(
        default=None,
        description="[O1] 要在视频中包含的角色或物体元素列表，在 prompt 中引用为 @Element1, @Element2 等"
    )

    # === Image-to-Video 参数 ===
    image_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Video] 用作视频起始帧的单个图像 URL"
    )
    tail_image_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Pro Image-to-Video] 用作视频结束帧的图像 URL"
    )

    # === 时长和尺寸参数 ===
    duration: Optional[Literal["5", "10"]] = Field(
        default="5",
        description="视频时长（秒），支持 5 秒或 10 秒"
    )
    aspect_ratio: Optional[Literal["16:9", "9:16", "1:1"]] = Field(
        default="16:9",
        description="视频宽高比，支持 16:9（横屏）、9:16（竖屏）、1:1（正方形）"
    )

    # === 生成控制参数 ===
    negative_prompt: Optional[str] = Field(
        default=None,
        description="负面提示词，描述不希望出现的内容。默认：'blur, distort, and low quality'"
    )
    cfg_scale: Optional[float] = Field(
        default=None,
        description="CFG (Classifier Free Guidance) 缩放系数，控制模型对提示词的遵循程度。默认：0.5"
    )

    # === 高级控制参数 ===
    static_mask_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Advanced] 静态笔刷应用区域的遮罩图像 URL（用户使用运动笔刷创建的遮罩）"
    )
    dynamic_masks: Optional[List[DynamicMask]] = Field(
        default=None,
        description="[Advanced] 动态遮罩列表，用于精确控制视频中的运动"
    )
    camera_control: Optional[str] = Field(
        default=None,
        description="[V1 Text-to-Video] 相机控制参数：down_back, forward_up, right_turn_forward, left_turn_forward"
    )

    # === 内部参数 ===
    model: Optional[str] = Field(
        default="kling-video-o1",
        description="模型名称，用于选择对应的 endpoint"
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="任务完成后的回调 URL"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }
