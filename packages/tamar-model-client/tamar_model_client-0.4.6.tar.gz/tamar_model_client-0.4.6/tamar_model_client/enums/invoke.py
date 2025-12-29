from enum import Enum


class InvokeType(str, Enum):
    """模型调用类型枚举"""
    RESPONSES = "responses"
    CHAT_COMPLETIONS = "chat-completions"
    MESSAGES = "messages"

    GENERATION = "generation"  # 生成类，默认的值
    IMAGE_GENERATION = "image-generation"
    IMAGE_EDIT_GENERATION = "image-edit-generation"
    IMAGE_LAYER_GENERATION = "image-layer-generation"  # 图像分层分解
    IMAGE_GENERATION_GENAI = "image-generation-genai"  # GenAI SDK图像生成
    VIDEO_GENERATION = "video-generation"  # 视频生成（通用）
    VIDEO_GENERATION_GENAI = "video-generation-genai"  # GenAI SDK视频生成
    VIDEO_EDIT_GENERATION = "video-edit-generation"  # 视频编辑
    IMAGE_UPSCALER = "image-upscaler"  # 图像超分辨率/放大
    IMAGE_SEGMENTATION = "image-segmentation"  # SAM-3 图像分割/3D重建
    VIDEO_SEGMENTATION = "video-segmentation"  # SAM-3 视频分割
