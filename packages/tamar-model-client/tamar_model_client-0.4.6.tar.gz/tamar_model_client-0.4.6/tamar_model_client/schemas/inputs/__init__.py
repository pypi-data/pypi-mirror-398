# Re-export all classes for backward compatibility
from tamar_model_client.schemas.inputs.base import (
    UserContext,
    TamarFileIdInput,
    BaseRequest,
)
# OpenAI
from tamar_model_client.schemas.inputs.openai.responses import OpenAIResponsesInput
from tamar_model_client.schemas.inputs.openai.chat_completions import OpenAIChatCompletionsInput
from tamar_model_client.schemas.inputs.openai.images import OpenAIImagesInput, OpenAIImagesEditInput
from tamar_model_client.schemas.inputs.openai.videos import OpenAIVideosInput
# Google
from tamar_model_client.schemas.inputs.google.genai import GoogleGenAiInput
from tamar_model_client.schemas.inputs.google.genai_images import GoogleGenAIImagesInput
from tamar_model_client.schemas.inputs.google.genai_videos import GoogleGenAiVideosInput
from tamar_model_client.schemas.inputs.google.vertexai_images import GoogleVertexAIImagesInput
# Anthropic
from tamar_model_client.schemas.inputs.anthropic.messages import AnthropicMessagesInput
# Freepik
from tamar_model_client.schemas.inputs.freepik.image_upscaler import FreepikImageUpscalerInput
# BytePlus
from tamar_model_client.schemas.inputs.byteplus.omnihuman_video import BytePlusOmniHumanVideoInput
from tamar_model_client.schemas.inputs.byteplus.seedance import BytePlusSeeDANCEInput, ContentItem
# Fal AI
from tamar_model_client.schemas.inputs.fal_ai.qwen_images import FalAIQwenImageEditInput
from tamar_model_client.schemas.inputs.fal_ai.qwen_image_layered import FalAIQwenImageLayeredInput
from tamar_model_client.schemas.inputs.fal_ai.wan_video_replace import FalAIWanVideoReplaceInput
from tamar_model_client.schemas.inputs.fal_ai.z_images import FalAIZImageInput, LoRAInput, ImageSizeCustom
from tamar_model_client.schemas.inputs.fal_ai.sam3 import (
    SAM3DAlignInput,
    SAM3DBodyInput,
    SAM3DObjectsInput,
    SAM3ImageInput,
    SAM3ImageRLEInput,
    SAM3ImageEmbedInput,
    SAM3VideoInput,
    SAM3VideoRLEInput,
    LabelEnum,
    BoxPromptBase,
    BoxPrompt,
    PointPromptBase,
    PointPrompt,
)
# BFL
from tamar_model_client.schemas.inputs.bfl import BFLInput, BFLFlux2Input
# Azure
from tamar_model_client.schemas.inputs.azure import AzureFluxImageInput, AzureFluxImageEditInput
# Unified
from tamar_model_client.schemas.inputs.unified import (
    ModelRequestInput,
    ModelRequest,
    BatchModelRequestItem,
    BatchModelRequest,
)

__all__ = [
    # Base
    "UserContext",
    "TamarFileIdInput",
    "BaseRequest",
    # OpenAI
    "OpenAIResponsesInput",
    "OpenAIChatCompletionsInput",
    "OpenAIImagesInput",
    "OpenAIImagesEditInput",
    "OpenAIVideosInput",
    # Google
    "GoogleGenAiInput",
    "GoogleVertexAIImagesInput",
    "GoogleGenAIImagesInput",
    "GoogleGenAiVideosInput",
    # Anthropic
    "AnthropicMessagesInput",
    # Freepik
    "FreepikImageUpscalerInput",
    # BytePlus
    "BytePlusOmniHumanVideoInput",
    "BytePlusSeeDANCEInput",
    "ContentItem",
    # Fal AI
    "FalAIQwenImageEditInput",
    "FalAIQwenImageLayeredInput",
    "FalAIWanVideoReplaceInput",
    "FalAIZImageInput",
    "LoRAInput",
    "ImageSizeCustom",
    # Fal AI SAM-3
    "SAM3DAlignInput",
    "SAM3DBodyInput",
    "SAM3DObjectsInput",
    "SAM3ImageInput",
    "SAM3ImageRLEInput",
    "SAM3ImageEmbedInput",
    "SAM3VideoInput",
    "SAM3VideoRLEInput",
    "LabelEnum",
    "BoxPromptBase",
    "BoxPrompt",
    "PointPromptBase",
    "PointPrompt",
    # BFL
    "BFLInput",
    "BFLFlux2Input",
    # Azure
    "AzureFluxImageInput",
    "AzureFluxImageEditInput",
    # Unified
    "ModelRequestInput",
    "ModelRequest",
    "BatchModelRequestItem",
    "BatchModelRequest",
]
