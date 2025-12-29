"""Fal AI Z-Image Schema

Supports both standard and LoRA versions:
- Standard: https://fal.ai/models/fal-ai/z-image/turbo/api
- LoRA: https://fal.ai/models/fal-ai/z-image/turbo/lora/api
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal, Dict, Any


class ImageSizeCustom(BaseModel):
    """自定义图像尺寸"""
    width: int = Field(default=512, description="图像宽度")
    height: int = Field(default=512, description="图像高度")


class LoRAInput(BaseModel):
    """LoRA 权重输入（最多 3 个）"""
    path: str = Field(..., description="LoRA 模型路径或 URL")
    scale: float = Field(default=1.0, ge=0.0, le=4.0, description="LoRA 权重缩放系数（0.0 到 4.0）")


class FalAIZImageInput(BaseModel):
    """Fal AI Z-Image 输入 Schema（支持标准版和 LoRA 版）"""

    # 必填参数
    prompt: str = Field(..., description="生成图像的文本提示词")

    # 可选 - 图像尺寸
    image_size: Optional[Union[
        Literal[
            "square_hd",
            "square",
            "portrait_4_3",
            "portrait_16_9",
            "landscape_4_3",
            "landscape_16_9"
        ],
        ImageSizeCustom,
        Dict[str, Any]  # 支持字典形式
    ]] = Field(default="landscape_4_3", description="生成图像的尺寸")

    # 可选 - 生成参数
    num_inference_steps: Optional[int] = Field(default=8, ge=1, le=8, description="推理步骤数（1-8）")
    seed: Optional[int] = Field(default=None, description="随机种子，用于复现结果")
    num_images: Optional[int] = Field(default=1, ge=1, le=4, description="生成图像数量（1-4）")

    # 可选 - 安全和扩展
    enable_safety_checker: Optional[bool] = Field(default=True, description="启用安全检查器")
    enable_prompt_expansion: Optional[bool] = Field(default=False, description="启用提示词扩展（增加 0.0025 积分）")

    # 可选 - 输出格式
    output_format: Optional[Literal["jpeg", "png", "webp"]] = Field(default="png", description="输出图像格式")

    # 可选 - 加速
    acceleration: Optional[Literal["none", "regular", "high"]] = Field(default="none", description="加速级别")

    # 可选 - LoRA 权重（最多 3 个）
    loras: Optional[List[LoRAInput]] = Field(default=None, description="LoRA 权重列表（最多 3 个）")

    # 可选 - 高级
    sync_mode: Optional[bool] = Field(default=False, description="同步模式，返回 data URI（不保存在历史记录）")

    # 模型名称（用于内部路由）
    model: Optional[str] = Field(default="z-image-turbo", description="模型名称")

    # 回调地址
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "A beautiful sunset over mountains",
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 8,
                    "num_images": 1,
                    "output_format": "png"
                },
                {
                    "prompt": "A cyberpunk city street at night",
                    "image_size": {"width": 1024, "height": 768},
                    "loras": [
                        {
                            "path": "https://example.com/lora1.safetensors",
                            "scale": 0.8
                        }
                    ],
                    "num_inference_steps": 8,
                    "enable_safety_checker": True
                }
            ]
        }
    }
