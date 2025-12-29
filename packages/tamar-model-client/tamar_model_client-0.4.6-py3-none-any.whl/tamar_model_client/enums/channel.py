from enum import Enum


class Channel(str, Enum):
    """渠道枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VERTEXAI = "vertexai"
    AI_STUDIO = "ai-studio"
    OMNIHUMAN = "omnihuman"
    SEEDANCE = "seedance"

    # 默认的
    NORMAL = "normal"
