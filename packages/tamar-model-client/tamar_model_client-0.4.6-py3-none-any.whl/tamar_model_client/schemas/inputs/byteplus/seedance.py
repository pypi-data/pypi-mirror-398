"""
BytePlus SeeDANCE 1.5 Pro Schemas

官方文档: https://docs.byteplus.com/en/docs/ModelArk/1520757
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """Content 数组项（文本或图像）"""

    type: Literal["text", "image_url"] = Field(
        ...,
        description="内容类型：text 或 image_url"
    )

    text: Optional[str] = Field(
        None,
        description="文本内容（type=text 时使用）。可在文本后添加 --[参数] 控制视频规格"
    )

    image_url: Optional[Dict[str, str]] = Field(
        None,
        description="图像URL（type=image_url 时使用）。格式: {'url': 'https://...'}"
    )


class BytePlusSeeDANCEInput(BaseModel):
    """BytePlus SeeDANCE 1.5 Pro 请求参数

    官方文档: https://docs.byteplus.com/en/docs/ModelArk/1520757

    核心功能：文本生成视频 (Text-to-Video) 或 图像生成视频 (Image-to-Video)
    """

    # ==================== 基础参数 ====================
    model: str = Field(
        "seedance-1.5-pro",
        description="模型 ID。可以是模型 ID 或 endpoint ID"
    )

    content: List[ContentItem] = Field(
        ...,
        description=(
            "输入文本和图像信息的对象数组。\n"
            "支持格式：\n"
            "1. Text-to-Video: [{'type': 'text', 'text': 'your prompt'}]\n"
            "2. Image-to-Video: [{'type': 'image_url', 'image_url': {'url': '...'}}]\n"
            "3. 图文结合: [{'type': 'text', 'text': '...'}, {'type': 'image_url', 'image_url': {'url': '...'}}]"
        )
    )

    # ==================== 任务配置参数 ====================
    callback_url: Optional[str] = Field(
        None,
        description=(
            "回调通知地址。当视频生成任务状态变化时，Ark 会向此地址发送回调请求。\n"
            "回调内容结构与查询任务信息的响应体一致。\n"
            "回调状态：queued（队列中）、running（运行中）、succeeded（成功）、failed（失败）、expired（超时）"
        )
    )

    return_last_frame: Optional[bool] = Field(
        None,
        description=(
            "是否返回生成视频的最后一帧图像（PNG 格式，无水印）。\n"
            "用于生成连续视频：将前一个视频的最后一帧作为下一个视频的首帧。\n"
            "默认值: false"
        )
    )

    service_tier: Optional[str] = Field(
        None,
        description=(
            "服务层级。\n"
            "- default: 在线推理模式（低延迟，较低 RPM/并发配额）\n"
            "- flex: 离线推理模式（高 TPD 配额，价格为在线模式的 50%）\n"
            "注意：提交后不支持修改服务层级。默认值: default"
        )
    )

    execution_expires_after: Optional[int] = Field(
        None,
        description=(
            "任务过期时间阈值（秒）。从任务创建时间（created_at）开始计算。\n"
            "超过此时间未完成的任务将自动终止并标记为 expired。\n"
            "默认值: 172800（48 小时）\n"
            "有效范围: [3600, 259200]"
        )
    )

    generate_audio: Optional[bool] = Field(
        None,
        description=(
            "控制生成的视频是否包含与画面同步的音频（仅 Seedance 1.5 pro 支持）。\n"
            "- true: 输出带音频的视频（根据提示词和画面自动生成配音、音效或背景音乐）\n"
            "- false: 输出静音视频\n"
            "默认值: true"
        )
    )

    # ==================== 视频规格参数（文本命令） ====================
    resolution: Optional[str] = Field(
        None,
        description=(
            "视频分辨率。可选值: 480p, 720p, 1080p（部分模型不支持）\n"
            "默认值: Seedance 1.5 pro/1.0 lite 为 720p，1.0 pro/pro-fast 为 1080p\n"
            "文本命令缩写: --rs"
        )
    )

    ratio: Optional[str] = Field(
        None,
        description=(
            "视频宽高比。可选值: 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive（自动选择）\n"
            "默认值: Text-to-Video 为 16:9，Image-to-Video 为 adaptive\n"
            "注意: Seedance 1.5 pro 的 adaptive 模式会根据提示词智能选择\n"
            "文本命令缩写: --rt"
        )
    )

    duration: Optional[int] = Field(
        None,
        description=(
            "视频时长（秒）。有效范围: 2~12\n"
            "特殊值: -1 表示由模型自动选择 [4, 12] 范围内的时长（整秒）\n"
            "默认值: 5\n"
            "注意: 与 frames 二选一，frames 优先\n"
            "文本命令缩写: --dur"
        )
    )

    frames: Optional[int] = Field(
        None,
        description=(
            "视频帧数（Seedance 1.5 pro 不支持）。可用于生成非整秒时长的视频。\n"
            "计算公式: 帧数 = 时长 × 24\n"
            "有效范围: [29, 289] 且符合格式 25 + 4n（n 为正整数）\n"
            "注意: 与 duration 二选一，frames 优先\n"
            "文本命令缩写: --frames"
        )
    )

    framepersecond: Optional[int] = Field(
        None,
        description=(
            "视频帧率（每秒显示的图像数）。可选值: 24\n"
            "默认值: 24\n"
            "文本命令缩写: --fps"
        )
    )

    seed: Optional[int] = Field(
        None,
        description=(
            "随机种子，控制输出内容的随机性。有效范围: [-1, 2^32-1]\n"
            "默认值: -1（使用随机数）\n"
            "注意: 相同种子和请求生成相似但不一定完全相同的输出\n"
            "文本命令缩写: --seed"
        )
    )

    camerafixed: Optional[bool] = Field(
        None,
        description=(
            "是否固定相机（参考图生成视频不支持）。\n"
            "- true: 固定相机（平台会在提示词中追加固定相机指令，但不保证效果）\n"
            "- false: 不固定相机\n"
            "默认值: false\n"
            "文本命令缩写: --cf"
        )
    )

    watermark: Optional[bool] = Field(
        None,
        description=(
            "是否在输出视频中添加水印。\n"
            "- true: 添加水印\n"
            "- false: 不添加水印\n"
            "默认值: false\n"
            "文本命令缩写: --wm"
        )
    )

    # ==================== 系统内部参数 ====================
    enable_async_task: Optional[bool] = Field(
        True,
        description="是否启用异步任务处理（视频生成为长时间任务，建议启用）"
    )
