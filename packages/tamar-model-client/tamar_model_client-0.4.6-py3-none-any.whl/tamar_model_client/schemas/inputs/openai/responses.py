from typing import Optional, List, Union, Literal, Iterable

import httpx
from openai import Omit, omit
from openai._types import Headers, Query, Body, NotGiven, not_given
from openai.types import Metadata
from openai.types.responses import response_create_params, ResponseIncludable, ResponseInputParam, ResponsePromptParam, \
    ResponseTextConfigParam, ToolParam
from openai.types.shared_params import ResponsesModel, Reasoning
from pydantic import BaseModel


class OpenAIResponsesInput(BaseModel):
    background: Optional[bool] | Omit = omit
    conversation: Optional[response_create_params.Conversation] | Omit = omit
    include: Optional[List[ResponseIncludable]] | Omit = omit
    input: Union[str, ResponseInputParam] | Omit = omit
    instructions: Optional[str] | Omit = omit
    max_output_tokens: Optional[int] | Omit = omit
    max_tool_calls: Optional[int] | Omit = omit
    metadata: Optional[Metadata] | Omit = omit
    model: ResponsesModel | Omit = omit
    parallel_tool_calls: Optional[bool] | Omit = omit
    previous_response_id: Optional[str] | Omit = omit
    prompt: Optional[ResponsePromptParam] | Omit = omit
    prompt_cache_key: str | Omit = omit
    prompt_cache_retention: Optional[Literal["in-memory", "24h"]] | Omit = omit
    reasoning: Optional[Reasoning] | Omit = omit
    safety_identifier: str | Omit = omit
    service_tier: Optional[Literal["auto", "default", "flex", "scale", "priority"]] | Omit = omit
    store: Optional[bool] | Omit = omit
    stream: Optional[Literal[False]] | Literal[True] | Omit = omit
    stream_options: Optional[response_create_params.StreamOptions] | Omit = omit
    temperature: Optional[float] | Omit = omit
    text: ResponseTextConfigParam | Omit = omit
    tool_choice: response_create_params.ToolChoice | Omit = omit
    tools: Iterable[ToolParam] | Omit = omit
    top_logprobs: Optional[int] | Omit = omit
    top_p: Optional[float] | Omit = omit
    truncation: Optional[Literal["auto", "disabled"]] | Omit = omit
    user: str | Omit = omit
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = not_given

    model_config = {
        "arbitrary_types_allowed": True
    }
