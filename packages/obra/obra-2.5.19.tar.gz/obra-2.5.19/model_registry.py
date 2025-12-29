"""Unified Model Registry - Single Source of Truth for LLM Configurations.

This module provides a centralized registry of LLM provider configurations,
model definitions, and validation functions. All consumers (obra package,
DObra agents, interactive mode) should import from this module.

Example:
    >>> from obra.model_registry import validate_model, get_cli_args
    >>> result = validate_model("anthropic", "sonnet")
    >>> result.valid
    True
    >>> get_cli_args("anthropic", "opus")
    ['--model', 'opus']

Schema Version:
    Major: Breaking changes to data structures
    Minor: New models/fields added
    Patch: Fixes to existing data

Migration Note:
    This module was migrated from obra_client.model_registry as part of
    CLIENT-SUNSET-001. The obra_client package is deprecated.
"""

import sys
import warnings
from dataclasses import dataclass, field
from enum import Enum

# Schema version for breaking change detection
REGISTRY_VERSION = "1.0.0"


def _warn_if_legacy_loaded() -> None:
    """Warn if deprecated obra_client.model_registry is also loaded.

    This helps detect mixed imports during migration from obra_client to obra.
    The warning is emitted once per session.
    """
    if "obra_client.model_registry" in sys.modules:
        warnings.warn(
            "Both 'obra.model_registry' and 'obra_client.model_registry' are loaded. "
            "The obra_client package is deprecated. Please update all imports to use "
            "'from obra.model_registry import ...' instead of "
            "'from obra_client.model_registry import ...'",
            DeprecationWarning,
            stacklevel=3,
        )


# Check for legacy module on import
_warn_if_legacy_loaded()


class ModelStatus(Enum):
    """Status of a model in the registry.

    TESTED: Verified working via CLI testing
    DOCUMENTED: From official docs, not yet tested
    DEPRECATED: Known to be removed or failing
    RESTRICTED: Requires specific auth (e.g., API key only)
    """

    TESTED = "tested"
    DOCUMENTED = "documented"
    DEPRECATED = "deprecated"
    RESTRICTED = "restricted"


