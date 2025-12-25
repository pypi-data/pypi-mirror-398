"""Data models for AI Bridge."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class VendorType(str, Enum):
    """Supported AI vendors."""
    KIMI = "kimi"
    QWEN = "qwen"
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass
class Usage:
    """Token usage statistics."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    @classmethod
    def from_openai(cls, usage) -> "Usage":
        """Create from OpenAI SDK usage object."""
        if not usage:
            return cls()
        return cls(
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
    
    @classmethod
    def from_gemini(cls, metadata) -> "Usage":
        """Create from Gemini SDK usage metadata."""
        if not metadata:
            return cls()
        prompt = getattr(metadata, "prompt_token_count", None)
        completion = getattr(metadata, "candidates_token_count", None)
        total = None
        if prompt is not None and completion is not None:
            total = prompt + completion
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )
    
    @classmethod
    def from_dashscope(cls, usage: Optional[Dict]) -> "Usage":
        """Create from Dashscope SDK usage dict."""
        if not usage:
            return cls()
        return cls(
            prompt_tokens=usage.get("input_tokens"),
            completion_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        )


@dataclass
class Response:
    """
    AI response wrapper.
    
    Attributes:
        content: Raw AI response content, unmodified.
        usage: Token usage statistics.
        raw: Original SDK response object (for advanced users).
    """
    content: str
    usage: Usage
    raw: Optional[Any] = None
    
    def __str__(self) -> str:
        return self.content
