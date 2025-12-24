from typing import Any, TypeAlias, Union
from dataclasses import dataclass

from .response import ChatCompletionResponse
from .messages import ToolCall


@dataclass
class AssistantMessageDeltaChunk:
    """Incremental changes to an assistant message.

    Attributes:
        content: Incremental text content chunk
    """
    content: str

    @property
    def type(self) -> str:
        return "content_delta"


@dataclass
class AssistantMessageSentenceChunk:
    """Incremental fully-formed sentences of an assistant message.

    Attributes:
        sentence: Complete sentence extracted from the streaming response
    """
    sentence: str

    @property
    def type(self) -> str:
        return "content_sentence"


@dataclass
class ToolCallChunk:
    """Full formed tool call compiled from streamed parts.

    Attributes:
        tool_call: Complete tool call with function name and arguments
    """
    tool_call: ToolCall

    @property
    def type(self) -> str:
        return "tool_call"


@dataclass
class FinishReasonChunk:
    """Finish reason of the streamed completion.

    Attributes:
        finish_reason: Reason the model stopped generating (e.g., "stop", "length", "tool_calls")
    """
    finish_reason: str

    @property
    def type(self) -> str:
        return "finish_reason"


@dataclass
class UsageChunk:
    """Usage information of the streamed completion.

    Attributes:
        usage: Usage statistics including token counts and costs
    """
    usage: dict[str, Any]

    @property
    def type(self) -> str:
        return "usage"


@dataclass
class FinalResponseChunk:
    """Full chat completion response built from AssistantMessageDeltaChunks and ToolCallChunk.

    Attributes:
        response: Complete chat completion response assembled from streaming chunks
    """
    response: ChatCompletionResponse

    @property
    def type(self) -> str:
        return "response"


ChatCompletionChunk: TypeAlias = Union[AssistantMessageDeltaChunk, ToolCallChunk, FinishReasonChunk, UsageChunk, FinalResponseChunk] 
