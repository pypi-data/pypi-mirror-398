"""Base provider protocol and common types.

This module defines the LLMProvider protocol that all provider
implementations must follow.

Related:
    - obra/llm/invoker.py
    - src/plugins/base.py (CLI reference)
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderResponse:
    """Response from LLM provider.

    Attributes:
        content: Generated content
        tokens_used: Total tokens used
        thinking_tokens: Tokens used for thinking (if applicable)
        model: Model used
        finish_reason: Reason for completion
        raw_response: Raw provider response
    """

    content: str = ""
    tokens_used: int = 0
    thinking_tokens: int = 0
    model: str = ""
    finish_reason: str = ""
    raw_response: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All providers must implement this interface to work with LLMInvoker.

    Example:
        >>> class MyProvider(LLMProvider):
        ...     def initialize(self, **kwargs):
        ...         self._api_key = kwargs.get("api_key")
        ...
        ...     def generate(self, **kwargs) -> Dict[str, Any]:
        ...         # Implementation
        ...         pass
    """

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""

    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """Initialize provider with configuration.

        Args:
            **kwargs: Provider-specific configuration
                - api_key: API key for authentication
                - endpoint: API endpoint URL
                - timeout: Request timeout
        """

    @abstractmethod
    def generate(self, **kwargs) -> dict[str, Any]:
        """Generate completion.

        Args:
            **kwargs: Generation parameters
                - prompt: Input prompt
                - model: Model to use
                - system_prompt: System prompt
                - temperature: Temperature (0.0-2.0)
                - max_tokens: Maximum tokens
                - response_format: Expected format ("text" or "json")
                - budget_tokens: Thinking budget (Anthropic)
                - reasoning_effort: Reasoning effort (OpenAI)

        Returns:
            Dict with content, tokens_used, and other metadata
        """

    @abstractmethod
    def generate_stream(self, **kwargs) -> Iterator[str]:
        """Generate with streaming output.

        Args:
            **kwargs: Same as generate()

        Yields:
            Text chunks as generated
        """

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if provider is configured and reachable
        """

    def get_model_info(self) -> dict[str, Any]:
        """Get information about provider/model.

        Returns:
            Dict with provider info
        """
        return {
            "provider": self.__class__.__name__,
            "default_model": self.default_model,
        }


__all__ = [
    "LLMProvider",
    "ProviderResponse",
]
