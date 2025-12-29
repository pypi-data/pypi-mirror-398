"""Ollama provider implementation.

Provides access to local models via Ollama with support for
thinking mode on compatible models.

Uses obra.model_registry as the single source of truth for:
- Default model selection
- Context window sizes
- Output token budget calculation

Example:
    >>> provider = OllamaProvider()
    >>> provider.initialize(endpoint="http://localhost:11434")
    >>> response = provider.generate(
    ...     prompt="Analyze this code",
    ...     model="qwen2.5-coder:32b",
    ... )

Related:
    - https://ollama.ai/
    - obra/llm/thinking_mode.py
    - obra/model_registry.py (authoritative model config)
"""

import logging
import os
from collections.abc import Iterator
from typing import Any

import requests

from obra.llm.providers.base import LLMProvider
from obra.model_registry import get_default_model, get_default_output_budget

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local models.

    Supports:
    - Any model available in Ollama
    - Thinking mode for compatible models
    - JSON response format
    - Streaming output

    Model configuration is sourced from obra.model_registry:
    - Default model: Dynamically from registry (currently "qwen2.5-coder:32b")
    - Output budget: Calculated from model's context window (~30K for 128K context)

    Thread-safety:
        Thread-safe (stateless HTTP calls).
    """

    # Provider identifier for registry lookups
    PROVIDER_NAME = "ollama"

    # Fallbacks if registry lookup fails
    _FALLBACK_MODEL = "qwen2.5-coder:32b"
    _FALLBACK_OUTPUT_BUDGET = 16_384

    DEFAULT_ENDPOINT = "http://localhost:11434"
    DEFAULT_TIMEOUT = 120

    # Models known to support thinking
    THINKING_MODELS = {
        "qwq",
        "deepseek-r1",
        "granite3.1-dense",
    }

    def __init__(self) -> None:
        """Initialize provider."""
        self._endpoint: str = self.DEFAULT_ENDPOINT
        self._timeout: int = self.DEFAULT_TIMEOUT

    @property
    def default_model(self) -> str:
        """Default model from registry (falls back to qwen2.5-coder:32b)."""
        return get_default_model(self.PROVIDER_NAME) or self._FALLBACK_MODEL

    def _get_output_budget(self, model: str) -> int:
        """Get output token budget for model from registry.

        Args:
            model: Model identifier

        Returns:
            Output token budget (varies by model size, 16K fallback)
        """
        budget = get_default_output_budget(self.PROVIDER_NAME, model)
        return budget if budget else self._FALLBACK_OUTPUT_BUDGET

    def initialize(self, **kwargs) -> None:
        """Initialize with endpoint configuration.

        Args:
            endpoint: Ollama API endpoint (or uses OLLAMA_HOST env var)
            timeout: Request timeout in seconds
            **kwargs: Additional configuration
        """
        self._endpoint = (
            kwargs.get("endpoint") or
            os.environ.get("OLLAMA_HOST") or
            self.DEFAULT_ENDPOINT
        )
        self._timeout = kwargs.get("timeout", self.DEFAULT_TIMEOUT)

        logger.info(f"Ollama provider initialized: {self._endpoint}")

    def generate(self, **kwargs) -> dict[str, Any]:
        """Generate completion via Ollama API.

        Args:
            prompt: Input prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate (num_predict)
            thinking: Enable thinking mode for compatible models
            response_format: "text" or "json"

        Returns:
            Dict with content and metadata
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))
        thinking = kwargs.get("thinking", False)
        response_format = kwargs.get("response_format", "text")

        # Build request
        request_data: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            request_data["system"] = system_prompt

        # JSON format
        if response_format == "json":
            request_data["format"] = "json"

        # Thinking mode for compatible models
        if thinking and self._supports_thinking(model):
            # Add thinking prompt prefix
            request_data["prompt"] = f"<think>\n{prompt}\n</think>"

        try:
            url = f"{self._endpoint}/api/generate"
            response = requests.post(
                url,
                json=request_data,
                timeout=self._timeout,
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("response", "")

            # Calculate tokens
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens

            return {
                "content": content,
                "tokens_used": total_tokens,
                "thinking_tokens": 0,
                "model": model,
                "finish_reason": "stop" if data.get("done") else "length",
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            }

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self._endpoint}")
            return self._error_response(f"Cannot connect to Ollama at {self._endpoint}")
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self._timeout}s")
            return self._error_response(f"Request timed out after {self._timeout}s")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return self._error_response(str(e))

    def generate_stream(self, **kwargs) -> Iterator[str]:
        """Generate with streaming.

        Args:
            **kwargs: Same as generate()

        Yields:
            Text chunks
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_model)
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", self._get_output_budget(model))

        request_data: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            request_data["system"] = system_prompt

        try:
            url = f"{self._endpoint}/api/generate"
            response = requests.post(
                url,
                json=request_data,
                timeout=self._timeout,
                stream=True,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"[Error: {e!s}]"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count.

        Args:
            text: Text to count

        Returns:
            Estimated tokens
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if Ollama is reachable
        """
        try:
            response = requests.get(
                f"{self._endpoint}/api/tags",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        """List available models.

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self._endpoint}/api/tags",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []

    def _supports_thinking(self, model: str) -> bool:
        """Check if model supports thinking mode.

        Args:
            model: Model name

        Returns:
            True if model supports thinking
        """
        model_lower = model.lower()
        return any(t in model_lower for t in self.THINKING_MODELS)

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


__all__ = ["OllamaProvider"]
