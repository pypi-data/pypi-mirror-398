"""ThinkingModeAdapter for provider-agnostic extended thinking abstraction.

This module provides:
- ThinkingMode enum for mode control (AUTO, EXTENDED, STANDARD, DISABLED)
- ThinkingLevel enum for level abstraction
- ThinkingConfig dataclass for per-session configuration
- ThinkingModeAdapter for thread-safe thinking mode management

The adapter translates unified thinking levels into provider-specific
parameters, enabling consistent extended thinking across providers.

Provider Schemas:
- Anthropic: budget_tokens parameter (1024-128000)
- OpenAI: reasoning_effort parameter ("low", "medium", "high")
- Google: model_suffix "-thinking" for Gemini 2.0 Flash Thinking
- Ollama: thinking=True boolean for supported models

Example:
    >>> adapter = ThinkingModeAdapter()
    >>> adapter.configure(
    ...     session_id="ses-123",
    ...     model="claude-3-opus-20240229",
    ...     mode=ThinkingMode.EXTENDED,
    ...     thinking_budget_tokens=16000,
    ... )
    >>> params = adapter.get_provider_params("ses-123", "anthropic")
    >>> params
    {'budget_tokens': 16000}

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md
    - src/refinement/thinking_adapter.py (CLI reference)
    - obra/llm/invoker.py
"""

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ThinkingMode(str, Enum):
    """Extended thinking mode control.

    AUTO: Let provider decide thinking depth based on task
    EXTENDED: Request maximum thinking (highest token budget)
    STANDARD: Normal reasoning (moderate token budget)
    DISABLED: No extended thinking
    """

    AUTO = "auto"
    EXTENDED = "extended"
    STANDARD = "standard"
    DISABLED = "disabled"


class ThinkingLevel(str, Enum):
    """Thinking level naming convention.

    Aligned across all features:
    - off: Disabled (0 tokens)
    - minimal: Light reasoning (1024 tokens)
    - standard: Normal reasoning (8000 tokens)
    - high: Deep reasoning (16000 tokens)
    - maximum: Maximum reasoning (31999 tokens - Claude limit)
    """

    OFF = "off"
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


# Token budgets for each level
THINKING_LEVEL_TOKENS: dict[ThinkingLevel, int] = {
    ThinkingLevel.OFF: 0,
    ThinkingLevel.MINIMAL: 1024,
    ThinkingLevel.STANDARD: 8000,
    ThinkingLevel.HIGH: 16000,
    ThinkingLevel.MAXIMUM: 31999,
}


@dataclass
class ThinkingConfig:
    """Configuration for extended thinking mode.

    Attributes:
        model: Model ID (must support extended thinking for EXTENDED mode)
        mode: Thinking mode (AUTO, EXTENDED, STANDARD, DISABLED)
        thinking_budget_tokens: Max tokens for thinking (1024-128000)
        temperature: Must be 1.0 for extended thinking
        streaming: Whether to stream thinking output
        created_at: When configuration was created
    """

    model: str
    mode: ThinkingMode = ThinkingMode.AUTO
    thinking_budget_tokens: int = 10000
    temperature: float = 1.0
    streaming: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.mode == ThinkingMode.EXTENDED and self.temperature != 1.0:
            raise ValueError("Extended thinking requires temperature=1.0")
        if self.thinking_budget_tokens < 0:
            raise ValueError("thinking_budget_tokens must be non-negative")


