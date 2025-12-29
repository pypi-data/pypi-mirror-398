from enum import Enum


class ProviderType(str, Enum):
    """模型提供商类型枚举"""
    OPENAI = "openai"
    GOOGLE = "google"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    FREEPIK = "freepik"
    BYTEPLUS = "byteplus"
    FAL_AI = "fal-ai"
    BFL = "bfl"
    XFUSIONAI = "xfusionai"
    TUZI = "tuzi"
    KLING_AI = "kling-ai"
    DOUBAO = "doubao"
