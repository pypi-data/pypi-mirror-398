import httpx
from anthropic._types import SequenceNotStr
from anthropic.types import MessageParam, ModelParam, MetadataParam, TextBlockParam, ThinkingConfigParam, \
    ToolChoiceParam, ToolUnionParam
from openai import NotGiven, NOT_GIVEN
from openai._types import Headers, Query, Body
from pydantic import BaseModel
from typing import Union, Iterable, Literal


class AnthropicMessagesInput(BaseModel):
    max_tokens: int
    messages: Iterable[MessageParam]
    model: ModelParam
    metadata: MetadataParam | NotGiven = NOT_GIVEN
    service_tier: Literal["auto", "standard_only"] | NotGiven = NOT_GIVEN
    stop_sequences: SequenceNotStr[str] | NotGiven = NOT_GIVEN
    stream: Literal[False] | Literal[True] | NotGiven = NOT_GIVEN
    system: Union[str, Iterable[TextBlockParam]] | NotGiven = NOT_GIVEN
    temperature: float | NotGiven = NOT_GIVEN
    thinking: ThinkingConfigParam | NotGiven = NOT_GIVEN
    tool_choice: ToolChoiceParam | NotGiven = NOT_GIVEN
    tools: Iterable[ToolUnionParam] | NotGiven = NOT_GIVEN
    top_k: int | NotGiven = NOT_GIVEN
    top_p: float | NotGiven = NOT_GIVEN
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN

    model_config = {
        "arbitrary_types_allowed": True
    }
