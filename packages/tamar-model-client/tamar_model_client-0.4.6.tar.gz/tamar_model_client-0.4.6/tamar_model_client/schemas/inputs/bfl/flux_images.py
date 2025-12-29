from typing import Optional, Literal, Union
from pydantic import BaseModel, Field

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class BFLInput(BaseModel):
    """BFL 全系列图像生成通用请求参数

    支持 Black Forest Labs 的所有 FLUX 模型：
    - Text-to-Image: 使用 prompt 生成图像
    - Image-to-Image/Editing: 使用 prompt + input_image(s) 编辑图像
    - Multi-Reference: 支持最多 8 张输入图像（FLUX.2 系列）

    支持的模型系列：
    1. FLUX.2 系列:
       - flux-2-pro: 高质量图像生成（8个input_image, width/height）
       - flux-2-flex: 灵活控制（8个input_image, width/height, guidance/steps）

    2. FLUX KONTEXT 系列:
       - flux-kontext-pro: 上下文感知生成（4个input_image, aspect_ratio）
       - flux-kontext-max: 最大上下文（4个input_image, aspect_ratio）

    3. FLUX 1.1 系列:
       - flux-1.1-pro: 高性能生成（image_prompt, width/height）

    官方文档:
    - FLUX.2 PRO: https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[pro]
    - FLUX.2 FLEX: https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[flex]
    - FLUX KONTEXT PRO: https://docs.bfl.ai/api-reference/models/edit-or-create-an-image-with-flux-kontext-pro
    - FLUX KONTEXT MAX: https://docs.bfl.ai/api-reference/models/edit-or-create-an-image-with-flux-kontext-max
    - FLUX 1.1 PRO: https://docs.bfl.ai/api-reference/models/generate-an-image-with-flux-11-[pro]
    """

    # === 核心参数 ===
    prompt: str = Field(
        description="文本描述，用于生成或编辑图像"
    )

    image_prompt: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[FLUX 1.1 only] 图像提示词，用于引导生成（URL 或 TamarFileIdInput）"
    )

    # === 图像编辑参数（最多支持 8 张输入图像）===
    input_image: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 1 张输入图像，用于图像编辑（URL 或 TamarFileIdInput）"
    )
    input_image_2: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 2 张输入图像（URL 或 TamarFileIdInput）"
    )
    input_image_3: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 3 张输入图像（URL 或 TamarFileIdInput）"
    )
    input_image_4: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 4 张输入图像（URL 或 TamarFileIdInput）"
    )
    input_image_5: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 5 张输入图像（URL 或 TamarFileIdInput）- Experimental Multiref"
    )
    input_image_6: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 6 张输入图像（URL 或 TamarFileIdInput）- Experimental Multiref"
    )
    input_image_7: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 7 张输入图像（URL 或 TamarFileIdInput）- Experimental Multiref"
    )
    input_image_8: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="[Image-to-Image] 第 8 张输入图像（URL 或 TamarFileIdInput）- Experimental Multiref"
    )

    # === 生成控制参数 ===
    seed: Optional[int] = Field(
        default=None,
        description="随机种子，用于可复现的生成结果"
    )

    # 尺寸参数：width/height（FLUX.2, FLUX 1.1）或 aspect_ratio（FLUX KONTEXT）
    width: Optional[int] = Field(
        default=None,
        description="[FLUX.2, FLUX 1.1] 生成图像的宽度（像素）。FLUX.2最小64，FLUX 1.1范围256-1440且必须是32的倍数",
        ge=64
    )
    height: Optional[int] = Field(
        default=None,
        description="[FLUX.2, FLUX 1.1] 生成图像的高度（像素）。FLUX.2最小64，FLUX 1.1范围256-1440且必须是32的倍数",
        ge=64
    )
    aspect_ratio: Optional[str] = Field(
        default=None,
        description="[FLUX KONTEXT only] 宽高比，例如 '16:9', '1:1', '4:3' 等"
    )

    safety_tolerance: Optional[int] = Field(
        default=2,
        description="安全容忍度，范围 0-6（FLUX KONTEXT/1.1）或 0-5（FLUX.2），数值越高越宽松。默认：2",
        ge=0,
        le=6
    )
    output_format: Optional[Literal["jpeg", "png"]] = Field(
        default="jpeg",
        description="输出图像格式，支持 'jpeg' 或 'png'。默认：jpeg"
    )

    # === 高级控制参数 ===
    prompt_upsampling: Optional[bool] = Field(
        default=None,
        description="是否启用 prompt 增强。FLUX.2 FLEX默认true，FLUX KONTEXT/1.1默认false"
    )
    guidance: Optional[float] = Field(
        default=5.0,
        description="[FLEX only] CFG 引导强度，范围 1.5-10。默认：5（仅 flux-2-flex 支持）",
        ge=1.5,
        le=10.0
    )
    steps: Optional[int] = Field(
        default=50,
        description="[FLEX only] 推理步数，范围 1-50。默认：50（仅 flux-2-flex 支持）",
        ge=1,
        le=50
    )

    # === Webhook 回调参数 ===
    webhook_url: Optional[str] = Field(
        default=None,
        description="任务完成后的 Webhook 回调 URL"
    )
    webhook_secret: Optional[str] = Field(
        default=None,
        description="Webhook 认证密钥"
    )

    # === 内部参数 ===
    model: Optional[str] = Field(
        default="flux-2-pro",
        description="模型名称，用于选择对应的 endpoint"
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="任务完成后的回调 URL（内部使用）"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }


# 保持向后兼容的别名
BFLFlux2Input = BFLInput
