from typing import Iterable, Union, Optional, Dict, List, Literal

import httpx
from openai import Omit, omit
from openai._types import SequenceNotStr, Headers, Query, Body, NotGiven, not_given
from openai.types import ChatModel, Metadata, ReasoningEffort
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionAudioParam, completion_create_params, \
    ChatCompletionPredictionContentParam, ChatCompletionStreamOptionsParam, ChatCompletionToolChoiceOptionParam, \
    ChatCompletionToolUnionParam
from pydantic import BaseModel


class OpenAIChatCompletionsInput(BaseModel):
    messages: Iterable[ChatCompletionMessageParam]
    model: Union[str, ChatModel]
    audio: Optional[ChatCompletionAudioParam] | Omit = omit
    frequency_penalty: Optional[float] | Omit = omit
    function_call: completion_create_params.FunctionCall | Omit = omit
    functions: Iterable[completion_create_params.Function] | Omit = omit
    logit_bias: Optional[Dict[str, int]] | Omit = omit
    logprobs: Optional[bool] | Omit = omit
    max_completion_tokens: Optional[int] | Omit = omit
    max_tokens: Optional[int] | Omit = omit
    metadata: Optional[Metadata] | Omit = omit
    modalities: Optional[List[Literal["text", "audio"]]] | Omit = omit
    n: Optional[int] | Omit = omit
    parallel_tool_calls: bool | Omit = omit
    prediction: Optional[ChatCompletionPredictionContentParam] | Omit = omit
    presence_penalty: Optional[float] | Omit = omit
    prompt_cache_key: str | Omit = omit
    prompt_cache_retention: Optional[Literal["in-memory", "24h"]] | Omit = omit
    reasoning_effort: Optional[ReasoningEffort] | Omit = omit
    response_format: completion_create_params.ResponseFormat | Omit = omit
    safety_identifier: str | Omit = omit
    seed: Optional[int] | Omit = omit
    service_tier: Optional[Literal["auto", "default", "flex", "scale", "priority"]] | Omit = omit
    stop: Union[Optional[str], SequenceNotStr[str], None] | Omit = omit
    store: Optional[bool] | Omit = omit
    stream: Optional[Literal[False]] | Literal[True] | Omit = omit
    stream_options: Optional[ChatCompletionStreamOptionsParam] | Omit = omit
    temperature: Optional[float] | Omit = omit
    tool_choice: ChatCompletionToolChoiceOptionParam | Omit = omit
    tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit
    top_logprobs: Optional[int] | Omit = omit
    top_p: Optional[float] | Omit = omit
    user: str | Omit = omit
    verbosity: Optional[Literal["low", "medium", "high"]] | Omit = omit
    web_search_options: completion_create_params.WebSearchOptions | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    model_config = {
        "arbitrary_types_allowed": True
    }
