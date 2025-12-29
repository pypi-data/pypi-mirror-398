"""Google AI provider implementation.

Provides access to Gemini models via the Google AI API with support
for Gemini 2.0 Flash Thinking.

Uses obra.model_registry as the single source of truth for:
- Default model selection
- Context window sizes
- Output token budget calculation

Example:
    >>> provider = GoogleProvider()
    >>> provider.initialize(api_key="...")
    >>> response = provider.generate(
    ...     prompt="Analyze this code",
    ...     model="gemini-2.5-flash",
    ... )

Related:
    - https://ai.google.dev/gemini-api/docs
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


class GoogleProvider(LLMProvider):
    """Google AI provider for Gemini models.

    Supports:
    - Gemini 2.5 Pro, Flash, Flash Lite
    - Gemini 3 Pro Preview
    - JSON response format
    - Streaming output

    Model configuration is sourced from obra.model_registry:
    - Default model: Dynamically from registry (currently "gemini-2.5-pro")
    - Output budget: Calculated from model's context window (~80K for 1M context)

    Thread-safety:
        Thread-safe (stateless API calls).
    """

    # Provider identifier for registry lookups
    PROVIDER_NAME = "google"

    # Fallbacks if registry lookup fails
    _FALLBACK_MODEL = "gemini-2.5-flash"
    _FALLBACK_OUTPUT_BUDGET = 16_384

    # Special model for thinking mode
    THINKING_MODEL = "gemini-2.0-flash-thinking-exp"

    def __init__(self) -> None:
        """Initialize provider."""
        self._client: Any = None
        self._api_key: str | None = None

    @property
    def default_model(self) -> str:
        """Default model from registry (falls back to gemini-2.5-flash)."""
        return get_default_model(self.PROVIDER_NAME) or self._FALLBACK_MODEL

    def _get_output_budget(self, model: str) -> int:
        """Get output token budget for model from registry.

        Args:
            model: Model identifier

        Returns:
            Output token budget (80K for Gemini Pro/Flash, 16K fallback)
        """
        budget = get_default_output_budget(self.PROVIDER_NAME, model)
        return budget if budget else self._FALLBACK_OUTPUT_BUDGET

    def initialize(self, **kwargs) -> None:
        """Initialize with API key.

        Args:
            api_key: Google AI API key (or uses GOOGLE_API_KEY env var)
            **kwargs: Additional configuration
        """
        self._api_key = kwargs.get("api_key") or os.environ.get("GOOGLE_API_KEY")

        if not self._api_key:
            logger.warning("No Google API key configured")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._client = genai
            logger.info("Google AI provider initialized")
        except ImportError:
            logger.error("google-generativeai package not installed: pip install google-generativeai")

    def generate(self, **kwargs) -> dict[str, Any]:
        """Generate completion via Google AI API.

        Args:
            prompt: Input prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model_suffix: Use thinking model suffix
            response_format: "text" or "json"

        Returns:
            Dict with content and metadata
        """
        if self._client is None:
            return self._error_response("Google AI client not initialized")

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))
        model_suffix = kwargs.get("model_suffix")
        response_format = kwargs.get("response_format", "text")

        # Apply thinking model suffix if specified
        if model_suffix == "-thinking":
            model = self.THINKING_MODEL

        try:
            # Configure generation
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            # JSON mode
            if response_format == "json":
                generation_config["response_mime_type"] = "application/json"

            # Create model instance
            genai_model = self._client.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_prompt if system_prompt else None,
            )

            # Generate
            response = genai_model.generate_content(prompt)

            # Extract content
            content = response.text if response.text else ""

            # Token usage (estimated if not provided)
            tokens_used = 0
            if hasattr(response, "usage_metadata"):
                tokens_used = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )

            return {
                "content": content,
                "tokens_used": tokens_used,
                "thinking_tokens": 0,
                "model": model,
                "finish_reason": "stop",
            }

        except Exception as e:
            logger.error(f"Google AI API error: {e}")
            return self._error_response(str(e))

    def generate_stream(self, **kwargs) -> Iterator[str]:
        """Generate with streaming.

        Args:
            **kwargs: Same as generate()

        Yields:
            Text chunks
        """
        if self._client is None:
            yield "[Error: Google AI client not initialized]"
            return

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))

        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            genai_model = self._client.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_prompt if system_prompt else None,
            )

            response = genai_model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Google AI streaming error: {e}")
            yield f"[Error: {e!s}]"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count.

        Args:
            text: Text to count

        Returns:
            Estimated tokens
        """
        # Gemini uses ~4 characters per token on average
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


__all__ = ["GoogleProvider"]
