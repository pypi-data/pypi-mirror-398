from typing import Any, Literal
from dataclasses import dataclass


@dataclass
class CacheBreakpoint:
    """Anthropic prompt caching breakpoint for optimization.
    Anthropic request will fail if supplied with more than 4 cache breakpoints in the request.

    [Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

    Attributes:
        ttl: The time-to-live for the cache control breakpoint
    """
    ttl: Literal["5m", "1h"]

    def serialize(self) -> dict[str, Any]:
        """Serialize cache breakpoint to dict representation."""
        return {"ttl": self.ttl}
    
    @classmethod
    def deserialize(cls, data: dict) -> "CacheBreakpoint":
        """Deserialize cache breakpoint from dict representation."""
        return cls(ttl=data["ttl"])
