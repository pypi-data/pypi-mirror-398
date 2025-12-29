"""Fal AI SAM-3 APIs Schema

SAM-3 是 Fal AI 的统一分割模型，支持图像和视频的分割、3D重建等功能。

图像API (6个):
- 3D Align: https://fal.ai/models/fal-ai/sam-3/3d-align/api
- 3D Body: https://fal.ai/models/fal-ai/sam-3/3d-body/api
- 3D Objects: https://fal.ai/models/fal-ai/sam-3/3d-objects/api
- Image Segmentation: https://fal.ai/models/fal-ai/sam-3/image/api
- Image RLE: https://fal.ai/models/fal-ai/sam-3/image-rle/api
- Image Embed: https://fal.ai/models/fal-ai/sam-3/image/embed/api

视频API (2个):
- Video Segmentation: https://fal.ai/models/fal-ai/sam-3/video/api
- Video RLE: https://fal.ai/models/fal-ai/sam-3/video-rle/api
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from enum import IntEnum

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


# ========================================
# Common Types
# ========================================

class LabelEnum(IntEnum):
    """Point prompt label"""
    BACKGROUND = 0
    FOREGROUND = 1


class BoxPromptBase(BaseModel):
    """基础框提示 (用于 3D Objects 和 Video)"""
    x_min: int = Field(..., description="框的最小 X 坐标")
    y_min: int = Field(..., description="框的最小 Y 坐标")
    x_max: int = Field(..., description="框的最大 X 坐标")
    y_max: int = Field(..., description="框的最大 Y 坐标")
    object_id: Optional[int] = Field(default=None, description="可选的物体标识符")


class BoxPrompt(BoxPromptBase):
    """框提示 (支持帧索引，用于 Image 和 Video RLE)"""
    frame_index: Optional[int] = Field(default=None, description="要交互的帧索引")


class PointPromptBase(BaseModel):
    """基础点提示 (用于 3D Objects 和 Video)"""
    x: int = Field(..., description="提示的 X 坐标")
    y: int = Field(..., description="提示的 Y 坐标")
    label: LabelEnum = Field(..., description="1 表示前景，0 表示背景")
    object_id: Optional[int] = Field(default=None, description="可选的物体标识符")


class PointPrompt(PointPromptBase):
    """点提示 (支持帧索引，用于 Image 和 Video RLE)"""
    frame_index: Optional[int] = Field(default=None, description="要交互的帧索引")


# ========================================
# SAM-3 3D Align API
# ========================================

class SAM3DAlignInput(BaseModel):
    """SAM-3 3D Align 输入 Schema - 人体网格对齐

    将 SAM-3D Body 生成的人体网格与原始图像的深度信息对齐。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-3d-align 或 sam3-3d-align
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="用于 MoGe 深度估计的原始图像 URL 或 file_id")
    body_mesh_url: Union[str, TamarFileIdInput, dict] = Field(..., description="SAM-3D Body 生成的网格文件 URL (.ply 或 .glb) 或 file_id")

    # 可选参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    body_mask_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(default=None, description="人体遮罩图像 URL 或 file_id。如果未提供，使用完整图像")
    object_mesh_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(default=None, description="可选的 SAM-3D Object 网格 URL (.glb) 或 file_id，用于创建组合场景")
    focal_length: Optional[float] = Field(default=None, description="来自 SAM-3D Body 元数据的焦距。如果未提供，从 MoGe 估计")

    # 内部参数
    model: Optional[str] = Field(default="sam-3-3d-align", description="模型名称")
    callback_url: Optional[str] = Field(None, description="异步任务完成后的回调地址")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 3D Body API
# ========================================

