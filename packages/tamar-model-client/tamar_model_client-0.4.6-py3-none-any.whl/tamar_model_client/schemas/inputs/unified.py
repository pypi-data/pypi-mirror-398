import httpx
from anthropic._types import SequenceNotStr
from anthropic.types import MetadataParam, TextBlockParam, ThinkingConfigParam, ToolChoiceParam, ToolUnionParam, \
    ModelParam
from google.genai import types
from openai import NotGiven, NOT_GIVEN, Omit
from openai._types import Headers, Query, Body, FileTypes
from openai.types import ChatModel, Metadata, ReasoningEffort, ImageModel, VideoModel, VideoSeconds, VideoSize
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionAudioParam, completion_create_params, \
    ChatCompletionPredictionContentParam, ChatCompletionStreamOptionsParam, ChatCompletionToolChoiceOptionParam, \
    ChatCompletionToolUnionParam
from openai.types.responses import ResponseInputParam, ResponseIncludable, ResponseTextConfigParam, \
    response_create_params, ToolParam
from openai.types.responses.response_prompt_param import ResponsePromptParam
from openai.types.shared_params import ResponsesModel, Reasoning
from pydantic import BaseModel, model_validator, field_validator
from typing import Any, List, Optional, Union, Iterable, Dict, Literal, Sequence

from tamar_model_client.schemas.inputs.base import UserContext, TamarFileIdInput, BaseRequest
from tamar_model_client.utils import convert_file_field, validate_fields_by_provider_and_invoke_type


