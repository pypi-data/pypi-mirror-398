"""Anthropic provider implementation.

Provides access to Claude models via the Anthropic API with support
for extended thinking mode.

Uses obra.model_registry as the single source of truth for:
- Default model selection
- Context window sizes
- Output token budget calculation

Example:
    >>> provider = AnthropicProvider()
    >>> provider.initialize(api_key="sk-...")
    >>> response = provider.generate(
    ...     prompt="Analyze this code",
    ...     model="sonnet",
    ...     budget_tokens=16000,  # Extended thinking
    ... )

Related:
    - https://docs.anthropic.com/claude/reference/messages_post
    - obra/llm/thinking_mode.py
    - obra/model_registry.py (authoritative model config)
"""

import logging
import os
from collections.abc import Iterator
from typing import Any

from obra.llm.providers.base import LLMProvider
from obra.model_registry import get_default_model, get_default_output_budget

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider for Claude models.

    Supports:
    - Claude 4.5 Sonnet, Opus, Haiku (and earlier versions)
    - Extended thinking with budget_tokens
    - JSON response format
    - Streaming output

    Model configuration is sourced from obra.model_registry:
    - Default model: Dynamically from registry (currently "sonnet")
    - Output budget: Calculated from model's context window (~30K for 200K context)

    Thread-safety:
        Thread-safe (stateless API calls).
    """

    # Provider identifier for registry lookups
    PROVIDER_NAME = "anthropic"

    # Fallbacks if registry lookup fails
    _FALLBACK_MODEL = "sonnet"
    _FALLBACK_OUTPUT_BUDGET = 16_384

    def __init__(self) -> None:
        """Initialize provider."""
        self._client: Any = None
        self._api_key: str | None = None

    @property
    def default_model(self) -> str:
        """Default model from registry (falls back to sonnet)."""
        return get_default_model(self.PROVIDER_NAME) or self._FALLBACK_MODEL

    def _get_output_budget(self, model: str) -> int:
        """Get output token budget for model from registry.

        Args:
            model: Model identifier

        Returns:
            Output token budget (30K+ for Claude models, 16K fallback)
        """
        budget = get_default_output_budget(self.PROVIDER_NAME, model)
        return budget if budget else self._FALLBACK_OUTPUT_BUDGET

    def initialize(self, **kwargs) -> None:
        """Initialize with API key.

        Args:
            api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)
            **kwargs: Additional configuration
        """
        self._api_key = kwargs.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")

        if not self._api_key:
            logger.warning("No Anthropic API key configured")
            return

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
            logger.info("Anthropic provider initialized")
        except ImportError:
            logger.error("anthropic package not installed: pip install anthropic")

    def generate(self, **kwargs) -> dict[str, Any]:
        """Generate completion via Anthropic API.

        Args:
            prompt: Input prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            budget_tokens: Thinking budget for extended thinking
            response_format: "text" or "json"

        Returns:
            Dict with content and metadata
        """
        if self._client is None:
            return self._error_response("Anthropic client not initialized")

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))
        budget_tokens = kwargs.get("budget_tokens", 0)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Build request params
        request_params: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        # Extended thinking configuration
        if budget_tokens > 0:
            # Extended thinking requires temperature=1.0
            request_params["temperature"] = 1.0
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget_tokens,
            }
        else:
            request_params["temperature"] = temperature

        try:
            response = self._client.messages.create(**request_params)

            # Extract content
            content = ""
            thinking_tokens = 0

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "thinking":
                    # Track thinking tokens if available
                    if hasattr(block, "thinking"):
                        thinking_tokens += len(block.thinking) // 4

            # Calculate tokens
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            return {
                "content": content,
                "tokens_used": total_tokens,
                "thinking_tokens": thinking_tokens,
                "model": model,
                "finish_reason": response.stop_reason or "end_turn",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._error_response(str(e))

    def generate_stream(self, **kwargs) -> Iterator[str]:
        """Generate with streaming.

        Args:
            **kwargs: Same as generate()

        Yields:
            Text chunks
        """
        if self._client is None:
            yield "[Error: Anthropic client not initialized]"
            return

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))
        budget_tokens = kwargs.get("budget_tokens", 0)

        messages = [{"role": "user", "content": prompt}]

        request_params: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        if budget_tokens > 0:
            request_params["temperature"] = 1.0
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget_tokens,
            }
        else:
            request_params["temperature"] = temperature

        try:
            with self._client.messages.stream(**request_params) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"[Error: {e!s}]"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count.

        Args:
            text: Text to count

        Returns:
            Estimated tokens (using ~4 chars per token)
        """
        # Rough estimate: Claude uses ~4 characters per token
        return len(text) // 4

    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if API key is configured and client initialized
        """
        return self._client is not None

    def _error_response(self, message: str) -> dict[str, Any]:
        """Create error response.

        Args:
            message: Error message

        Returns:
            Error response dict
        """
        return {
            "content": "",
            "tokens_used": 0,
            "error": message,
        }


__all__ = ["AnthropicProvider"]