class SAM3DBodyInput(BaseModel):
    """SAM-3 3D Body 输入 Schema - 3D人体生成

    从单张图像生成 3D 人体网格，包含关键点和相机参数。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-3d-body 或 sam3-3d-body
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="包含人体的图像 URL 或 file_id")

    # 可选参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    mask_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="可选的二值遮罩图像 URL 或 file_id (白色=人，黑色=背景)。提供时，跳过自动人体检测并使用此遮罩。边界框从遮罩自动计算"
    )
    export_meshes: Optional[bool] = Field(default=True, description="为每个人导出单独的网格文件 (.ply)")
    include_3d_keypoints: Optional[bool] = Field(default=True, description="在 GLB 网格中包含 3D 关键点标记（球体）用于可视化")

    # 内部参数
    model: Optional[str] = Field(default="sam-3-3d-body", description="模型名称")
    callback_url: Optional[str] = Field(None, description="异步任务完成后的回调地址")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 3D Objects API
# ========================================

class SAM3DObjectsInput(BaseModel):
    """SAM-3 3D Objects 输入 Schema - 3D物体重建

    从单张图像重建 3D 物体，支持多物体场景。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-3d-objects 或 sam3-3d-objects
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要进行 3D 重建的图像 URL 或 file_id")

    # 可选参数 - 分割 (支持URL字符串、file_id字典或TamarFileIdInput)
    mask_urls: Optional[List[Union[str, TamarFileIdInput, dict]]] = Field(
        default=None,
        description="可选的遮罩 URL 或 file_id 列表（每个物体一个）。如果未提供，使用 prompt/point_prompts/box_prompts 自动分割，或使用整个图像"
    )
    prompt: Optional[str] = Field(default="car", description="未提供遮罩时用于自动分割的文本提示词（例如 'chair', 'lamp'）")
    point_prompts: Optional[List[PointPromptBase]] = Field(default=None, description="未提供遮罩时用于自动分割的点提示")
    box_prompts: Optional[List[BoxPromptBase]] = Field(
        default=None,
        description="未提供遮罩时用于自动分割的框提示。支持多个框 - 每个框产生一个单独的物体遮罩用于 3D 重建"
    )

    # 可选参数 - 高级 (支持URL字符串、file_id字典或TamarFileIdInput)
    seed: Optional[int] = Field(default=None, description="用于可重现性的随机种子")
    pointmap_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(
        default=None,
        description="可选的外部点云/深度数据 URL 或 file_id (NPY 或 NPZ 格式)，用于改进 3D 重建的深度估计"
    )

    # 内部参数
    model: Optional[str] = Field(default="sam-3-3d-objects", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 Image Segmentation API
# ========================================

class SAM3ImageInput(BaseModel):
    """SAM-3 Image Segmentation 输入 Schema - 图像分割

    对图像进行智能分割，支持文本、点和框提示。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-image 或 sam3-image
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要分割的图像 URL 或 file_id")

    # 可选参数 - 提示
    prompt: Optional[str] = Field(default="wheel", description="分割的文本提示词")
    point_prompts: Optional[List[PointPrompt]] = Field(default=None, description="点提示列表")
    box_prompts: Optional[List[BoxPrompt]] = Field(
        default=None,
        description="框提示坐标 (x_min, y_min, x_max, y_max)。支持多个框 - 使用 object_id 对同一物体的框分组，或留空表示不同物体"
    )

    # 可选参数 - 输出设置
    apply_mask: Optional[bool] = Field(default=True, description="在图像上应用遮罩")
    sync_mode: Optional[bool] = Field(default=False, description="如果为 True，媒体将作为 data URI 返回")
    output_format: Optional[Literal["jpeg", "png", "webp"]] = Field(default="png", description="生成图像的格式")

    # 可选参数 - 多遮罩
    return_multiple_masks: Optional[bool] = Field(default=False, description="如果为 True，上传并返回由 max_masks 定义的多个生成的遮罩")
    max_masks: Optional[int] = Field(default=3, description="启用 return_multiple_masks 时返回的最大遮罩数")

    # 可选参数 - 元数据
    include_scores: Optional[bool] = Field(default=False, description="是否包含遮罩置信度分数")
    include_boxes: Optional[bool] = Field(default=False, description="是否为每个遮罩包含边界框（如果可用）")

    # 内部参数
    model: Optional[str] = Field(default="sam-3-image", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 Image RLE API
# ========================================

class SAM3ImageRLEInput(BaseModel):
    """SAM-3 Image RLE 输入 Schema - RLE编码分割

    与 SAM3ImageInput 相同，但返回 RLE 编码而不是图像文件。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-image-rle 或 sam3-image-rle
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要分割的图像 URL 或 file_id")

    # 可选参数 - 提示
    prompt: Optional[str] = Field(default="wheel", description="分割的文本提示词")
    point_prompts: Optional[List[PointPrompt]] = Field(default=None, description="点提示列表")
    box_prompts: Optional[List[BoxPrompt]] = Field(
        default=None,
        description="框提示坐标 (x_min, y_min, x_max, y_max)。支持多个框 - 使用 object_id 对同一物体的框分组，或留空表示不同物体"
    )

    # 可选参数 - 输出设置
    apply_mask: Optional[bool] = Field(default=True, description="在图像上应用遮罩")
    sync_mode: Optional[bool] = Field(default=False, description="如果为 True，媒体将作为 data URI 返回")
    output_format: Optional[Literal["jpeg", "png", "webp"]] = Field(default="png", description="生成图像的格式")

    # 可选参数 - 多遮罩
    return_multiple_masks: Optional[bool] = Field(default=False, description="如果为 True，上传并返回由 max_masks 定义的多个生成的遮罩")
    max_masks: Optional[int] = Field(default=3, description="启用 return_multiple_masks 时返回的最大遮罩数")

    # 可选参数 - 元数据
    include_scores: Optional[bool] = Field(default=False, description="是否包含遮罩置信度分数")
    include_boxes: Optional[bool] = Field(default=False, description="是否为每个遮罩包含边界框（如果可用）")

    # 内部参数
    model: Optional[str] = Field(default="sam-3-image-rle", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 Image Embed API
# ========================================

class SAM3ImageEmbedInput(BaseModel):
    """SAM-3 Image Embed 输入 Schema - 图像嵌入

    生成图像嵌入向量，用于相似度搜索和下游任务。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: image-segmentation
    - model: sam-3-image-embed 或 sam3-image-embed
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    image_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要嵌入的图像 URL 或 file_id")

    # 内部参数
    model: Optional[str] = Field(default="sam-3-image-embed", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 Video Segmentation API
# ========================================

class SAM3VideoInput(BaseModel):
    """SAM-3 Video Segmentation 输入 Schema - 视频分割

    对视频进行智能分割和跟踪，支持文本、点和框提示。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: video-segmentation
    - model: sam-3-video 或 sam3-video
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    video_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要分割的视频 URL 或 file_id")

    # 可选参数 - 提示
    prompt: Optional[str] = Field(default="", description="分割的文本提示词。使用逗号跟踪多个物体（例如 'person, cloth'）")
    point_prompts: Optional[List[PointPromptBase]] = Field(default=None, description="点提示列表")
    box_prompts: Optional[List[BoxPromptBase]] = Field(default=None, description="框提示坐标列表 (x_min, y_min, x_max, y_max)")

    # 可选参数 - 设置
    apply_mask: Optional[bool] = Field(default=True, description="在视频上应用遮罩")
    detection_threshold: Optional[float] = Field(
        default=0.5,
        description="检测置信度阈值 (0.0-1.0)。较低 = 更多检测但更不精确"
    )

    # 内部参数
    model: Optional[str] = Field(default="sam-3-video", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========================================
# SAM-3 Video RLE API
# ========================================

class SAM3VideoRLEInput(BaseModel):
    """SAM-3 Video RLE 输入 Schema - 视频RLE分割

    与 Video Segmentation 类似，但支持帧特定提示和初始遮罩。

    gRPC 调用参数:
    - provider: fal-ai
    - channel: normal
    - invoke_type: video-segmentation
    - model: sam-3-video-rle 或 sam3-video-rle
    """

    # 必填参数 (支持URL字符串、file_id字典或TamarFileIdInput)
    video_url: Union[str, TamarFileIdInput, dict] = Field(..., description="要分割的视频 URL 或 file_id")

    # 可选参数 - 初始遮罩 (支持URL字符串、file_id字典或TamarFileIdInput)
    mask_url: Optional[Union[str, TamarFileIdInput, dict]] = Field(default=None, description="要初始应用的遮罩 URL 或 file_id")
    frame_index: Optional[int] = Field(default=None, description="提供 mask_url 时用于初始交互的帧索引")

    # 可选参数 - 提示 (支持帧)
    prompt: Optional[str] = Field(default="", description="分割的文本提示词。使用逗号跟踪多个物体（例如 'person, cloth'）")
    point_prompts: Optional[List[PointPrompt]] = Field(default=None, description="带帧索引的点提示列表")
    box_prompts: Optional[List[BoxPrompt]] = Field(default=None, description="带可选 frame_index 的框提示列表")

    # 可选参数 - 设置
    apply_mask: Optional[bool] = Field(default=None, description="在视频上应用遮罩")
    boundingbox_zip: Optional[bool] = Field(default=None, description="返回每帧边界框叠加作为 zip 存档")
    detection_threshold: Optional[float] = Field(
        default=0.5,
        description="检测置信度阈值 (0.0-1.0)。较低 = 更多检测但更不精确。默认：现有物体 0.5，新物体 0.7。如果文本提示失败，尝试 0.2-0.3"
    )

    # 内部参数
    model: Optional[str] = Field(default="sam-3-video-rle", description="模型名称")
    callback_url: Optional[str] = Field(default=None, description="任务完成后的回调 URL")
    enable_async_task: bool = Field(False, description="是否开启异步任务模式（默认 False）")

    model_config = {
        "arbitrary_types_allowed": True
    }
