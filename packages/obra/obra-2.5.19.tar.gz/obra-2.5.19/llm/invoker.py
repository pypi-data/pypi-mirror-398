"""Unified LLM invocation layer with structured output support.

This module provides the LLMInvoker class that provides a consistent interface
for invoking LLMs across different providers (Anthropic, OpenAI, Google, Ollama).

Features:
    - Provider abstraction (single interface, multiple backends)
    - Extended thinking support via ThinkingModeAdapter
    - Structured output parsing
    - Automatic retries with exponential backoff
    - Token tracking for context management

Example:
    >>> from obra.llm import LLMInvoker, ThinkingLevel
    >>> invoker = LLMInvoker()
    >>> result = invoker.invoke(
    ...     prompt="Analyze this code",
    ...     provider="anthropic",
    ...     thinking_level=ThinkingLevel.HIGH,
    ... )
    >>> print(result.content)
    >>> print(f"Tokens used: {result.tokens_used}")

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md
    - obra/llm/thinking_mode.py
    - obra/llm/providers/
"""

import logging
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from obra.llm.thinking_mode import (
    THINKING_LEVEL_TOKENS,
    ThinkingLevel,
    ThinkingMode,
    ThinkingModeAdapter,
)

if TYPE_CHECKING:
    from obra.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class InvocationResult:
    """Result from LLM invocation.

    Attributes:
        content: Generated content
        tokens_used: Total tokens used
        thinking_tokens: Tokens used for thinking (if applicable)
        provider: Provider that generated the response
        model: Model used
        duration_seconds: Time taken for invocation
        success: Whether invocation succeeded
        error_message: Error message if failed
        raw_response: Raw provider response for debugging
    """

    content: str = ""
    tokens_used: int = 0
    thinking_tokens: int = 0
    provider: str = ""
    model: str = ""
    duration_seconds: float = 0.0
    success: bool = True
    error_message: str = ""
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "tokens_used": self.tokens_used,
            "thinking_tokens": self.thinking_tokens,
            "provider": self.provider,
            "model": self.model,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message,
        }


