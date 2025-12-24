from typing import Any, Dict, Literal, Optional, TypeAlias, Union
from enum import StrEnum
from dataclasses import dataclass

from .messages import ConversationHistory
from .cache import CacheBreakpoint


class CompletionsProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class FunctionDefinition:
    """Function definition for tool calling.

    Attributes:
        name: Name of the function
        description: Description of what the function does
        parameters: JSON schema describing the function's parameters
        strict: Whether to enable strict mode for parameter validation (OpenAI only)
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: Optional[bool] = None

    @classmethod
    def deserialize(cls, data: dict) -> "FunctionDefinition":
        """Deserialize function definition from dictionary representation."""
        return cls(
            name=data["name"],
            description=data["description"],
            parameters=data["parameters"],
            strict=data.get("strict", None),
        )


@dataclass
class ToolDefinition:
    """Tool definition for LLM tool calling.

    Attributes:
        type: Type of tool (always "function")
        function: Function definition containing name, description, and parameters
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
    """
    type: Literal["function"]
    function: FunctionDefinition
    cache_breakpoint: Optional[CacheBreakpoint] = None

    @classmethod
    def deserialize(cls, data: dict) -> "ToolDefinition":
        """Deserialize tool definition from dictionary representation."""
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        return cls(
            type=data["type"],
            function=FunctionDefinition.deserialize(data["function"]),
            cache_breakpoint=cache_breakpoint,
        )


ToolChoice: TypeAlias = Union[Literal["none", "auto", "required"], str]


def normalize_tools(tools: list[Union[dict, ToolDefinition]]) -> list[ToolDefinition]:
    """Convert list of dicts or tool def objects to list of normalized ToolDefinitions."""
    normalized_tools: list[ToolDefinition] = []

    for tool in tools:
        if isinstance(tool, ToolDefinition):
            normalized_tools.append(tool)
        elif isinstance(tool, dict):
            normalized_tools.append(ToolDefinition.deserialize(tool))
        else:
            raise TypeError(f"Tools must be dict or ToolDefinition, got {type(tool)}")

    return normalized_tools


@dataclass
class StreamOptions:
    """Options for configuring streaming behavior.

    Attributes:
        stream_sentences: Whether to stream response by sentences instead of tokens
        clean_sentences: Whether to clean markdown and special characters from sentences for speech
            Only applicable if stream_sentences = True
            Defaults to True
        min_sentence_length: Minimum length (in characters) for a sentence to be yielded
            Only applicable if stream_sentences = True
            Defaults to 6 characters
        punctuation_marks: Optional set of punctuation marks to use for sentence boundaries
            Only applicable if stream_sentences = True
            Defaults to comprehensive set covering most languages
        punctuation_language: Optional language code to use language-specific punctuation
            Only applicable if stream_sentences = True
            Supported: 'en', 'zh', 'ko', 'ja', 'es', 'fr', 'it', 'de'
    """
    stream_sentences: bool = False
    clean_sentences: bool = True
    min_sentence_length: int = 6
    punctuation_marks: Optional[list[str]] = None
    punctuation_language: Optional[str] = None

    @classmethod
    def deserialize(cls, data: dict) -> "StreamOptions":
        """Deserialize stream options from dictionary representation."""
        return cls(
            stream_sentences=data.get("stream_sentences", False),
            clean_sentences=data.get("clean_sentences", True),
            min_sentence_length=data.get("min_sentence_length", 6),
            punctuation_marks=data.get("punctuation_marks", None),
            punctuation_language=data.get("punctuation_language", None),
        )


@dataclass
class ChatCompletionRequest:
    """Normalized chat completion request for any LLM provider.

    Attributes:
        provider: LLM provider to use (OpenAI, Anthropic, or Google)
        api_key: API key for authentication with the provider
        model: Model name to use for completion
        messages: Conversation history as a list of messages
        temperature: Sampling temperature for response randomness (0.0 to 1.0)
        tools: Optional list of tool definitions for function calling
        tool_choice: How the model should choose which tools to call
        streaming: Whether to stream the response
        stream_options: Options for configuring streaming behavior
        timeout: Request timeout in seconds
        max_tokens: Maximum number of tokens in the response
        service_tier: Optional service tier for OpenAI API (e.g., "auto", "default")
    """
    provider: CompletionsProvider
    api_key: str
    model: str
    messages: ConversationHistory
    temperature: Optional[float] = None
    tools: Optional[list[ToolDefinition]] = None
    tool_choice: Optional[ToolChoice] = None
    streaming: bool = False
    stream_options: Optional[StreamOptions] = None
    timeout: Optional[float] = None
    max_tokens: Optional[int] = None
    service_tier: Optional[str] = None
