from openai import NotGiven
from pydantic import BaseModel
from typing import Any
import os, mimetypes


def convert_file_field(value: Any) -> Any:
    def is_file_like(obj):
        return hasattr(obj, "read") and callable(obj.read)

    def infer_mimetype(filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    def convert_item(item):
        if is_file_like(item):
            filename = os.path.basename(getattr(item, "name", "file.png"))
            content_type = infer_mimetype(filename)
            content = item.read()
            if hasattr(item, "seek"):
                item.seek(0)
            return (filename, content, content_type)
        elif isinstance(item, tuple):
            parts = list(item)
            if len(parts) > 1:
                maybe_file = parts[1]
                if is_file_like(maybe_file):
                    content = maybe_file.read()
                    if hasattr(maybe_file, "seek"):
                        maybe_file.seek(0)
                    parts[1] = content
                elif not isinstance(maybe_file, (bytes, bytearray)):
                    raise ValueError(f"Unsupported second element in tuple: {type(maybe_file)}")
            if len(parts) == 2:
                parts.append(infer_mimetype(os.path.basename(parts[0] or "file.png")))
            return tuple(parts)
        else:
            return item

    if value is None:
        return value
    elif isinstance(value, list):
        return [convert_item(v) for v in value]
    else:
        return convert_item(value)


def validate_fields_by_provider_and_invoke_type(
        instance: BaseModel,
        extra_allowed_fields: set[str],
        extra_required_fields: set[str] = set()
) -> BaseModel:
    """
    通用的字段校验逻辑，根据 provider 和 invoke_type 动态检查字段合法性和必填字段。
    适用于 ModelRequest 和 BatchModelRequestItem。
    """
    from tamar_model_client.enums import ProviderType, InvokeType
    from tamar_model_client.schemas.inputs import GoogleGenAiInput, OpenAIResponsesInput, OpenAIChatCompletionsInput, \
        OpenAIImagesInput, OpenAIImagesEditInput, OpenAIVideosInput, GoogleVertexAIImagesInput, GoogleGenAIImagesInput, \
        GoogleGenAiVideosInput, \
        AnthropicMessagesInput, \
        FreepikImageUpscalerInput, \
        BytePlusOmniHumanVideoInput, \
        BytePlusSeeDANCEInput, \
        FalAIQwenImageEditInput, \
        FalAIQwenImageLayeredInput, \
        FalAIWanVideoReplaceInput, \
        BFLInput, \
        AzureFluxImageInput, \
        AzureFluxImageEditInput
    from tamar_model_client.schemas.inputs.fal_ai import (
        FalAIKlingVideoInput, FalAIZImageInput,
        SAM3DAlignInput, SAM3DBodyInput, SAM3DObjectsInput,
        SAM3ImageInput, SAM3ImageRLEInput, SAM3ImageEmbedInput,
        SAM3VideoInput, SAM3VideoRLEInput
    )

    google_allowed = extra_allowed_fields | set(GoogleGenAiInput.model_fields)
    openai_responses_allowed = extra_allowed_fields | set(OpenAIResponsesInput.model_fields)
    openai_chat_allowed = extra_allowed_fields | set(OpenAIChatCompletionsInput.model_fields)
    openai_images_allowed = extra_allowed_fields | set(OpenAIImagesInput.model_fields)
    openai_images_edit_allowed = extra_allowed_fields | set(OpenAIImagesEditInput.model_fields)
    openai_videos_allowed = extra_allowed_fields | set(OpenAIVideosInput.model_fields)
    google_vertexai_images_allowed = extra_allowed_fields | set(GoogleVertexAIImagesInput.model_fields)
    google_genai_images_allowed = extra_allowed_fields | set(GoogleGenAIImagesInput.model_fields)
    google_genai_videos_allowed = extra_allowed_fields | set(GoogleGenAiVideosInput.model_fields)
    anthropic_messages_allowed = extra_allowed_fields | set(AnthropicMessagesInput.model_fields)
    freepik_image_upscaler_allowed = extra_allowed_fields | set(FreepikImageUpscalerInput.model_fields)
    byteplus_omnihuman_video_allowed = extra_allowed_fields | set(BytePlusOmniHumanVideoInput.model_fields)
    byteplus_seedance_video_allowed = extra_allowed_fields | set(BytePlusSeeDANCEInput.model_fields)
    # BytePlus 聚合 OmniHuman 和 SeeDANCE 的字段
    byteplus_video_allowed = byteplus_omnihuman_video_allowed | byteplus_seedance_video_allowed
    # FAL_AI Qwen Image Edit Plus
    fal_ai_qwen_image_edit_allowed = extra_allowed_fields | set(FalAIQwenImageEditInput.model_fields)
    # FAL_AI Qwen Image Layered
    fal_ai_qwen_image_layered_allowed = extra_allowed_fields | set(FalAIQwenImageLayeredInput.model_fields)
    fal_ai_wan_video_replace_allowed = extra_allowed_fields | set(FalAIWanVideoReplaceInput.model_fields)
    fal_ai_kling_video_allowed = extra_allowed_fields | set(FalAIKlingVideoInput.model_fields)
    fal_ai_z_image_allowed = extra_allowed_fields | set(FalAIZImageInput.model_fields)

    # SAM-3 所有图像 API 的字段（合并到 IMAGE_SEGMENTATION）
    sam3_image_allowed = (
        extra_allowed_fields
        | set(SAM3DAlignInput.model_fields)
        | set(SAM3DBodyInput.model_fields)
        | set(SAM3DObjectsInput.model_fields)
        | set(SAM3ImageInput.model_fields)
        | set(SAM3ImageRLEInput.model_fields)
        | set(SAM3ImageEmbedInput.model_fields)
    )

    # SAM-3 所有视频 API 的字段（合并到 VIDEO_SEGMENTATION）
    sam3_video_allowed = (
        extra_allowed_fields
        | set(SAM3VideoInput.model_fields)
        | set(SAM3VideoRLEInput.model_fields)
    )

    bfl_allowed = extra_allowed_fields | set(BFLInput.model_fields)
    # Azure 聚合 OpenAI 和 Flux 的字段
    azure_images_allowed = openai_images_allowed | set(AzureFluxImageInput.model_fields)
    azure_images_edit_allowed = openai_images_edit_allowed | set(AzureFluxImageEditInput.model_fields)

    google_required = {"model", "contents"}
    google_vertex_required = {"model", "prompt"}
    google_genai_images_required = {"model", "prompt"}
    google_genai_videos_required = {"model"}
    openai_resp_required = {"input", "model"}
    openai_chat_required = {"messages", "model"}
    openai_img_required = {"prompt"}
    openai_edit_required = {"image", "prompt"}
    openai_videos_required = {"prompt"}
    anthropic_messages_required = {"max_tokens", "messages", "model"}
    freepik_image_upscaler_required = {"image"}
    byteplus_omnihuman_video_required = {"image_url", "audio_url"}
    byteplus_seedance_video_required = {"model", "content"}
    # BytePlus VIDEO_GENERATION 没有统一的必填字段（因为两个 API 不同）
    byteplus_video_required = set()  # 由服务端根据 channel 进行具体校验
    # FAL_AI Qwen Image Edit Plus 必填字段
    fal_ai_qwen_image_edit_required = {"image_urls"}
    # FAL_AI Qwen Image Layered 必填字段
    fal_ai_qwen_image_layered_required = {"prompt", "image_url"}
    fal_ai_wan_video_replace_required = {"video_url", "image_url"}
    bfl_required = {"prompt"}

    match (instance.provider, instance.invoke_type):
        case (ProviderType.GOOGLE | ProviderType.XFUSIONAI | ProviderType.TUZI, InvokeType.GENERATION):
            allowed = google_allowed
            required = google_required
        case (ProviderType.GOOGLE, InvokeType.IMAGE_GENERATION):
            allowed = google_vertexai_images_allowed
            required = google_vertex_required
        case ((ProviderType.OPENAI | ProviderType.AZURE), (InvokeType.RESPONSES | InvokeType.GENERATION)) \
             | ((ProviderType.ANTHROPIC), InvokeType.RESPONSES):
            allowed = openai_responses_allowed
            required = openai_resp_required
        case ((ProviderType.OPENAI | ProviderType.AZURE | ProviderType.ANTHROPIC), InvokeType.CHAT_COMPLETIONS):
            allowed = openai_chat_allowed
            required = openai_chat_required
        case (ProviderType.OPENAI, InvokeType.IMAGE_GENERATION):
            allowed = openai_images_allowed
            required = openai_img_required
        case (ProviderType.OPENAI, InvokeType.IMAGE_EDIT_GENERATION):
            allowed = openai_images_edit_allowed
            required = openai_edit_required
        case (ProviderType.AZURE, InvokeType.IMAGE_GENERATION):
            # Azure 支持 OpenAI (gpt-image-1) 和 Flux 模型，聚合两者的字段
            allowed = azure_images_allowed
            required = openai_img_required
        case (ProviderType.AZURE, InvokeType.IMAGE_EDIT_GENERATION):
            # Azure 支持 OpenAI 和 Flux 图片编辑，聚合两者的字段
            allowed = azure_images_edit_allowed
            required = openai_edit_required
        case ((ProviderType.OPENAI | ProviderType.AZURE | ProviderType.XFUSIONAI | ProviderType.TUZI),
              InvokeType.VIDEO_GENERATION):
            allowed = openai_videos_allowed
            required = openai_videos_required
        case (ProviderType.GOOGLE, InvokeType.IMAGE_GENERATION_GENAI):
            allowed = google_genai_images_allowed
            required = google_genai_images_required
        case (ProviderType.GOOGLE, InvokeType.VIDEO_GENERATION_GENAI):
            allowed = google_genai_videos_allowed
            required = google_genai_videos_required
        case (ProviderType.ANTHROPIC, InvokeType.GENERATION | InvokeType.MESSAGES):
            allowed = anthropic_messages_allowed
            required = anthropic_messages_required
        case (ProviderType.FREEPIK, InvokeType.IMAGE_UPSCALER):
            allowed = freepik_image_upscaler_allowed
            required = freepik_image_upscaler_required
        case (ProviderType.BYTEPLUS | ProviderType.DOUBAO, InvokeType.VIDEO_GENERATION):
            # BytePlus 和 Doubao 支持 OmniHuman 和 SeeDANCE 两种视频生成 API
            allowed = byteplus_video_allowed
            required = byteplus_video_required
        case (ProviderType.FAL_AI, InvokeType.IMAGE_GENERATION):
            # Z-Image API
            allowed = fal_ai_z_image_allowed
            required = {"model", "prompt"}  # Z-Image 的必填字段
        case (ProviderType.FAL_AI, InvokeType.IMAGE_SEGMENTATION):
            # SAM-3 图像 API（6个）
            allowed = sam3_image_allowed
            required = {"model"}  # model 必填，用于路由到不同的 SAM-3 API
        case (ProviderType.FAL_AI, InvokeType.IMAGE_EDIT_GENERATION):
            allowed = fal_ai_qwen_image_edit_allowed
            required = fal_ai_qwen_image_edit_required
        case (ProviderType.FAL_AI, InvokeType.IMAGE_LAYER_GENERATION):
            allowed = fal_ai_qwen_image_layered_allowed
            required = fal_ai_qwen_image_layered_required
        case (ProviderType.FAL_AI, InvokeType.VIDEO_EDIT_GENERATION):
            allowed = fal_ai_wan_video_replace_allowed
            required = fal_ai_wan_video_replace_required
        case (ProviderType.FAL_AI, InvokeType.VIDEO_GENERATION):
            # Kling Video API
            allowed = fal_ai_kling_video_allowed
            required = {"model", "prompt"}  # Kling Video 的必填字段
        case (ProviderType.FAL_AI, InvokeType.VIDEO_SEGMENTATION):
            # SAM-3 视频 API（2个）
            allowed = sam3_video_allowed
            required = {"model"}  # model 必填，用于路由到不同的 SAM-3 API
        case (ProviderType.BFL, InvokeType.IMAGE_GENERATION | InvokeType.IMAGE_EDIT_GENERATION):
            allowed = bfl_allowed
            required = bfl_required
        case _:
            raise ValueError(f"Unsupported provider/invoke_type: {instance.provider} + {instance.invoke_type}")

    required = required | extra_required_fields

    from openai import Omit

    def is_missing_value(val):
        """Check if a value is considered missing (None, NOT_GIVEN, or Omit)"""
        return val is None or isinstance(val, NotGiven) or isinstance(val, Omit)

    missing = [f for f in required if is_missing_value(getattr(instance, f, None))]
    if missing:
        raise ValueError(
            f"Missing required fields for provider={instance.provider} and invoke_type={instance.invoke_type}: {missing}")

    illegal = []
    valid_fields = {"provider", "channel", "invoke_type"}
    if getattr(instance, "stream", None) is not None:
        valid_fields.add("stream")

    for k, v in instance.__dict__.items():
        if k in valid_fields:
            continue
        if k not in allowed and v is not None and not isinstance(v, NotGiven):
            illegal.append(k)

    if illegal:
        raise ValueError(
            f"Unsupported fields for provider={instance.provider} and invoke_type={instance.invoke_type}: {illegal}")

    return instance
