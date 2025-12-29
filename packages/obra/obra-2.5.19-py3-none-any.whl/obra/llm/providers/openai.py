"""OpenAI provider implementation.

Provides access to GPT and O1 models via the OpenAI API with support
for reasoning effort (extended thinking for O1 models).

Uses obra.model_registry as the single source of truth for:
- Default model selection
- Context window sizes
- Output token budget calculation

Example:
    >>> provider = OpenAIProvider()
    >>> provider.initialize(api_key="sk-...")
    >>> response = provider.generate(
    ...     prompt="Analyze this code",
    ...     model="gpt-4o",
    ... )

Related:
    - https://platform.openai.com/docs/api-reference/chat
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


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for GPT and O1 models.

    Supports:
    - GPT-4o, GPT-5.x series
    - O1/O3 models with reasoning_effort
    - JSON response format
    - Streaming output

    Model configuration is sourced from obra.model_registry:
    - Default model: Dynamically from registry (currently auto-select/gpt-4o)
    - Output budget: Calculated from model's context window (~30-48K)

    Thread-safety:
        Thread-safe (stateless API calls).
    """

    # Provider identifier for registry lookups
    PROVIDER_NAME = "openai"

    # Fallbacks if registry lookup fails
    _FALLBACK_MODEL = "gpt-5.1"
    _FALLBACK_OUTPUT_BUDGET = 16_384

    # Models that support reasoning effort
    O1_MODELS = {"o1", "o1-mini", "o1-preview", "o3"}

    def __init__(self) -> None:
        """Initialize provider."""
        self._client: Any = None
        self._api_key: str | None = None

    @property
    def default_model(self) -> str:
        """Default model from registry (falls back to gpt-4o)."""
        return get_default_model(self.PROVIDER_NAME) or self._FALLBACK_MODEL

    def _get_output_budget(self, model: str) -> int:
        """Get output token budget for model from registry.

        Args:
            model: Model identifier

        Returns:
            Output token budget (30K+ for GPT models, 16K fallback)
        """
        budget = get_default_output_budget(self.PROVIDER_NAME, model)
        return budget if budget else self._FALLBACK_OUTPUT_BUDGET

    def initialize(self, **kwargs) -> None:
        """Initialize with API key.

        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
            **kwargs: Additional configuration
        """
        self._api_key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")

        if not self._api_key:
            logger.warning("No OpenAI API key configured")
            return

        try:
            import openai
            self._client = openai.OpenAI(api_key=self._api_key)
            logger.info("OpenAI provider initialized")
        except ImportError:
            logger.error("openai package not installed: pip install openai")

    def generate(self, **kwargs) -> dict[str, Any]:
        """Generate completion via OpenAI API.

        Args:
            prompt: Input prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            reasoning_effort: Reasoning effort for O1 models ("low", "medium", "high")
            response_format: "text" or "json"

        Returns:
            Dict with content and metadata
        """
        if self._client is None:
            return self._error_response("OpenAI client not initialized")

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))
        reasoning_effort = kwargs.get("reasoning_effort")
        response_format = kwargs.get("response_format", "text")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request params
        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        # O1 models don't use temperature but support reasoning_effort
        is_o1 = any(model.startswith(o1) for o1 in self.O1_MODELS)
        if is_o1:
            if reasoning_effort:
                request_params["reasoning_effort"] = reasoning_effort
        else:
            request_params["temperature"] = temperature

        # JSON response format
        if response_format == "json":
            request_params["response_format"] = {"type": "json_object"}

        try:
            response = self._client.chat.completions.create(**request_params)

            # Extract content
            content = response.choices[0].message.content or ""

            # Calculate tokens
            usage = response.usage
            total_tokens = usage.total_tokens if usage else 0

            return {
                "content": content,
                "tokens_used": total_tokens,
                "thinking_tokens": 0,  # OpenAI doesn't expose this separately
                "model": model,
                "finish_reason": response.choices[0].finish_reason or "stop",
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._error_response(str(e))

    def generate_stream(self, **kwargs) -> Iterator[str]:
        """Generate with streaming.

        Args:
            **kwargs: Same as generate()

        Yields:
            Text chunks
        """
        if self._client is None:
            yield "[Error: OpenAI client not initialized]"
            return

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            stream = self._client.chat.completions.create(**request_params)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"[Error: {e!s}]"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count.

        Args:
            text: Text to count

        Returns:
            Estimated tokens
        """
        # Try to use tiktoken if available
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.default_model)
            return len(encoding.encode(text))
        except (ImportError, KeyError):
            # Fallback: ~4 characters per token
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


__all__ = ["OpenAIProvider"]