class ThinkingModeAdapter:
    """Thread-safe adapter for extended thinking mode.

    Stores per-session configuration to avoid conflicts in concurrent sessions.
    Supports multiple LLM providers with their specific thinking parameters.

    Thread Safety:
    - Configuration stored per session_id
    - Lock protects config dict access
    - Safe for concurrent session operations

    Example:
        >>> adapter = ThinkingModeAdapter()
        >>> adapter.configure(
        ...     session_id="ses-123",
        ...     model="claude-3-opus-20240229",
        ...     mode=ThinkingMode.EXTENDED,
        ... )
        >>> params = adapter.get_provider_params("ses-123", "anthropic")
        >>> params
        {'budget_tokens': 10000}
    """

    # Provider-specific thinking parameter schemas
    PROVIDER_SCHEMAS: dict[str, dict[str, Any]] = {
        "anthropic": {
            "api": {
                "extended_thinking": {"budget_tokens": int},
                "levels": {
                    ThinkingLevel.OFF: {"budget_tokens": 0},
                    ThinkingLevel.MINIMAL: {"budget_tokens": 1024},
                    ThinkingLevel.STANDARD: {"budget_tokens": 8000},
                    ThinkingLevel.HIGH: {"budget_tokens": 16000},
                    ThinkingLevel.MAXIMUM: {"budget_tokens": 31999},
                },
            },
            "cli": {
                # Claude Code uses --thinking flag
                "extended_thinking": {"flag": "--thinking"},
            },
        },
        "openai": {
            "api": {
                # OpenAI o1 models use reasoning_effort
                "extended_thinking": {"reasoning_effort": str},
                "levels": {
                    ThinkingLevel.OFF: {"reasoning_effort": None},
                    ThinkingLevel.MINIMAL: {"reasoning_effort": "low"},
                    ThinkingLevel.STANDARD: {"reasoning_effort": "medium"},
                    ThinkingLevel.HIGH: {"reasoning_effort": "high"},
                    ThinkingLevel.MAXIMUM: {"reasoning_effort": "high"},
                },
            },
        },
        "google": {
            "api": {
                # Gemini 2.0 Flash Thinking has implicit thinking
                "extended_thinking": {"model_suffix": "-thinking"},
            },
        },
        "ollama": {
            "api": {
                # Ollama uses thinking parameter for supported models
                "extended_thinking": {"thinking": bool},
                "levels": {
                    ThinkingLevel.OFF: {"thinking": False},
                    ThinkingLevel.MINIMAL: {"thinking": True},
                    ThinkingLevel.STANDARD: {"thinking": True},
                    ThinkingLevel.HIGH: {"thinking": True},
                    ThinkingLevel.MAXIMUM: {"thinking": True},
                },
            },
            "local": {
                "extended_thinking": {"thinking": bool},
                "levels": {
                    ThinkingLevel.OFF: {"thinking": False},
                    ThinkingLevel.MINIMAL: {"thinking": True},
                    ThinkingLevel.STANDARD: {"thinking": True},
                    ThinkingLevel.HIGH: {"thinking": True},
                    ThinkingLevel.MAXIMUM: {"thinking": True},
                },
            },
        },
    }

    def __init__(self) -> None:
        """Initialize adapter."""
        self._lock = threading.Lock()
        self._configs: dict[str, ThinkingConfig] = {}

    def configure(
        self,
        session_id: str,
        model: str,
        mode: ThinkingMode = ThinkingMode.AUTO,
        thinking_budget_tokens: int = 10000,
        temperature: float = 1.0,
        streaming: bool = True,
    ) -> None:
        """Configure thinking mode for a session. Thread-safe.

        Args:
            session_id: Session ID to configure
            model: Model ID
            mode: Thinking mode
            thinking_budget_tokens: Max tokens for thinking
            temperature: Must be 1.0 for extended thinking
            streaming: Whether to stream thinking output

        Raises:
            ValueError: If temperature != 1.0 for EXTENDED mode
        """
        config = ThinkingConfig(
            model=model,
            mode=mode,
            thinking_budget_tokens=thinking_budget_tokens,
            temperature=temperature,
            streaming=streaming,
        )

        with self._lock:
            self._configs[session_id] = config

    def get_config(self, session_id: str) -> ThinkingConfig:
        """Get configuration for session. Thread-safe.

        Args:
            session_id: Session ID to retrieve config for

        Returns:
            ThinkingConfig for the session

        Raises:
            RuntimeError: If no config exists for session
        """
        with self._lock:
            if session_id not in self._configs:
                raise RuntimeError(f"No thinking config for session {session_id}")
            return self._configs[session_id]

    def has_config(self, session_id: str) -> bool:
        """Check if configuration exists for session. Thread-safe.

        Args:
            session_id: Session ID to check

        Returns:
            True if config exists, False otherwise
        """
        with self._lock:
            return session_id in self._configs

    def get_provider_params(
        self,
        session_id: str,
        provider: str,
        interface: str = "api",
    ) -> dict[str, Any]:
        """Get provider-specific thinking parameters. Thread-safe.

        DISABLED mode returns empty params.

        Args:
            session_id: Session ID
            provider: Provider name (anthropic, openai, google, ollama)
            interface: Interface type (api, cli, local)

        Returns:
            Provider-specific parameter dictionary.
            Empty dict for DISABLED mode or unknown provider.
        """
        config = self.get_config(session_id)

        # DISABLED mode: return empty params
        if config.mode == ThinkingMode.DISABLED:
            return {}

        # Unknown provider: return empty params
        if provider not in self.PROVIDER_SCHEMAS:
            return {}

        provider_schema = self.PROVIDER_SCHEMAS[provider].get(interface, {})
        if not provider_schema:
            return {}

        # Get level-specific params if available
        level = self._mode_to_level(config.mode, config.thinking_budget_tokens)
        levels = provider_schema.get("levels", {})

        if level in levels:
            params = dict(levels[level])
            # Filter out None values
            return {k: v for k, v in params.items() if v is not None}

        # Fallback: use budget_tokens directly for Anthropic
        if provider == "anthropic" and interface == "api":
            return {"budget_tokens": config.thinking_budget_tokens}

        return {}

    def wrap_request(
        self,
        session_id: str,
        request_params: dict[str, Any],
        provider: str = "anthropic",
        interface: str = "api",
    ) -> dict[str, Any]:
        """Add thinking mode parameters to request. Thread-safe.

        Args:
            session_id: Session ID
            request_params: Existing request parameters
            provider: Provider name
            interface: Interface type

        Returns:
            Request params with thinking parameters added
        """
        thinking_params = self.get_provider_params(session_id, provider, interface)

        # Merge thinking params into request
        result = dict(request_params)
        if thinking_params:
            result.update(thinking_params)

        return result

    def cleanup_session(self, session_id: str) -> None:
        """Remove session config. Call on session completion. Thread-safe.

        Args:
            session_id: Session ID to clean up
        """
        with self._lock:
            self._configs.pop(session_id, None)

    def get_active_sessions(self) -> int:
        """Get count of active session configurations. Thread-safe.

        Returns:
            Number of sessions with active configs
        """
        with self._lock:
            return len(self._configs)

    def _mode_to_level(
        self,
        mode: ThinkingMode,
        budget_tokens: int,
    ) -> ThinkingLevel:
        """Convert mode and budget to thinking level.

        Args:
            mode: Thinking mode
            budget_tokens: Token budget

        Returns:
            Appropriate ThinkingLevel
        """
        if mode == ThinkingMode.DISABLED:
            return ThinkingLevel.OFF
        if mode == ThinkingMode.STANDARD:
            return ThinkingLevel.STANDARD
        if mode == ThinkingMode.EXTENDED:
            # Map budget to level
            if budget_tokens >= 31999:
                return ThinkingLevel.MAXIMUM
            if budget_tokens >= 16000:
                return ThinkingLevel.HIGH
            if budget_tokens >= 8000:
                return ThinkingLevel.STANDARD
            if budget_tokens >= 1024:
                return ThinkingLevel.MINIMAL
            return ThinkingLevel.OFF
        # AUTO
        return ThinkingLevel.STANDARD


__all__ = [
    "THINKING_LEVEL_TOKENS",
    "ThinkingConfig",
    "ThinkingLevel",
    "ThinkingMode",
    "ThinkingModeAdapter",
]