class LLMInvoker:
    """Unified LLM invocation with provider abstraction.

    Provides a consistent interface for invoking LLMs across different
    providers while handling thinking mode, retries, and structured output.

    Example:
        >>> invoker = LLMInvoker()
        >>> result = invoker.invoke(
        ...     prompt="Analyze this code",
        ...     provider="anthropic",
        ...     thinking_level=ThinkingLevel.HIGH,
        ... )

    Thread-safety:
        Thread-safe through ThinkingModeAdapter's per-session configuration.

    Attributes:
        thinking_adapter: ThinkingModeAdapter for extended thinking
        providers: Dictionary of registered providers
        default_provider: Default provider name
    """

    def __init__(
        self,
        thinking_adapter: ThinkingModeAdapter | None = None,
        default_provider: str = "anthropic",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize LLMInvoker.

        Args:
            thinking_adapter: Optional ThinkingModeAdapter
            default_provider: Default provider name
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (exponential backoff)
        """
        self._thinking_adapter = thinking_adapter or ThinkingModeAdapter()
        self._default_provider = default_provider
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._providers: dict[str, LLMProvider] = {}

        logger.debug(
            f"LLMInvoker initialized: default_provider={default_provider}, "
            f"max_retries={max_retries}"
        )

    def register_provider(self, name: str, provider: "LLMProvider") -> None:
        """Register an LLM provider.

        Args:
            name: Provider name (e.g., "anthropic", "openai")
            provider: Provider instance
        """
        self._providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")

    def invoke(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        thinking_level: str | None = None,
        response_format: str = "text",
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> InvocationResult:
        """Invoke LLM with unified interface.

        Args:
            prompt: Input prompt
            provider: Provider name (uses default if not specified)
            model: Model to use (provider default if not specified)
            thinking_level: Thinking level (off, minimal, standard, high, maximum)
            response_format: Expected response format ("text" or "json")
            system_prompt: Optional system prompt
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            InvocationResult with content and metadata
        """
        start_time = time.time()
        provider_name = provider or self._default_provider

        # Generate session ID for thinking mode
        session_id = f"invoke-{uuid.uuid4().hex[:8]}"

        try:
            # Get provider
            llm_provider = self._get_provider(provider_name)
            if llm_provider is None:
                return InvocationResult(
                    success=False,
                    error_message=f"Provider not registered: {provider_name}",
                    provider=provider_name,
                    duration_seconds=time.time() - start_time,
                )

            # Get model (provider default if not specified)
            model_name = model or llm_provider.default_model

            # Configure thinking mode if specified
            thinking_params = {}
            if thinking_level:
                thinking_params = self._configure_thinking(
                    session_id=session_id,
                    model=model_name,
                    thinking_level=thinking_level,
                    provider=provider_name,
                )

            # Build request parameters
            request_params = {
                "prompt": prompt,
                "model": model_name,
                "response_format": response_format,
                **thinking_params,
            }

            if system_prompt:
                request_params["system_prompt"] = system_prompt
            if temperature is not None:
                request_params["temperature"] = temperature
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens

            request_params.update(kwargs)

            # Invoke with retries
            response = self._invoke_with_retry(llm_provider, request_params)

            duration = time.time() - start_time
            return InvocationResult(
                content=response.get("content", ""),
                tokens_used=response.get("tokens_used", 0),
                thinking_tokens=response.get("thinking_tokens", 0),
                provider=provider_name,
                model=model_name,
                duration_seconds=duration,
                success=True,
                raw_response=response,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM invocation failed: {e}")
            return InvocationResult(
                success=False,
                error_message=str(e),
                provider=provider_name,
                duration_seconds=duration,
            )

        finally:
            # Clean up thinking session
            self._thinking_adapter.cleanup_session(session_id)

    def invoke_stream(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        thinking_level: str | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Invoke LLM with streaming output.

        Args:
            prompt: Input prompt
            provider: Provider name
            model: Model to use
            thinking_level: Thinking level
            **kwargs: Additional parameters

        Yields:
            Text chunks as they're generated
        """
        provider_name = provider or self._default_provider
        session_id = f"stream-{uuid.uuid4().hex[:8]}"

        try:
            llm_provider = self._get_provider(provider_name)
            if llm_provider is None:
                yield f"[Error: Provider not registered: {provider_name}]"
                return

            model_name = model or llm_provider.default_model

            # Configure thinking mode
            thinking_params = {}
            if thinking_level:
                thinking_params = self._configure_thinking(
                    session_id=session_id,
                    model=model_name,
                    thinking_level=thinking_level,
                    provider=provider_name,
                )

            request_params = {
                "prompt": prompt,
                "model": model_name,
                **thinking_params,
                **kwargs,
            }

            yield from llm_provider.generate_stream(**request_params)

        finally:
            self._thinking_adapter.cleanup_session(session_id)

    def estimate_tokens(self, text: str, provider: str | None = None) -> int:
        """Estimate token count for text.

        Args:
            text: Text to count tokens for
            provider: Provider for provider-specific counting

        Returns:
            Estimated token count
        """
        provider_name = provider or self._default_provider
        llm_provider = self._get_provider(provider_name)

        if llm_provider is not None:
            return llm_provider.estimate_tokens(text)

        # Fallback: rough estimate (4 chars per token)
        return len(text) // 4

    def is_available(self, provider: str | None = None) -> bool:
        """Check if provider is available.

        Args:
            provider: Provider name to check

        Returns:
            True if provider is available
        """
        provider_name = provider or self._default_provider
        llm_provider = self._get_provider(provider_name)

        if llm_provider is None:
            return False

        return llm_provider.is_available()

    def _get_provider(self, name: str) -> Optional["LLMProvider"]:
        """Get provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        if name not in self._providers:
            # Try lazy loading
            provider = self._lazy_load_provider(name)
            if provider:
                self._providers[name] = provider

        return self._providers.get(name)

    def _lazy_load_provider(self, name: str) -> Optional["LLMProvider"]:
        """Lazy load a provider.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        try:
            if name == "anthropic":
                from obra.llm.providers.anthropic import AnthropicProvider
                return AnthropicProvider()
            if name == "openai":
                from obra.llm.providers.openai import OpenAIProvider
                return OpenAIProvider()
            if name == "google":
                from obra.llm.providers.google import GoogleProvider
                return GoogleProvider()
            if name == "ollama":
                from obra.llm.providers.ollama import OllamaProvider
                return OllamaProvider()
            logger.warning(f"Unknown provider: {name}")
            return None
        except ImportError as e:
            logger.warning(f"Failed to import provider {name}: {e}")
            return None

    def _configure_thinking(
        self,
        session_id: str,
        model: str,
        thinking_level: str,
        provider: str,
    ) -> dict[str, Any]:
        """Configure thinking mode for session.

        Args:
            session_id: Session ID
            model: Model name
            thinking_level: Thinking level string
            provider: Provider name

        Returns:
            Provider-specific thinking parameters
        """
        # Convert level string to ThinkingLevel enum
        level_map = {
            "off": ThinkingLevel.OFF,
            "minimal": ThinkingLevel.MINIMAL,
            "standard": ThinkingLevel.STANDARD,
            "high": ThinkingLevel.HIGH,
            "maximum": ThinkingLevel.MAXIMUM,
        }
        level = level_map.get(thinking_level.lower(), ThinkingLevel.STANDARD)

        # Get token budget for level
        budget_tokens = THINKING_LEVEL_TOKENS.get(level, 8000)

        # Convert to ThinkingMode
        if level == ThinkingLevel.OFF:
            mode = ThinkingMode.DISABLED
        elif level in (ThinkingLevel.HIGH, ThinkingLevel.MAXIMUM):
            mode = ThinkingMode.EXTENDED
        else:
            mode = ThinkingMode.STANDARD

        # Configure adapter
        self._thinking_adapter.configure(
            session_id=session_id,
            model=model,
            mode=mode,
            thinking_budget_tokens=budget_tokens,
        )

        # Get provider-specific params
        return self._thinking_adapter.get_provider_params(
            session_id=session_id,
            provider=provider,
            interface="api",
        )

    def _invoke_with_retry(
        self,
        provider: "LLMProvider",
        request_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke provider with retry logic.

        Args:
            provider: Provider instance
            request_params: Request parameters

        Returns:
            Provider response

        Raises:
            Exception: If all retries fail
        """
        last_error: Exception | None = None
        delay = self._retry_delay

        for attempt in range(self._max_retries):
            try:
                return provider.generate(**request_params)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM invocation attempt {attempt + 1}/{self._max_retries} "
                    f"failed: {e}"
                )

                if attempt < self._max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

        raise last_error or Exception("All retry attempts failed")


__all__ = [
    "InvocationResult",
    "LLMInvoker",
]