@dataclass
class ModelInfo:
    """Information about a specific model.

    Attributes:
        id: Model identifier to pass to CLI
        display_name: Human-readable name for UI
        status: Verification status
        resolves_to: Canonical model ID (for aliases)
        description: Brief description
        note: Additional context (e.g., "Requires API key")
        context_window: Token limit if known
        capabilities: Future feature flags (vision, tools, streaming)
    """

    id: str
    display_name: str
    status: ModelStatus
    resolves_to: str | None = None
    description: str | None = None
    note: str | None = None
    context_window: int | None = None
    capabilities: set[str] = field(default_factory=set)

    @property
    def is_usable(self) -> bool:
        """Whether this model can be used (not deprecated)."""
        return self.status != ModelStatus.DEPRECATED


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider.

    Attributes:
        name: Display name (e.g., "Anthropic")
        cli: CLI command (e.g., "claude")
        flag: Model flag (e.g., "--model")
        default_model: Default model ID (None = auto-select)
        models: Available models
        invalid_patterns: Known invalid formats
        oauth_supported: Whether OAuth auth works
        api_key_env: Env var for API key auth
    """

    name: str
    cli: str
    flag: str
    default_model: str | None
    models: dict[str, ModelInfo]
    invalid_patterns: set[str] = field(default_factory=set)
    oauth_supported: bool = True
    api_key_env: str | None = None


# =============================================================================
# Model Registry Data - December 2025
# =============================================================================

MODEL_REGISTRY: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        name="Anthropic",
        cli="claude",
        flag="--model",
        default_model="sonnet",
        oauth_supported=True,
        api_key_env="ANTHROPIC_API_KEY",
        invalid_patterns={
            "sonnet-4",
            "Sonnet-4-5",
            "claude-sonnet-4",
            "claude-3-5-sonnet-*",  # Deprecated format
        },
        models={
            # Aliases (tested)
            "sonnet": ModelInfo(
                id="sonnet",
                display_name="Sonnet 4.5",
                status=ModelStatus.TESTED,
                resolves_to="claude-sonnet-4-5-20250929",
                description="Fast, capable - recommended for most tasks",
                context_window=200_000,
            ),
            "opus": ModelInfo(
                id="opus",
                display_name="Opus 4.5",
                status=ModelStatus.TESTED,
                resolves_to="claude-opus-4-5-20251101",
                description="Most capable, slower",
                context_window=200_000,
            ),
            "haiku": ModelInfo(
                id="haiku",
                display_name="Haiku 4.5",
                status=ModelStatus.TESTED,
                resolves_to="claude-haiku-4-5-20251001",
                description="Fastest, lighter tasks",
                context_window=200_000,
            ),
            # Full model IDs (tested)
            "claude-sonnet-4-5": ModelInfo(
                id="claude-sonnet-4-5",
                display_name="Sonnet 4.5 (explicit)",
                status=ModelStatus.TESTED,
                resolves_to="claude-sonnet-4-5-20250929",
                context_window=200_000,
            ),
            "claude-opus-4-5": ModelInfo(
                id="claude-opus-4-5",
                display_name="Opus 4.5 (explicit)",
                status=ModelStatus.TESTED,
                resolves_to="claude-opus-4-5-20251101",
                context_window=200_000,
            ),
            "claude-haiku-4-5": ModelInfo(
                id="claude-haiku-4-5",
                display_name="Haiku 4.5 (explicit)",
                status=ModelStatus.TESTED,
                resolves_to="claude-haiku-4-5-20251001",
                context_window=200_000,
            ),
            # Legacy model (tested)
            "claude-sonnet-4-20250514": ModelInfo(
                id="claude-sonnet-4-20250514",
                display_name="Sonnet 4.0",
                status=ModelStatus.TESTED,
                description="Previous generation",
                context_window=200_000,
            ),
        },
    ),
    "google": ProviderConfig(
        name="Google",
        cli="gemini",
        flag="--model",
        default_model="gemini-3-flash-preview",
        oauth_supported=True,
        api_key_env="GOOGLE_API_KEY",
        invalid_patterns=set(),
        models={
            # Aliases (documented)
            "gemini-3": ModelInfo(
                id="gemini-3",
                display_name="Gemini 3 Flash (Preview)",
                status=ModelStatus.DOCUMENTED,
                resolves_to="gemini-3-flash-preview",
                description="Next-gen balanced model - recommended",
                note="Requires preview features enabled",
                context_window=1_000_000,
            ),
            "gemini-2.5-pro": ModelInfo(
                id="gemini-2.5-pro",
                display_name="Gemini 2.5 Pro",
                status=ModelStatus.TESTED,
                description="Complex reasoning tasks",
                context_window=1_000_000,
            ),
            "gemini-2.5-flash": ModelInfo(
                id="gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                status=ModelStatus.TESTED,
                description="Balanced speed and reasoning",
                context_window=1_000_000,
            ),
            "gemini-2.5-flash-lite": ModelInfo(
                id="gemini-2.5-flash-lite",
                display_name="Gemini 2.5 Flash Lite",
                status=ModelStatus.DOCUMENTED,
                description="Quick, simple tasks",
                context_window=128_000,
            ),
            "gemini-3-pro-preview": ModelInfo(
                id="gemini-3-pro-preview",
                display_name="Gemini 3 Pro Preview",
                status=ModelStatus.DOCUMENTED,
                description="Next-gen complex reasoning",
                note="Requires preview features enabled",
                context_window=1_000_000,
            ),
            "gemini-3-flash-preview": ModelInfo(
                id="gemini-3-flash-preview",
                display_name="Gemini 3 Flash Preview",
                status=ModelStatus.DOCUMENTED,
                description="Next-gen balanced speed and reasoning",
                note="Requires preview features enabled",
                context_window=1_000_000,
            ),
        },
    ),
    "ollama": ProviderConfig(
        name="Ollama",
        cli="ollama",
        flag="run",  # ollama run <model>
        default_model="qwen2.5-coder:32b",
        oauth_supported=False,
        api_key_env=None,  # Local, no API key
        invalid_patterns=set(),
        models={
            "phi3:mini": ModelInfo(
                id="phi3:mini",
                display_name="Phi-3 Mini",
                status=ModelStatus.DOCUMENTED,
                description="Ultra-compact model for constrained environments",
                context_window=4_096,
            ),
            "qwen2.5-coder:3b": ModelInfo(
                id="qwen2.5-coder:3b",
                display_name="Qwen 2.5 Coder 3B",
                status=ModelStatus.DOCUMENTED,
                description="Small but capable coding model",
                context_window=8_192,
            ),
            "qwen2.5-coder:7b": ModelInfo(
                id="qwen2.5-coder:7b",
                display_name="Qwen 2.5 Coder 7B",
                status=ModelStatus.DOCUMENTED,
                description="Balanced performance/resource model",
                context_window=16_384,
            ),
            "qwen2.5-coder:14b": ModelInfo(
                id="qwen2.5-coder:14b",
                display_name="Qwen 2.5 Coder 14B",
                status=ModelStatus.DOCUMENTED,
                description="Good balance for medium contexts",
                context_window=32_768,
            ),
            "qwen2.5-coder:32b": ModelInfo(
                id="qwen2.5-coder:32b",
                display_name="Qwen 2.5 Coder 32B",
                status=ModelStatus.TESTED,
                description="Production-grade local model (recommended)",
                context_window=128_000,
            ),
        },
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        cli="codex",
        flag="--model",
        default_model="gpt-5.2-codex",
        oauth_supported=True,
        api_key_env="OPENAI_API_KEY",
        invalid_patterns=set(),
        models={
            # Aliases (tested)
            "codex": ModelInfo(
                id="codex",
                display_name="Codex (GPT-5.2)",
                status=ModelStatus.TESTED,
                resolves_to="gpt-5.2-codex",
                description="Latest frontier agentic coding model - recommended",
                context_window=400_000,
            ),
            "gpt-5.2": ModelInfo(
                id="gpt-5.2",
                display_name="GPT-5.2",
                status=ModelStatus.TESTED,
                resolves_to="gpt-5.2-codex",
                description="Latest frontier agentic coding model",
                context_window=400_000,
            ),
            # Full model IDs (tested)
            "gpt-5.2-codex": ModelInfo(
                id="gpt-5.2-codex",
                display_name="GPT-5.2 Codex",
                status=ModelStatus.TESTED,
                description="Latest frontier agentic coding model",
                context_window=400_000,
            ),
            "gpt-5.1-codex-max": ModelInfo(
                id="gpt-5.1-codex-max",
                display_name="GPT-5.1 Codex Max",
                status=ModelStatus.TESTED,
                description="Codex-optimized flagship for deep and fast reasoning",
                context_window=400_000,
            ),
            "gpt-5.1-codex-mini": ModelInfo(
                id="gpt-5.1-codex-mini",
                display_name="GPT-5.1 Codex Mini",
                status=ModelStatus.TESTED,
                description="Optimized for codex - cheaper, faster, but less capable",
                context_window=400_000,
            ),
            "gpt-5.1": ModelInfo(
                id="gpt-5.1",
                display_name="GPT-5.1",
                status=ModelStatus.TESTED,
                description="Coding and agentic tasks",
                context_window=400_000,
            ),
            "gpt-4o": ModelInfo(
                id="gpt-4o",
                display_name="GPT-4o",
                status=ModelStatus.DEPRECATED,
                note="Legacy model - use gpt-5.1 or gpt-5.2 instead",
                context_window=128_000,
            ),
            "o3": ModelInfo(
                id="o3",
                display_name="O3",
                status=ModelStatus.DEPRECATED,
                note="Not in active use",
                description="Reasoning-focused model",
                context_window=200_000,
            ),
        },
    ),
}


# =============================================================================
# Registry API Functions
# =============================================================================


@dataclass
class ValidationResult:
    """Result of model validation.

    Attributes:
        valid: Whether the model is valid for use
        model_id: The model identifier that was validated
        status: Model status from registry (if found)
        warning: Warning message (model works but has caveats)
        error: Error message (model will not work)
    """

    valid: bool
    model_id: str
    status: ModelStatus | None = None
    warning: str | None = None
    error: str | None = None


def get_provider(provider: str) -> ProviderConfig | None:
    """Get provider configuration.

    Args:
        provider: Provider name (anthropic, google, openai)

    Returns:
        ProviderConfig or None if provider not found
    """
    return MODEL_REGISTRY.get(provider)


def get_provider_names() -> list[str]:
    """Get list of supported provider names.

    Returns:
        List of provider names (e.g., ["anthropic", "google", "openai"])
    """
    return list(MODEL_REGISTRY.keys())


def get_provider_models(
    provider: str,
    include_deprecated: bool = False,
    only_tested: bool = False,
) -> list[ModelInfo]:
    """Get available models for a provider.

    Args:
        provider: Provider name (anthropic, google, openai)
        include_deprecated: Include deprecated models
        only_tested: Only return models with TESTED status

    Returns:
        List of ModelInfo objects

    Example:
        >>> models = get_provider_models("anthropic", only_tested=True)
        >>> [m.id for m in models]
        ['sonnet', 'opus', 'haiku', 'claude-sonnet-4-5', ...]
    """
    config = MODEL_REGISTRY.get(provider)
    if not config:
        return []

    models = []
    for model in config.models.values():
        if not include_deprecated and model.status == ModelStatus.DEPRECATED:
            continue
        if only_tested and model.status != ModelStatus.TESTED:
            continue
        models.append(model)

    return models


def validate_model(provider: str, model: str) -> ValidationResult:
    """Validate a model identifier for a provider.

    Checks:
    1. Provider exists
    2. Model doesn't match invalid patterns
    3. Model is in registry (with status)
    4. Unknown models are allowed with warning (future-proofing)

    Args:
        provider: Provider name
        model: Model identifier to validate

    Returns:
        ValidationResult with validity and any warnings/errors

    Example:
        >>> result = validate_model("anthropic", "sonnet")
        >>> result.valid, result.status
        (True, ModelStatus.TESTED)

        >>> result = validate_model("anthropic", "sonnet-4")
        >>> result.valid, result.error
        (False, "Invalid model format: sonnet-4...")
    """
    config = MODEL_REGISTRY.get(provider)
    if not config:
        return ValidationResult(
            valid=False,
            model_id=model,
            error=f"Unknown provider: {provider}. Valid providers: {', '.join(get_provider_names())}",
        )

    # Check invalid patterns
    for pattern in config.invalid_patterns:
        if pattern.endswith("*"):
            if model.startswith(pattern[:-1]):
                return ValidationResult(
                    valid=False,
                    model_id=model,
                    error=f"Invalid model format: {model}. Pattern '{pattern}' is not supported.",
                )
        elif model == pattern:
            return ValidationResult(
                valid=False,
                model_id=model,
                error=f"Invalid model format: {model}. Try 'sonnet', 'opus', or 'haiku' instead.",
            )

    # Check if model is in registry
    model_info = config.models.get(model)
    if model_info:
        warning = None
        if model_info.status == ModelStatus.DEPRECATED:
            warning = f"Model '{model}' is deprecated and may not work."
        elif model_info.status == ModelStatus.RESTRICTED:
            warning = model_info.note or f"Model '{model}' may have access restrictions."
        elif model_info.status == ModelStatus.DOCUMENTED:
            warning = f"Model '{model}' is documented but not tested with Obra."

        return ValidationResult(
            valid=True,
            model_id=model,
            status=model_info.status,
            warning=warning,
        )

    # Model not in registry - allow but warn (supports future models)
    return ValidationResult(
        valid=True,
        model_id=model,
        warning=f"Model '{model}' is not in Obra's tested model list. It may or may not work.",
    )


def get_cli_args(provider: str, model: str | None) -> list[str]:
    """Get CLI arguments for a provider and model.

    Args:
        provider: Provider name
        model: Model identifier (None for default)

    Returns:
        List of CLI arguments (e.g., ["--model", "sonnet"])

    Example:
        >>> get_cli_args("anthropic", "opus")
        ['--model', 'opus']
        >>> get_cli_args("anthropic", None)
        ['--model', 'sonnet']  # default
        >>> get_cli_args("openai", None)
        []  # auto-select
    """
    config = MODEL_REGISTRY.get(provider)
    if not config:
        return []

    # Use default if no model specified
    effective_model = model or config.default_model

    if effective_model:
        return [config.flag, effective_model]

    return []  # No model flag (auto-select)


def resolve_alias(provider: str, model: str) -> str:
    """Resolve a model alias to its canonical form.

    Args:
        provider: Provider name
        model: Model identifier (possibly an alias)

    Returns:
        Canonical model ID (or original if not an alias)

    Example:
        >>> resolve_alias("anthropic", "sonnet")
        'claude-sonnet-4-5-20250929'
        >>> resolve_alias("anthropic", "unknown-model")
        'unknown-model'
    """
    config = MODEL_REGISTRY.get(provider)
    if not config:
        return model

    model_info = config.models.get(model)
    if model_info and model_info.resolves_to:
        return model_info.resolves_to

    return model


def get_default_model(provider: str) -> str | None:
    """Get the default model for a provider.

    Args:
        provider: Provider name

    Returns:
        Default model ID or None if auto-select

    Example:
        >>> get_default_model("anthropic")
        'sonnet'
        >>> get_default_model("openai")
        None  # auto-select
    """
    config = MODEL_REGISTRY.get(provider)
    return config.default_model if config else None


def get_model_context_window(provider: str, model: str) -> int | None:
    """Get the context window size for a model.

    Args:
        provider: Provider name (anthropic, google, openai)
        model: Model identifier

    Returns:
        Context window size in tokens, or None if unknown

    Example:
        >>> get_model_context_window("openai", "gpt-5.2")
        400000
        >>> get_model_context_window("anthropic", "sonnet")
        200000
    """
    config = MODEL_REGISTRY.get(provider)
    if not config:
        return None

    model_info = config.models.get(model)
    if model_info:
        return model_info.context_window

    return None


# =============================================================================
# Context Budget Calculation
# =============================================================================

# Hard safety limits
MIN_RESERVED_OUTPUT = 30_000  # Always reserve at least 30K for output
MAX_RESERVED_OUTPUT = 100_000  # Never reserve more than 100K (wasteful on huge models)
DEFAULT_CONTEXT_WINDOW = 128_000  # Fallback if model context unknown


def calculate_max_prompt_tokens(
    context_window: int | None,
    min_reserved: int = MIN_RESERVED_OUTPUT,
    max_reserved: int = MAX_RESERVED_OUTPUT,
) -> int:
    """Calculate maximum tokens for prompt based on model context window.

    Uses tiered percentages with hard safety limits:
    - 500K+: 92% for prompt (8% reserved)
    - 200K-500K: 88% for prompt (12% reserved)
    - 100K-200K: 82% for prompt (18% reserved)
    - <100K: 75% for prompt (25% reserved)

    Safety limits ensure:
    - At least min_reserved tokens for output (default: 30K)
    - At most max_reserved tokens reserved (default: 100K)

    Args:
        context_window: Model's context window size in tokens
        min_reserved: Minimum tokens to reserve for output
        max_reserved: Maximum tokens to reserve for output

    Returns:
        Maximum tokens available for prompt

    Example:
        >>> calculate_max_prompt_tokens(400_000)  # GPT-5.2
        352000  # 400K * 0.88 = 352K
        >>> calculate_max_prompt_tokens(200_000)  # Claude Sonnet
        176000  # 200K * 0.88 = 176K
        >>> calculate_max_prompt_tokens(50_000)   # Small model
        37500   # 50K * 0.75 = 37.5K
        >>> calculate_max_prompt_tokens(None)     # Unknown
        105600  # 128K fallback * 0.82 = 105K
    """
    # Use fallback if context window unknown
    if context_window is None:
        context_window = DEFAULT_CONTEXT_WINDOW

    # Tiered percentage based on context window size
    if context_window >= 500_000:
        ratio = 0.92  # 8% reserved for 500K+ models
    elif context_window >= 200_000:
        ratio = 0.88  # 12% reserved for 200K-500K models
    elif context_window >= 100_000:
        ratio = 0.82  # 18% reserved for 100K-200K models
    else:
        ratio = 0.75  # 25% reserved for <100K models

    # Calculate based on percentage
    max_prompt = int(context_window * ratio)

    # Apply hard safety limits
    reserved = context_window - max_prompt

    if reserved < min_reserved:
        # Not reserving enough - enforce minimum
        max_prompt = context_window - min_reserved
    elif reserved > max_reserved:
        # Reserving too much - cap it
        max_prompt = context_window - max_reserved

    # Ensure we don't go negative (for very small context windows)
    return max(max_prompt, 0)


def get_max_prompt_tokens_for_model(provider: str, model: str) -> int:
    """Get maximum prompt tokens for a specific model.

    Convenience function that looks up context window and calculates max prompt.

    Args:
        provider: Provider name (anthropic, google, openai)
        model: Model identifier

    Returns:
        Maximum tokens available for prompt

    Example:
        >>> get_max_prompt_tokens_for_model("openai", "gpt-5.2")
        352000
        >>> get_max_prompt_tokens_for_model("anthropic", "sonnet")
        176000
    """
    context_window = get_model_context_window(provider, model)
    return calculate_max_prompt_tokens(context_window)


# Default output budget fallback (when model not in registry)
DEFAULT_OUTPUT_BUDGET = 16_384


def get_default_output_budget(provider: str, model: str) -> int:
    """Get recommended output token budget for a model.

    Calculates the output budget as the reserved space from
    calculate_max_prompt_tokens(). This is the inverse of max prompt tokens:
    output_budget = context_window - max_prompt_tokens

    For models with known context windows, this gives dynamic output limits:
    - 50K context: ~30K output (min safety limit applied)
    - 128K context: ~30K output (min safety limit applied)
    - 200K context: ~24K output → bumped to 30K
    - 400K context: ~48K output
    - 1M context: ~80K output

    Args:
        provider: Provider name (anthropic, google, openai, ollama)
        model: Model identifier

    Returns:
        Recommended output token budget. Falls back to DEFAULT_OUTPUT_BUDGET
        (16K) if model context window is unknown.

    Example:
        >>> get_default_output_budget("anthropic", "sonnet")
        30000  # 200K context, min safety limit
        >>> get_default_output_budget("google", "gemini-2.5-pro")
        80000  # 1M context
        >>> get_default_output_budget("openai", "gpt-5.2")
        48000  # 400K context
    """
    context_window = get_model_context_window(provider, model)
    if context_window is None:
        return DEFAULT_OUTPUT_BUDGET

    max_prompt = calculate_max_prompt_tokens(context_window)
    return context_window - max_prompt
