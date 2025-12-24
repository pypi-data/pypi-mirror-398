from typing import Any, Optional
from dataclasses import dataclass

from .messages import AssistantMessage


@dataclass
class ChatCompletionResponse:
    """Normalized chat completion response from any LLM provider.

    Attributes:
        message: The assistant's response message containing content and/or tool calls
        finish_reason: Reason the model stopped generating (e.g., "stop", "length", "tool_calls")
        usage: Optional usage statistics including token counts and costs
    """
    message: AssistantMessage
    finish_reason: str
    usage: Optional[dict[str, Any]] = None