class ModelRequestInput(BaseRequest):
    # 合并 model 字段
    model: Optional[Union[str, ResponsesModel, ChatModel, ImageModel, VideoModel, ModelParam]] = None

    # OpenAI Responses Input（合并）
    input: Optional[Union[str, ResponseInputParam]] = None
    conversation: Optional[Union[response_create_params.Conversation, NotGiven]] = NOT_GIVEN
    include: Optional[Union[List[ResponseIncludable], NotGiven]] = NOT_GIVEN
    instructions: Optional[Union[str, NotGiven]] = NOT_GIVEN
    max_output_tokens: Optional[Union[int, NotGiven]] = NOT_GIVEN
    max_tool_calls: Optional[Union[int, NotGiven]] = NOT_GIVEN
    metadata: Optional[Union[Metadata, "MetadataParam", NotGiven]] = NOT_GIVEN
    parallel_tool_calls: Optional[Union[bool, NotGiven]] = NOT_GIVEN
    previous_response_id: Optional[Union[str, NotGiven]] = NOT_GIVEN
    prompt: Optional[Union[str, ResponsePromptParam, NotGiven]] = NOT_GIVEN
    prompt_cache_key: Optional[Union[str, NotGiven]] = NOT_GIVEN
    prompt_cache_retention: Optional[Union[Literal["in-memory", "24h"], NotGiven]] = NOT_GIVEN
    reasoning: Optional[Union[Reasoning, NotGiven]] = NOT_GIVEN
    safety_identifier: Optional[Union[str, NotGiven]] = NOT_GIVEN
    service_tier: Optional[
        Union[Literal["auto", "default", "flex", "scale", "priority", "standard_only"], NotGiven]  # +anthropic
    ] = NOT_GIVEN
    store: Optional[Union[bool, NotGiven]] = NOT_GIVEN
    stream: Optional[Union[Literal[False], Literal[True], NotGiven]] = NOT_GIVEN
    stream_options: Optional[
        Union[response_create_params.StreamOptions, ChatCompletionStreamOptionsParam, NotGiven]] = NOT_GIVEN
    temperature: Optional[Union[float, NotGiven]] = NOT_GIVEN
    text: Optional[Union[ResponseTextConfigParam, NotGiven]] = NOT_GIVEN
    tool_choice: Optional[
        Union[response_create_params.ToolChoice, ChatCompletionToolChoiceOptionParam, "ToolChoiceParam", NotGiven]
    ] = NOT_GIVEN
    tools: Optional[
        Union[Iterable[ToolParam], Iterable[ChatCompletionToolUnionParam], Iterable["ToolUnionParam"], NotGiven]] = NOT_GIVEN
    top_logprobs: Optional[Union[int, NotGiven]] = NOT_GIVEN
    top_p: Optional[Union[float, NotGiven]] = NOT_GIVEN
    truncation: Optional[Union[Literal["auto", "disabled"], NotGiven]] = NOT_GIVEN
    user: Optional[Union[str, NotGiven]] = NOT_GIVEN
    verbosity: Optional[Union[Literal["low", "medium", "high"], NotGiven]] = NOT_GIVEN

    extra_headers: Optional[Union[Headers, None]] = None
    extra_query: Optional[Union[Query, None]] = None
    extra_body: Optional[Union[Body, None]] = None
    timeout: Optional[Union[float, httpx.Timeout, None, NotGiven]] = NOT_GIVEN

    # OpenAI Chat Completions Input（合并）
    messages: Optional[Iterable[ChatCompletionMessageParam]] = None
    audio: Optional[Union[ChatCompletionAudioParam, NotGiven]] = NOT_GIVEN
    frequency_penalty: Optional[Union[float, NotGiven]] = NOT_GIVEN
    function_call: Optional[Union[completion_create_params.FunctionCall, NotGiven]] = NOT_GIVEN
    functions: Optional[Union[Iterable[completion_create_params.Function], NotGiven]] = NOT_GIVEN
    logit_bias: Optional[Union[Dict[str, int], NotGiven]] = NOT_GIVEN
    logprobs: Optional[Union[bool, NotGiven]] = NOT_GIVEN
    max_completion_tokens: Optional[Union[int, NotGiven]] = NOT_GIVEN
    max_tokens: Optional[Union[int, NotGiven]] = NOT_GIVEN
    modalities: Optional[Union[List[Literal["text", "audio"]], NotGiven]] = NOT_GIVEN
    n: Optional[Union[int, NotGiven]] = NOT_GIVEN
    prediction: Optional[Union[ChatCompletionPredictionContentParam, NotGiven]] = NOT_GIVEN
    presence_penalty: Optional[Union[float, NotGiven]] = NOT_GIVEN
    reasoning_effort: Optional[Union[ReasoningEffort, NotGiven]] = NOT_GIVEN
    thinking: Optional[Union["ThinkingConfigParam", NotGiven]] = NOT_GIVEN
    response_format: Optional[
        Union[completion_create_params.ResponseFormat, Literal["url", "b64_json"], NotGiven]
    ] = NOT_GIVEN
    seed: Optional[Union[int, NotGiven]] = NOT_GIVEN
    stop: Optional[Union[str, List[str], NotGiven]] = NOT_GIVEN
    web_search_options: Optional[Union[completion_create_params.WebSearchOptions, NotGiven]] = NOT_GIVEN

    # Anthropic Messages Input
    system: Optional[Union[str, Iterable["TextBlockParam"], NotGiven]] = NOT_GIVEN
    stop_sequences: Optional[Union["SequenceNotStr[str]", Sequence[str], NotGiven]] = NOT_GIVEN
    top_k: Optional[Union[int, NotGiven]] = NOT_GIVEN

    # Google GenAI Input
    contents: Optional[Union[types.ContentListUnion, types.ContentListUnionDict]] = None
    config: Optional[Union[
        types.GenerateContentConfigOrDict, types.GenerateImagesConfigOrDict, types.GenerateVideosConfigOrDict]] = None

    # Google GenAI Videos Input
    video: Optional[types.VideoOrDict] = None
    source: Optional[Any] = None  # GenerateVideosSourceOrDict (if available)

    # OpenAI Videos Input
    input_reference: Optional[Union[FileTypes, TamarFileIdInput, NotGiven]] = NOT_GIVEN
    seconds: Optional[Union[VideoSeconds, NotGiven]] = NOT_GIVEN

    # 异步任务回调地址（通用）
    callback_url: Optional[str] = None  # 异步任务回调地址

    # Images（OpenAI Images / Images Edit / Google Vertex Images / Freepik 合并）
    image: Optional[Union[str, FileTypes, List[FileTypes], TamarFileIdInput, List[TamarFileIdInput]]] = None
    background: Optional[Union[bool, Literal["transparent", "opaque", "auto"], NotGiven]] = NOT_GIVEN  # OpenAI Responses(bool) + OpenAI Images(Literal)
    moderation: Optional[Union[Literal["low", "auto"], NotGiven]] = NOT_GIVEN
    input_fidelity: Optional[Union[Literal["high", "low"], NotGiven]] = NOT_GIVEN
    output_compression: Optional[Union[int, NotGiven]] = NOT_GIVEN
    output_format: Optional[Union[Literal["png", "jpeg", "webp", "b64_json", "url", "jpg"], NotGiven]] = NOT_GIVEN  # 扩展以支持 Azure Flux
    partial_images: Optional[Union[int, NotGiven]] = NOT_GIVEN
    mask: Union[FileTypes, TamarFileIdInput, NotGiven] = NOT_GIVEN
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[Literal["1:1", "9:16", "16:9", "4:3", "3:4", "21:9", "3:2", "2:3", "9:21"]] = None
    guidance_scale: Optional[float] = None
    enable_base64_output: Optional[bool] = None  # Azure Flux
    enable_sync_mode: Optional[bool] = None  # Azure Flux 编辑
    language: Optional[str] = None
    output_gcs_uri: Optional[str] = None
    add_watermark: Optional[bool] = None
    safety_filter_level: Optional[Literal["block_most", "block_some", "block_few", "block_fewest"]] = None
    person_generation: Optional[Literal["dont_allow", "allow_adult", "allow_all"]] = None
    quality: Optional[Union[Literal["standard", "hd", "low", "medium", "high", "auto"], NotGiven]] = NOT_GIVEN
    size: Optional[
        Union[
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            VideoSize,
            NotGiven,
        ]
    ] = NOT_GIVEN
    style: Optional[Union[Literal["vivid", "natural"], NotGiven]] = NOT_GIVEN
    number_of_images: Optional[int] = None  # Google 用法

    # Freepik Image Upscaler Input
    scale_factor: Optional[int] = None  # 图像缩放倍数 (2-16)
    sharpen: Optional[int] = None  # 锐化程度 (0-10)
    smart_grain: Optional[int] = None  # 智能颗粒度 (0-10)
    ultra_detail: Optional[int] = None  # 超细节程度 (0-100)
    flavor: Optional[Literal["sublime", "photo", "photo_denoiser"]] = None  # 处理风格

    # BytePlus OmniHuman Video Input
    image_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # 图像URL (支持 URL、TamarFileIdInput、dict)
    audio_url: Optional[str] = None  # 音频URL
    mask_url: Optional[str] = None  # 掩码URL
    pe_fast_mode: Optional[bool] = None  # 快速模式

    # Fal AI Qwen Image Edit Input
    image_urls: Optional[Union[List[str], List[TamarFileIdInput]]] = None  # 图像URL列表
    image_size: Optional[Union[
        Literal["square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"],
        Dict[str, Any]
    ]] = None  # 图像尺寸
    num_inference_steps: Optional[int] = None  # 推理步骤数
    acceleration: Optional[Literal["none", "regular", "high"]] = None  # 加速模式（Fal AI Qwen / Z-Image）
    sync_mode: Optional[bool] = None  # 同步模式
    enable_safety_checker: Optional[bool] = None  # 启用安全检查器
    enable_prompt_expansion: Optional[bool] = None  # 启用提示词扩展（Fal AI Z-Image）
    num_images: Optional[int] = None  # 生成图像数量
    loras: Optional[List[dict]] = None  # LoRA 权重列表（Fal AI Z-Image Turbo LoRA，最多 3 个）
    rotate_right_left: Optional[float] = None  # 左右旋转角度
    move_forward: Optional[float] = None  # 向前移动距离
    vertical_angle: Optional[float] = None  # 垂直角度
    wide_angle_lens: Optional[bool] = None  # 广角镜头
    lora_scale: Optional[float] = None  # LoRA 缩放系数

    # Fal AI Wan Video Replace Input
    video_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # 视频URL (支持 URL、TamarFileIdInput、dict)
    resolution: Optional[Literal["480p", "580p", "720p", "1080p"]] = None  # 视频分辨率 - Kling Video / SeeDANCE
    enable_output_safety_checker: Optional[bool] = None  # 启用输出安全检查器
    shift: Optional[float] = None  # 偏移量
    video_write_mode: Optional[Literal["fast", "balanced", "small"]] = None  # 视频写入模式
    return_frames_zip: Optional[bool] = None  # 返回帧 zip 文件
    use_turbo: Optional[bool] = None  # 使用 turbo 模式
    video_quality: Optional[Union[str, Literal["low", "medium", "high", "maximum"]]] = None  # 视频质量

    # Fal AI Kling Video Input
    duration: Optional[Union[Literal["5", "10"], int]] = None  # 视频时长（秒）- Kling Video / OpenAI Videos / SeeDANCE (4-12或-1)
    elements: Optional[List[dict]] = None  # Kling Video 元素列表（角色或物体）
    cfg_scale: Optional[float] = None  # CFG 缩放系数（Kling Video）
    static_mask_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # 静态遮罩 URL（Kling Video Advanced）
    dynamic_masks: Optional[List[dict]] = None  # 动态遮罩列表（Kling Video Advanced）
    camera_control: Optional[str] = None  # 相机控制参数（Kling Video V1）
    tail_image_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # 结束帧图像 URL（Kling Video Pro）

    # BytePlus SeeDANCE Input
    content: Optional[List[dict]] = None  # SeeDANCE 内容数组（text 或 image_url 对象）
    ratio: Optional[Literal["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"]] = None  # SeeDANCE 宽高比
    camerafixed: Optional[bool] = None  # SeeDANCE 是否固定相机
    watermark: Optional[bool] = None  # SeeDANCE 是否添加水印
    framepersecond: Optional[int] = None  # SeeDANCE 帧率（FPS）
    frames: Optional[int] = None  # SeeDANCE 视频帧数
    return_last_frame: Optional[bool] = None  # SeeDANCE 是否返回最后一帧图像
    generate_audio: Optional[bool] = None  # SeeDANCE 是否生成音频
    execution_expires_after: Optional[int] = None  # SeeDANCE 任务过期时间（秒）

    # Fal AI SAM-3 Input（支持 8 个 API）
    body_mesh_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # SAM-3 3D Align: 人体网格文件 URL
    object_mesh_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # SAM-3 3D Align: 物体网格文件 URL
    focal_length: Optional[float] = None  # SAM-3 3D Align: 焦距
    export_meshes: Optional[bool] = None  # SAM-3 3D Body: 导出网格文件
    include_3d_keypoints: Optional[bool] = None  # SAM-3 3D Body: 包含 3D 关键点
    mask_urls: Optional[List[Union[str, TamarFileIdInput, dict]]] = None  # SAM-3 3D Objects: 遮罩 URL 列表
    point_prompts: Optional[List[dict]] = None  # SAM-3 Image/Video: 点提示列表
    box_prompts: Optional[List[dict]] = None  # SAM-3 Image/Video: 框提示列表
    pointmap_url: Optional[Union[str, TamarFileIdInput, dict]] = None  # SAM-3 3D Objects: 点云/深度数据 URL
    apply_mask: Optional[bool] = None  # SAM-3 Image/Video: 应用遮罩
    return_multiple_masks: Optional[bool] = None  # SAM-3 Image/Image RLE: 返回多个遮罩
    max_masks: Optional[int] = None  # SAM-3 Image/Image RLE: 最大遮罩数量
    include_scores: Optional[bool] = None  # SAM-3 Image/Image RLE: 包含置信度分数
    include_boxes: Optional[bool] = None  # SAM-3 Image/Image RLE: 包含边界框
    frame_index: Optional[int] = None  # SAM-3 Video RLE: 帧索引
    boundingbox_zip: Optional[bool] = None  # SAM-3 Video RLE: 返回边界框 zip
    detection_threshold: Optional[float] = None  # SAM-3 Video/Video RLE: 检测置信度阈值

    # BFL Flux Input
    image_prompt: Optional[Union[str, TamarFileIdInput, dict]] = None  # 图像提示词（FLUX 1.1 PRO）
    input_image: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像（用于图像编辑和参考）
    input_image_2: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像2（支持最多8张参考图像）
    input_image_3: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像3
    input_image_4: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像4
    input_image_5: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像5
    input_image_6: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像6
    input_image_7: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像7
    input_image_8: Optional[Union[str, TamarFileIdInput, dict]] = None  # 输入图像8
    width: Optional[int] = None  # 图像宽度（BFL / 其他提供商）
    height: Optional[int] = None  # 图像高度（BFL / 其他提供商）
    guidance: Optional[float] = None  # 引导系数（FLUX.2 FLEX）
    steps: Optional[int] = None  # 生成步骤数（FLUX.2 FLEX / 其他提供商）
    safety_tolerance: Optional[Literal["1", "2", "3", "4", "5", "6"]] = None  # 安全容忍度（BFL）
    webhook_url: Optional[str] = None  # Webhook 回调 URL（BFL）
    webhook_secret: Optional[str] = None  # Webhook 密钥（BFL）

    # 是否开启异步任务模式(默认True)
    enable_async_task: Optional[bool] = None

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("image", mode="before")
    @classmethod
    def validate_image(cls, v):
        return convert_file_field(v)

    @field_validator("mask", mode="before")
    @classmethod
    def validate_mask(cls, v):
        return convert_file_field(v)


class ModelRequest(ModelRequestInput):
    user_context: UserContext  # 用户信息

    @model_validator(mode="after")
    def validate_by_provider_and_invoke_type(self) -> "ModelRequest":
        return validate_fields_by_provider_and_invoke_type(
            instance=self,
            extra_allowed_fields={"provider", "channel", "invoke_type", "user_context", "enable_async_task", "model"},
        )


class BatchModelRequestItem(ModelRequestInput):
    custom_id: Optional[str] = None
    priority: Optional[int] = None  # （可选、预留字段）批量调用时执行的优先级

    @model_validator(mode="after")
    def validate_by_provider_and_invoke_type(self) -> "BatchModelRequestItem":
        return validate_fields_by_provider_and_invoke_type(
            instance=self,
            extra_allowed_fields={"provider", "channel", "invoke_type", "user_context", "custom_id", "enable_async_task", "model"},
        )


class BatchModelRequest(BaseModel):
    user_context: UserContext  # 用户信息
    items: List[BatchModelRequestItem]  # 批量请求项列表
