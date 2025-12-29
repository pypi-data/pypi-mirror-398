"""Configuration management for Obra.

Handles terms acceptance state and client configuration stored in
~/.obra/client-config.yaml.

Example:
    from obra.config import load_config, save_config, get_api_base_url

    config = load_config()
    api_url = get_api_base_url()
"""

import logging
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

# Module logger
logger = logging.getLogger(__name__)

# Legal document versions - must match bundled documents
TERMS_VERSION = "2.1"
PRIVACY_VERSION = "1.3"

# Config file path
CONFIG_PATH = Path.home() / ".obra" / "client-config.yaml"

# Firebase configuration
# This is the Firebase Web API Key (public, safe to include in client)
# Used for custom token → ID token exchange via Firebase Auth REST API
# Project: obra-205b0
FIREBASE_API_KEY = "AIzaSyDHQNxR_4BQvK_W_i83H2hNH4p2OKFi2wM"  # pragma: allowlist secret

# Default API URL (production)
# Can be overridden via OBRA_API_BASE_URL environment variable
DEFAULT_API_BASE_URL = "https://us-central1-obra-205b0.cloudfunctions.net"

# Default LLM execution timeout (30 minutes)
# Can be overridden via OBRA_LLM_TIMEOUT environment variable
DEFAULT_LLM_TIMEOUT = 1800

# Default maximum iterations for orchestration loop
# Can be overridden via client-config.yaml max_iterations setting
DEFAULT_MAX_ITERATIONS = 100

# Network timeout configuration (C17)
# Default timeout for general network operations (seconds)
DEFAULT_NETWORK_TIMEOUT = 30
# Timeout for LLM API operations (seconds)
DEFAULT_LLM_API_TIMEOUT = 120


def get_api_base_url() -> str:
    """Get API base URL with environment variable override support.

    Resolution order:
    1. OBRA_API_BASE_URL environment variable
    2. api_base_url from config file
    3. DEFAULT_API_BASE_URL constant

    Returns:
        API base URL string

    Example:
        # Override for local development
        export OBRA_API_BASE_URL="http://localhost:5001/obra-205b0/us-central1"

        # Override for staging
        export OBRA_API_BASE_URL="https://us-central1-obra-staging.cloudfunctions.net"
    """
    # Priority 1: Environment variable
    env_url = os.environ.get("OBRA_API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    # Priority 2: Config file
    config = load_config()
    config_url = config.get("api_base_url")
    if config_url:
        return config_url.rstrip("/")

    # Priority 3: Default constant
    return DEFAULT_API_BASE_URL


def get_llm_timeout() -> int:
    """Get LLM execution timeout in seconds.

    Resolution order:
    1. OBRA_LLM_TIMEOUT environment variable
    2. llm_timeout from config file
    3. DEFAULT_LLM_TIMEOUT constant (1800s = 30 min)

    Returns:
        Timeout in seconds

    Example:
        # Override for long-running tasks
        export OBRA_LLM_TIMEOUT=3600

        # Or set in ~/.obra/client-config.yaml:
        # llm_timeout: 3600
    """
    # Priority 1: Environment variable
    env_timeout = os.environ.get("OBRA_LLM_TIMEOUT")
    if env_timeout:
        try:
            return int(env_timeout)
        except ValueError:
            pass  # Fall through to config file

    # Priority 2: Config file
    config = load_config()
    config_timeout = config.get("llm_timeout")
    if config_timeout:
        return int(config_timeout)

    # Priority 3: Default constant
    return DEFAULT_LLM_TIMEOUT


def get_max_iterations() -> int:
    """Get maximum orchestration loop iterations.

    Resolution order:
    1. OBRA_MAX_ITERATIONS environment variable
    2. max_iterations from config file
    3. DEFAULT_MAX_ITERATIONS constant (100)

    Returns:
        Maximum iterations

    Example:
        # Override for complex tasks
        export OBRA_MAX_ITERATIONS=150

        # Or set in ~/.obra/client-config.yaml:
        # max_iterations: 150
    """
    # Priority 1: Environment variable
    env_max_iterations = os.environ.get("OBRA_MAX_ITERATIONS")
    if env_max_iterations:
        try:
            return int(env_max_iterations)
        except ValueError:
            pass  # Fall through to config file

    # Priority 2: Config file
    config = load_config()
    config_max_iterations = config.get("max_iterations")
    if config_max_iterations:
        return int(config_max_iterations)

    # Priority 3: Default constant
    return DEFAULT_MAX_ITERATIONS


# =============================================================================
# LLM Configuration
# =============================================================================

# Supported LLM providers
LLM_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic",
        "description": "Claude models",
        "cli": "claude",  # Claude Code CLI
        "models": ["default", "sonnet", "opus", "haiku"],
        "default_model": "default",
        "oauth_env_var": None,  # OAuth uses browser-based login
        "api_key_env_var": "ANTHROPIC_API_KEY",  # pragma: allowlist secret
    },
    "google": {
        "name": "Google",
        "description": "Gemini models",
        "cli": "gemini",  # Gemini CLI
        # Dec 2025: Gemini 3 preview + 2.5 family (gemini-2.0 deprecated)
        # See: docs/reference/llm-providers/gemini-cli-models.md
        "models": [
            "default",  # Same as "auto" - let system choose
            "auto",  # Gemini CLI's auto mode (explicit)
            "gemini-3-pro-preview",  # Latest Gemini 3 (preview)
            "gemini-2.5-pro",  # Production, 1M context
            "gemini-2.5-flash",  # Balance of speed/reasoning
            "gemini-2.5-flash-lite",  # Simple tasks, quick
        ],
        "default_model": "default",
        "oauth_env_var": None,  # OAuth uses browser-based login (gemini auth login)
        "api_key_env_var": "GEMINI_API_KEY",  # pragma: allowlist secret
    },
    "openai": {
        "name": "OpenAI",
        "description": "Codex / GPT models",
        "cli": "codex",  # OpenAI Codex CLI
        # Dec 2025: GPT-5.x family (models below 5.1 are deprecated)
        "models": [
            "default",
            "gpt-5.2",  # Latest frontier (400K context)
            "gpt-5.1-codex-max",  # Codex default, flagship
            "gpt-5.1-codex",  # Codex optimized
            "gpt-5.1-codex-mini",  # Faster, cheaper
            "gpt-5.1",  # General reasoning
        ],
        "default_model": "default",
        "oauth_env_var": None,  # OAuth uses browser-based login (codex --login)
        "api_key_env_var": "OPENAI_API_KEY",  # pragma: allowlist secret
    },
}

# Auth methods
LLM_AUTH_METHODS = {
    "oauth": {
        "name": "OAuth (Flat Rate)",
        "description": "Subscription-based, fixed monthly cost",
        "recommended_model": "default",
        "note": "Recommended - inherits provider's optimal model",
    },
    "api_key": {
        "name": "API Key (Token Billing)",
        "description": "Pay per token usage",
        "recommended_model": None,  # User should choose
        "note": "⚠️ API Key method is currently untested",
    },
}

DEFAULT_PROVIDER = "anthropic"
DEFAULT_AUTH_METHOD = "oauth"
DEFAULT_MODEL = "default"
DEFAULT_THINKING_LEVEL = "medium"

# Abstract thinking levels (user-facing, provider-agnostic)
# Maps to provider-specific parameters in build_llm_args()
THINKING_LEVELS = ["off", "low", "medium", "high", "maximum"]

# Provider-specific thinking level mappings
# See docs/reference/llm-providers/ for official documentation
THINKING_LEVEL_MAP = {
    "anthropic": {
        # Claude Code V2 - only "ultrathink" keyword allocates thinking tokens
        # Intermediate levels (think, think hard) were deprecated in V2
        # See: docs/reference/llm-providers/claude-code-thinking.md
        "off": None,  # No thinking, don't use ultrathink
        "low": None,  # No intermediate levels exist
        "medium": None,  # No intermediate levels exist
        "high": None,  # No intermediate levels exist
        "maximum": "ultrathink",  # Only keyword that allocates thinking tokens (31,999)
    },
    "openai": {
        # Codex CLI model_reasoning_effort values
        # See: docs/reference/llm-providers/openai-codex-reasoning.md
        "off": "minimal",  # Minimize reasoning overhead
        "low": "low",
        "medium": "medium",  # Default
        "high": "high",
        "maximum": "xhigh",  # Only gpt-5.1-codex-max and gpt-5.2
    },
    "google": {
        # Gemini CLI - no reasoning effort control available
        "off": None,
        "low": None,
        "medium": None,
        "high": None,
        "maximum": None,
    },
}

# Known model shortcuts for quick switching
# Full model names (e.g., "claude-sonnet-4-5") are passed through
MODEL_SHORTCUTS = {"default", "sonnet", "opus", "haiku"}

# Models that support xhigh/maximum reasoning effort
# Used by get_effective_thinking_value() for fallback logic
XHIGH_SUPPORTED_MODELS: dict[str, set[str]] = {
    "openai": {"gpt-5.2", "gpt-5.1-codex-max"},  # xhigh only on flagship models
    "anthropic": set(),  # All Claude models support ultrathink (prompt keyword)
    "google": set(),  # Gemini has no reasoning effort control
}

# Model name patterns for provider inference (regex)
# Used by infer_provider_from_model() to auto-detect provider
MODEL_PROVIDER_PATTERNS: dict[str, str] = {
    # Anthropic/Claude patterns
    r"^opus$": "anthropic",
    r"^sonnet$": "anthropic",
    r"^haiku$": "anthropic",
    r"^claude": "anthropic",  # claude-*, claude-3-*, etc.
    # OpenAI/Codex patterns
    r"^gpt": "openai",  # gpt-4, gpt-5.2, etc.
    r"^o[134]": "openai",  # o1, o3, o4 models
    r"^codex": "openai",  # codex-*, codex-mini, etc.
    # Google/Gemini patterns
    r"^gemini": "google",  # gemini-2.5-*, gemini-3-*, etc.
}

# Model name prefixes for fast provider inference (non-regex fallback)
MODEL_PROVIDER_PREFIXES: dict[str, str] = {
    "opus": "anthropic",
    "sonnet": "anthropic",
    "haiku": "anthropic",
    "claude": "anthropic",
    "gpt": "openai",
    "o1": "openai",
    "o3": "openai",
    "o4": "openai",
    "codex": "openai",
    "gemini": "google",
}


def infer_provider_from_model(model: str) -> str | None:
    """Infer the LLM provider from a model name.

    Uses regex patterns first (MODEL_PROVIDER_PATTERNS), then falls back
    to prefix matching (MODEL_PROVIDER_PREFIXES).

    Args:
        model: Model name to analyze (e.g., "opus", "gpt-5.2", "gemini-2.5-flash")

    Returns:
        Provider name ("anthropic", "openai", "google") or None if unknown

    Examples:
        >>> infer_provider_from_model("opus")
        'anthropic'
        >>> infer_provider_from_model("gpt-5.2")
        'openai'
        >>> infer_provider_from_model("gemini-2.5-flash")
        'google'
        >>> infer_provider_from_model("custom-model")
        None
    """
    import re  # noqa: PLC0415

    if not model or model == "default":
        return None

    model_lower = model.lower()

    # Try regex patterns first (most precise)
    for pattern, provider in MODEL_PROVIDER_PATTERNS.items():
        if re.match(pattern, model_lower):
            return provider

    # Fall back to prefix matching
    for prefix, provider in MODEL_PROVIDER_PREFIXES.items():
        if model_lower.startswith(prefix):
            return provider

    return None


# =============================================================================
# Provider Health Check
# =============================================================================


@dataclass
class ProviderStatus:
    """Status of an LLM provider's CLI availability.

    Attributes:
        provider: Provider name (anthropic, openai, google)
        installed: Whether the CLI is installed and accessible
        cli_command: The CLI command name
        cli_path: Full path to CLI executable (if installed)
        install_hint: Installation instructions
        docs_url: Documentation URL
    """

    provider: str
    installed: bool
    cli_command: str
    cli_path: str | None = None
    install_hint: str = ""
    docs_url: str = ""


# Provider CLI information for health checking
PROVIDER_CLI_INFO: dict[str, dict[str, str]] = {
    "anthropic": {
        "cli": "claude",
        "install_hint": "npm install -g @anthropic-ai/claude-code",
        "docs_url": "https://docs.anthropic.com/en/docs/claude-code",
        "auth_hint": "claude login",
    },
    "openai": {
        "cli": "codex",
        "install_hint": "npm install -g @openai/codex",
        "docs_url": "https://platform.openai.com/docs/codex-cli",
        "auth_hint": "codex --login",
    },
    "google": {
        "cli": "gemini",
        "install_hint": "npm install -g @google/gemini-cli",
        "docs_url": "https://ai.google.dev/gemini-api/docs/gemini-cli",
        "auth_hint": "gemini auth login",
    },
}


def check_provider_status(provider: str) -> ProviderStatus:
    """Check if an LLM provider's CLI is installed and accessible.

    Uses shutil.which() to locate the CLI executable in PATH.

    Args:
        provider: Provider name (anthropic, openai, google)

    Returns:
        ProviderStatus with installation details

    Examples:
        >>> status = check_provider_status("anthropic")
        >>> if status.installed:
        ...     print(f"Claude CLI at: {status.cli_path}")
        ... else:
        ...     print(f"Install with: {status.install_hint}")
    """
    cli_info = PROVIDER_CLI_INFO.get(provider, {})
    cli_command = cli_info.get("cli", LLM_PROVIDERS.get(provider, {}).get("cli", ""))

    if not cli_command:
        return ProviderStatus(
            provider=provider,
            installed=False,
            cli_command="unknown",
            install_hint=f"Unknown provider: {provider}",
        )

    # Check if CLI is in PATH
    cli_path = shutil.which(cli_command)

    return ProviderStatus(
        provider=provider,
        installed=cli_path is not None,
        cli_command=cli_command,
        cli_path=cli_path,
        install_hint=cli_info.get("install_hint", ""),
        docs_url=cli_info.get("docs_url", ""),
    )


def validate_provider_ready(provider: str) -> None:
    """Validate that a provider's CLI is installed and ready.

    Raises ConfigurationError with installation hints if the CLI is not found.
    This provides a fail-fast check before attempting to use a provider.

    Args:
        provider: Provider name to validate (anthropic, openai, google)

    Raises:
        ConfigurationError: If provider CLI is not installed

    Example:
        >>> try:
        ...     validate_provider_ready("openai")
        ... except ConfigurationError as e:
        ...     print(f"Setup required: {e}")
    """
    from obra.exceptions import ConfigurationError  # noqa: PLC0415

    status = check_provider_status(provider)

    if not status.installed:
        provider_name = LLM_PROVIDERS.get(provider, {}).get("name", provider)
        cli_info = PROVIDER_CLI_INFO.get(provider, {})

        error_msg = f"{provider_name} CLI ({status.cli_command}) not found in PATH."
        details = []

        if status.install_hint:
            details.append(f"Install with: {status.install_hint}")

        auth_hint = cli_info.get("auth_hint")
        if auth_hint:
            details.append(f"Then authenticate: {auth_hint}")

        if status.docs_url:
            details.append(f"See: {status.docs_url}")

        if details:
            error_msg = f"{error_msg}\n\n" + "\n".join(details)

        raise ConfigurationError(error_msg)


def get_thinking_level_notes(
    provider: str,
    thinking_level: str,
    model: str | None = None,
) -> list[str]:
    """Get user-facing notes about thinking level behavior for a provider.

    Provides feedback about how the selected thinking level maps to
    provider-specific behavior, including limitations and recommendations.

    Args:
        provider: LLM provider name
        thinking_level: Abstract thinking level (off, low, medium, high, maximum)
        model: Optional model name for model-specific notes

    Returns:
        List of note strings to display to the user

    Examples:
        >>> get_thinking_level_notes("anthropic", "maximum")
        ['Using "ultrathink" prompt keyword for extended thinking (31,999 tokens)']

        >>> get_thinking_level_notes("google", "high")
        ['Gemini CLI does not support reasoning effort control']

        >>> get_thinking_level_notes("openai", "maximum", "gpt-5.1")
        ['xhigh reasoning not supported on gpt-5.1, using "high" instead']
    """
    notes = []

    # Provider-specific notes
    if provider == "anthropic":
        if thinking_level == "maximum":
            notes.append('Using "ultrathink" prompt keyword for extended thinking (31,999 tokens)')
        elif thinking_level in ("low", "high"):
            notes.append(
                f'Claude Code V2 only supports "off" (no thinking) or "maximum" (ultrathink). '
                f'Level "{thinking_level}" has no effect.'
            )

    elif provider == "openai":
        # Check xhigh support
        if thinking_level == "maximum":
            supported = XHIGH_SUPPORTED_MODELS.get("openai", set())
            if model and model not in supported:
                notes.append(f'xhigh reasoning not supported on {model}, using "high" instead')
                notes.append(f'For xhigh, use: {", ".join(sorted(supported))}')
            else:
                notes.append("Using xhigh reasoning effort for maximum analysis")

    elif provider == "google" and thinking_level != "off":
        notes.append("Gemini CLI does not support reasoning effort control")

    return notes


def get_effective_thinking_value(
    provider: str,
    thinking_level: str,
    model: str | None = None,
) -> str | None:
    """Get the effective provider-specific thinking value with fallback.

    Maps abstract thinking level to provider-specific value, applying
    fallback logic for unsupported configurations (e.g., xhigh → high
    for OpenAI models that don't support xhigh).

    Args:
        provider: LLM provider name
        thinking_level: Abstract thinking level (off, low, medium, high, maximum)
        model: Optional model name for model-specific fallback

    Returns:
        Provider-specific thinking value (e.g., "xhigh", "high", "ultrathink")
        or None if the provider doesn't support the level

    Examples:
        >>> get_effective_thinking_value("openai", "maximum", "gpt-5.2")
        'xhigh'
        >>> get_effective_thinking_value("openai", "maximum", "gpt-5.1")
        'high'  # Fallback - xhigh not supported
        >>> get_effective_thinking_value("anthropic", "maximum")
        'ultrathink'
        >>> get_effective_thinking_value("google", "high")
        None  # No reasoning control
    """
    provider_map = THINKING_LEVEL_MAP.get(provider, {})
    base_value = provider_map.get(thinking_level)

    # Apply fallback logic for OpenAI xhigh
    if provider == "openai" and thinking_level == "maximum":
        supported = XHIGH_SUPPORTED_MODELS.get("openai", set())
        if model and model not in supported:
            # Fall back to high
            return provider_map.get("high", "high")

    return base_value


def validate_model(model: str, provider: str = DEFAULT_PROVIDER) -> str:
    """Validate and normalize a model name.

    Supports two types of model names:
    1. Shortcuts: default, sonnet, opus, haiku (validated against provider)
    2. Full model names: claude-sonnet-4-5, gpt-4o, etc. (passthrough)

    Args:
        model: Model name to validate (shortcut or full name)
        provider: Provider to validate against for shortcuts

    Returns:
        Validated model name (unchanged)

    Raises:
        ValueError: If shortcut is not valid for the given provider
    """
    if not model:
        return DEFAULT_MODEL

    # Shortcuts are validated against provider's model list
    if model in MODEL_SHORTCUTS:
        provider_info = LLM_PROVIDERS.get(provider, LLM_PROVIDERS[DEFAULT_PROVIDER])
        valid_models = provider_info.get("models", [])
        if model not in valid_models:
            raise ValueError(
                f"Model '{model}' not valid for provider '{provider}'. "
                f"Valid: {', '.join(valid_models)}"
            )
        return model

    # Full model names are passed through without validation
    # This allows users to use specific model versions like "claude-sonnet-4-5"
    return model


def resolve_llm_config(
    role: str,
    override_provider: str | None = None,
    override_model: str | None = None,
    override_auth_method: str | None = None,
    override_thinking_level: str | None = None,
) -> dict[str, Any]:
    """Resolve LLM configuration for a role with optional overrides.

    Resolution order (highest to lowest priority):
    1. Session overrides (passed as arguments)
    2. Global config file (~/.obra/client-config.yaml)
    3. Defaults (anthropic, oauth, default, medium)

    Args:
        role: "orchestrator" or "implementation"
        override_provider: Optional provider override (session-only)
        override_model: Optional model override (session-only)
        override_auth_method: Optional auth method override (session-only)
        override_thinking_level: Optional thinking level override (session-only)

    Returns:
        Resolved config dict with provider, auth_method, model, thinking_level keys
        and optional parse retry controls.
    """
    if role not in ("orchestrator", "implementation"):
        raise ValueError(f"Invalid role: {role}")

    # Get base config from global config file
    llm_config = get_llm_config()
    role_config = llm_config.get(role, {})

    # Start with defaults
    resolved = {
        "provider": role_config.get("provider", DEFAULT_PROVIDER),
        "auth_method": role_config.get("auth_method", DEFAULT_AUTH_METHOD),
        "model": role_config.get("model", DEFAULT_MODEL),
        "thinking_level": role_config.get("thinking_level", DEFAULT_THINKING_LEVEL),
        "parse_retry_enabled": role_config.get("parse_retry_enabled", True),
        "parse_retry_providers": role_config.get("parse_retry_providers"),
        "parse_retry_models": role_config.get("parse_retry_models"),
    }

    # Apply overrides (session-only, don't persist)
    if override_provider:
        if override_provider not in LLM_PROVIDERS:
            raise ValueError(f"Invalid provider: {override_provider}")
        resolved["provider"] = override_provider

    if override_auth_method:
        if override_auth_method not in LLM_AUTH_METHODS:
            raise ValueError(f"Invalid auth method: {override_auth_method}")
        resolved["auth_method"] = override_auth_method

    if override_model:
        # Validate model against resolved provider
        resolved["model"] = validate_model(override_model, resolved["provider"])

    if override_thinking_level:
        if override_thinking_level not in THINKING_LEVELS:
            raise ValueError(
                f"Invalid thinking level: {override_thinking_level}. "
                f"Valid: {', '.join(THINKING_LEVELS)}"
            )
        resolved["thinking_level"] = override_thinking_level

    return resolved


def get_llm_config() -> dict[str, Any]:
    """Get LLM configuration from config file.

    Returns:
        Dictionary with LLM config for both orchestrator and implementation:
        {
            "orchestrator": {
                "provider": "anthropic",
                "auth_method": "oauth",
                "model": "default",
                "thinking_level": "medium"
            },
            "implementation": {
                "provider": "anthropic",
                "auth_method": "oauth",
                "model": "default",
                "thinking_level": "medium"
            }
        }
    """
    config = load_config()
    default_config = {
        "orchestrator": {
            "provider": DEFAULT_PROVIDER,
            "auth_method": DEFAULT_AUTH_METHOD,
            "model": DEFAULT_MODEL,
            "thinking_level": DEFAULT_THINKING_LEVEL,
        },
        "implementation": {
            "provider": DEFAULT_PROVIDER,
            "auth_method": DEFAULT_AUTH_METHOD,
            "model": DEFAULT_MODEL,
            "thinking_level": DEFAULT_THINKING_LEVEL,
        },
    }
    return config.get("llm", default_config)


def set_llm_config(
    role: str,  # "orchestrator" or "implementation"
    provider: str,
    auth_method: str,
    model: str = "default",
    thinking_level: str = "medium",
) -> None:
    """Set LLM configuration for a specific role.

    Args:
        role: "orchestrator" or "implementation"
        provider: LLM provider (anthropic, openai, google)
        auth_method: Auth method (oauth, api_key)
        model: Model to use (default recommended for oauth)
        thinking_level: Abstract thinking level (off, low, medium, high, maximum)
            Maps to provider-specific values via THINKING_LEVEL_MAP

    Raises:
        ValueError: If any parameter is invalid
    """
    if role not in ("orchestrator", "implementation"):
        raise ValueError(f"Invalid role: {role}. Must be 'orchestrator' or 'implementation'")

    if provider not in LLM_PROVIDERS:
        raise ValueError(f"Invalid provider: {provider}. Valid: {list(LLM_PROVIDERS.keys())}")

    if auth_method not in LLM_AUTH_METHODS:
        raise ValueError(f"Invalid auth method: {auth_method}. Valid: {list(LLM_AUTH_METHODS.keys())}")

    provider_info = LLM_PROVIDERS[provider]
    if model not in provider_info["models"]:
        raise ValueError(f"Invalid model '{model}' for {provider}. Valid: {provider_info['models']}")

    if thinking_level not in THINKING_LEVELS:
        raise ValueError(
            f"Invalid thinking level: {thinking_level}. "
            f"Valid: {', '.join(THINKING_LEVELS)}"
        )

    config = load_config()
    if "llm" not in config:
        config["llm"] = get_llm_config()

    config["llm"][role] = {
        "provider": provider,
        "auth_method": auth_method,
        "model": model,
        "thinking_level": thinking_level,
    }

    save_config(config)


def get_llm_display(role: str) -> str:
    """Get a human-readable display string for LLM config.

    Args:
        role: "orchestrator" or "implementation"

    Returns:
        Display string like "Anthropic (OAuth, default)"
    """
    llm_config = get_llm_config()
    role_config = llm_config.get(role, {})

    provider = role_config.get("provider", DEFAULT_PROVIDER)
    auth_method = role_config.get("auth_method", DEFAULT_AUTH_METHOD)
    model = role_config.get("model", DEFAULT_MODEL)

    provider_name = LLM_PROVIDERS.get(provider, {}).get("name", provider)
    auth_name = "OAuth" if auth_method == "oauth" else "API Key"

    return f"{provider_name} ({auth_name}, {model})"


def get_thinking_keyword(resolved_config: dict[str, str]) -> str | None:
    """Get the thinking keyword to prepend to prompts (Claude Code only).

    Claude Code V2 uses prompt keywords (not CLI args) to trigger extended thinking.
    Only "ultrathink" allocates thinking tokens; other levels were deprecated.

    Args:
        resolved_config: Resolved config dict from resolve_llm_config()

    Returns:
        "ultrathink" if provider is anthropic and thinking_level is maximum,
        None otherwise.

    Example:
        >>> get_thinking_keyword({"provider": "anthropic", "thinking_level": "maximum"})
        "ultrathink"
        >>> get_thinking_keyword({"provider": "anthropic", "thinking_level": "high"})
        None
        >>> get_thinking_keyword({"provider": "openai", "thinking_level": "maximum"})
        None  # OpenAI uses CLI args, not keywords
    """
    provider = resolved_config.get("provider", DEFAULT_PROVIDER)
    thinking_level = resolved_config.get("thinking_level", DEFAULT_THINKING_LEVEL)

    if provider == "anthropic" and thinking_level == "maximum":
        return "ultrathink"
    return None


def build_llm_args(resolved_config: dict[str, str]) -> list[str]:
    """Build CLI arguments from resolved LLM configuration.

    Generates provider-specific CLI arguments including the --model flag
    when model != "default" and thinking_level mapped to provider-specific
    parameters via THINKING_LEVEL_MAP.

    Note: For Claude Code, thinking is triggered via prompt keyword (see
    get_thinking_keyword()), not CLI args. For OpenAI Codex, thinking is
    controlled via --config model_reasoning_effort=<level>.

    Args:
        resolved_config: Resolved config dict from resolve_llm_config()
            Must have: provider, model keys
            Optional: thinking_level (maps to provider-specific values)

    Returns:
        List of CLI arguments (e.g., ["--dangerously-skip-permissions", "--model", "sonnet"])

    Example:
        # OpenAI with maximum thinking -> xhigh reasoning effort
        >>> build_llm_args({"provider": "openai", "model": "gpt-5.2", "thinking_level": "maximum"})
        ["exec", "--full-auto", "--model", "gpt-5.2", "--config", "model_reasoning_effort=xhigh"]

        # Anthropic - thinking handled via get_thinking_keyword(), not CLI args
        >>> build_llm_args({"provider": "anthropic", "model": "sonnet", "thinking_level": "maximum"})
        ["--dangerously-skip-permissions", "--model", "sonnet"]
    """
    provider = resolved_config.get("provider", DEFAULT_PROVIDER)
    model = resolved_config.get("model", DEFAULT_MODEL)
    thinking_level = resolved_config.get("thinking_level", DEFAULT_THINKING_LEVEL)

    # Map abstract thinking_level to provider-specific value
    provider_thinking_map = THINKING_LEVEL_MAP.get(provider, {})
    provider_thinking_value = provider_thinking_map.get(thinking_level)

    # Build args based on provider CLI
    if provider == "anthropic":
        # Claude Code CLI
        # ISSUE-LLM-002 FIX: Use --print mode for text generation (not code implementation)
        # and --output-format json to enforce JSON responses for derivation/examine phases
        args = ["--print"]  # Text generation mode (prevents code writing)
        args.extend(["--output-format", "json"])  # Force JSON output
        args.append("--dangerously-skip-permissions")
        if model and model != "default":
            args.extend(["--model", model])
        # Note: Claude thinking mode (ultrathink, etc.) would be passed via prompt
        # or environment, not CLI args - handled separately by orchestrator

        # FEAT-CLI-ISOLATION-001: Context isolation flags to prevent cross-session pollution
        # Fresh session ID ensures no cached context from prior invocations
        session_id = str(uuid.uuid4())
        args.extend(["--no-session-persistence"])  # Don't persist session state
        args.extend(["--session-id", session_id])  # Fresh session each invocation
        args.extend(["--setting-sources", "project"])  # Block user-level settings pollution
        logger.info(f"Claude CLI isolation: session_id={session_id[:8]}...")
        return args

    if provider == "google":
        # Gemini CLI - no reasoning effort control
        # See: docs/reference/llm-providers/gemini-cli-models.md
        args = ["--sandbox=permissive"]
        # "default" and "auto" both mean let Gemini choose (no --model flag)
        if model and model not in ("default", "auto"):
            args.extend(["--model", model])
        return args

    if provider == "openai":
        # OpenAI Codex CLI - uses exec --full-auto mode
        args = ["exec", "--full-auto"]
        if model and model != "default":
            args.extend(["--model", model])
        # Add reasoning effort (codex uses --config flag)
        if provider_thinking_value:
            args.extend(["--config", f"model_reasoning_effort={provider_thinking_value}"])
        return args

    # Fallback to Claude Code CLI args
    return ["--dangerously-skip-permissions"]


def get_llm_cli(provider: str = DEFAULT_PROVIDER) -> str:
    """Get the CLI executable path for a provider.

    Returns the full executable path for cross-platform subprocess compatibility.
    On Windows, this ensures extensions (.cmd/.exe) are included.
    On macOS/Linux, returns the resolved path for reliability.

    Args:
        provider: LLM provider name

    Returns:
        Full path to CLI executable, or bare command name as fallback
    """
    provider_info = LLM_PROVIDERS.get(provider, LLM_PROVIDERS[DEFAULT_PROVIDER])
    cli_name = provider_info.get("cli", "claude")
    # Full path for Windows compatibility (.cmd/.exe) and reliability everywhere
    return shutil.which(cli_name) or cli_name


def get_llm_command() -> tuple[str, list[str]]:
    """Get the implementation LLM command and arguments.

    Returns:
        Tuple of (command, args) for subprocess execution.
        Uses provider-specific CLI:
        - Anthropic: claude (Claude Code CLI)
        - Google: gemini (Gemini CLI)
        - OpenAI: codex (OpenAI Codex CLI)

    Note:
        Consider using resolve_llm_config() + build_llm_args() for more control.
    """
    llm_config = get_llm_config()
    impl_config = llm_config.get("implementation", {})

    provider = impl_config.get("provider", DEFAULT_PROVIDER)
    model = impl_config.get("model", DEFAULT_MODEL)

    cli = get_llm_cli(provider)
    args = build_llm_args({"provider": provider, "model": model})

    return cli, args


def get_config_path() -> Path:
    """Get path to client configuration file.

    Returns:
        Path to ~/.obra/client-config.yaml
    """
    return CONFIG_PATH


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.obra/client-config.yaml.

    Returns:
        Configuration dictionary, empty dict if file doesn't exist
    """
    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to ~/.obra/client-config.yaml.

    Args:
        config: Configuration dictionary to save

    Raises:
        OSError: If unable to write config file
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def get_default_project_override() -> str | None:
    """Get local default project override from client config."""
    config = load_config()
    projects = config.get("projects", {})
    if isinstance(projects, dict):
        value = projects.get("default_project")
        return str(value) if value is not None else None
    return None


def get_isolated_mode() -> bool | None:
    """Get agent isolation mode from config.

    Returns:
        True: Enable isolation
        False: Disable isolation
        None: Use default (auto-detect from CLI/ENV/CI)

    Config location: ~/.obra/client-config.yaml

    Example:
        # In client-config.yaml:
        agent:
          isolated_mode: true
    """
    config = load_config()
    agent_config = config.get("agent", {})
    if isinstance(agent_config, dict):
        return agent_config.get("isolated_mode")
    return None


def set_isolated_mode(enabled: bool | None) -> None:
    """Set agent isolation mode in config.

    Args:
        enabled: True to enable, False to disable, None to clear

    Config location: ~/.obra/client-config.yaml
    """
    config = load_config()

    if enabled is None:
        # Clear the setting
        if "agent" in config and isinstance(config["agent"], dict):
            config["agent"].pop("isolated_mode", None)
            if not config["agent"]:
                del config["agent"]
    else:
        if "agent" not in config:
            config["agent"] = {}
        config["agent"]["isolated_mode"] = enabled

    save_config(config)


def get_terms_acceptance() -> dict[str, Any] | None:
    """Get stored terms acceptance data.

    Returns:
        Dictionary with terms acceptance info, or None if not accepted:
        {
            "version": "2.1",
            "privacy_version": "1.3",
            "accepted_at": "2025-12-03T12:00:00+00:00"
        }
    """
    config = load_config()
    return config.get("terms_accepted")


def is_terms_accepted() -> bool:
    """Check if current terms version has been accepted.

    Returns:
        True if terms are accepted and version matches current,
        False otherwise
    """
    acceptance = get_terms_acceptance()

    if not acceptance:
        return False

    # Check if accepted version matches current version
    accepted_version = acceptance.get("version")
    if accepted_version != TERMS_VERSION:
        return False

    return True


def needs_reacceptance() -> bool:
    """Check if terms need to be re-accepted due to version change.

    Returns:
        True if terms were previously accepted but version changed,
        False if never accepted or current version is accepted
    """
    acceptance = get_terms_acceptance()

    if not acceptance:
        return False  # Never accepted, not "re-acceptance"

    accepted_version = acceptance.get("version")
    return accepted_version != TERMS_VERSION


def save_terms_acceptance(
    version: str = TERMS_VERSION,
    privacy_version: str = PRIVACY_VERSION,
) -> None:
    """Save terms acceptance to config file.

    Args:
        version: Terms version being accepted (default: current TERMS_VERSION)
        privacy_version: Privacy policy version (default: current PRIVACY_VERSION)
    """
    config = load_config()

    config["terms_accepted"] = {
        "version": version,
        "privacy_version": privacy_version,
        "accepted_at": datetime.now(UTC).isoformat(),
    }

    save_config(config)


def clear_terms_acceptance() -> None:
    """Clear stored terms acceptance (for testing/reset)."""
    config = load_config()

    if "terms_accepted" in config:
        del config["terms_accepted"]
        save_config(config)


# =============================================================================
# Firebase Auth Functions
# =============================================================================


def get_firebase_uid() -> str | None:
    """Get stored Firebase UID from config.

    Returns:
        Firebase UID string or None if not authenticated
    """
    config = load_config()
    return config.get("firebase_uid")


def get_user_email() -> str | None:
    """Get stored user email from config.

    Returns:
        User email string or None if not authenticated
    """
    config = load_config()
    return config.get("user_email")


def get_auth_token() -> str | None:
    """Get stored Firebase ID token from config.

    Returns:
        Firebase ID token or None if not authenticated
    """
    config = load_config()
    return config.get("auth_token")


def get_refresh_token() -> str | None:
    """Get stored Firebase refresh token from config.

    Returns:
        Firebase refresh token or None if not authenticated
    """
    config = load_config()
    return config.get("refresh_token")


def get_auth_provider() -> str | None:
    """Get stored auth provider from config.

    Returns:
        Auth provider (e.g., "google.com", "github.com") or None
    """
    config = load_config()
    return config.get("auth_provider")


def is_authenticated() -> bool:
    """Check if user is authenticated with Firebase Auth.

    Returns:
        True if Firebase UID and auth token are present
    """
    config = load_config()
    return bool(config.get("firebase_uid") and config.get("auth_token"))


def save_firebase_auth(
    firebase_uid: str,
    email: str,
    auth_token: str,
    refresh_token: str,
    auth_provider: str,
    display_name: str | None = None,
    token_expires_at: datetime | None = None,
) -> None:
    """Save Firebase authentication to config file.

    Args:
        firebase_uid: Firebase user ID
        email: User's email address
        auth_token: Firebase ID token
        refresh_token: Firebase refresh token
        auth_provider: Auth provider (e.g., "google.com")
        display_name: Optional user display name
        token_expires_at: Optional token expiration time. If not provided,
            defaults to 1 hour from now (Firebase ID token lifetime).
    """
    config = load_config()

    config["firebase_uid"] = firebase_uid
    config["user_email"] = email
    config["auth_token"] = auth_token
    config["refresh_token"] = refresh_token
    config["auth_provider"] = auth_provider
    config["auth_timestamp"] = datetime.now(UTC).isoformat()

    # Firebase ID tokens expire in 1 hour - save expiration for auto-refresh
    if token_expires_at is None:
        token_expires_at = datetime.now(UTC) + timedelta(hours=1)
    config["token_expires_at"] = token_expires_at.isoformat()

    if display_name:
        config["display_name"] = display_name

    # Also set user_id to email for compatibility with existing code
    config["user_id"] = email

    save_config(config)


def clear_firebase_auth() -> None:
    """Clear stored Firebase authentication from config file."""
    config = load_config()

    # Remove Firebase auth fields
    for key in [
        "firebase_uid",
        "user_email",
        "auth_token",
        "refresh_token",
        "auth_provider",
        "auth_timestamp",
        "display_name",
    ]:
        config.pop(key, None)

    save_config(config)


# Public exports
__all__ = [
    # Constants
    "TERMS_VERSION",
    "PRIVACY_VERSION",
    "CONFIG_PATH",
    "FIREBASE_API_KEY",
    "DEFAULT_API_BASE_URL",
    "DEFAULT_LLM_TIMEOUT",
    "DEFAULT_MAX_ITERATIONS",
    "LLM_PROVIDERS",
    "LLM_AUTH_METHODS",
    "DEFAULT_PROVIDER",
    "DEFAULT_AUTH_METHOD",
    "DEFAULT_MODEL",
    "DEFAULT_THINKING_LEVEL",
    "THINKING_LEVELS",
    "THINKING_LEVEL_MAP",
    "MODEL_SHORTCUTS",
    # Model inference constants
    "MODEL_PROVIDER_PATTERNS",
    "MODEL_PROVIDER_PREFIXES",
    "XHIGH_SUPPORTED_MODELS",
    # Provider health check
    "ProviderStatus",
    "PROVIDER_CLI_INFO",
    # API/Config functions
    "get_api_base_url",
    "get_llm_timeout",
    "get_max_iterations",
    "get_config_path",
    "load_config",
    "save_config",
    # Agent isolation config
    "get_isolated_mode",
    "set_isolated_mode",
    # LLM config functions
    "validate_model",
    "resolve_llm_config",
    "get_llm_config",
    "set_llm_config",
    "get_llm_display",
    "get_thinking_keyword",
    "build_llm_args",
    "get_llm_cli",
    "get_llm_command",
    # Model inference functions
    "infer_provider_from_model",
    # Provider health check functions
    "check_provider_status",
    "validate_provider_ready",
    # Thinking level functions
    "get_thinking_level_notes",
    "get_effective_thinking_value",
    # Terms functions
    "get_terms_acceptance",
    "is_terms_accepted",
    "needs_reacceptance",
    "save_terms_acceptance",
    "clear_terms_acceptance",
    # Firebase auth functions
    "get_firebase_uid",
    "get_user_email",
    "get_auth_token",
    "get_refresh_token",
    "get_auth_provider",
    "is_authenticated",
    "save_firebase_auth",
    "clear_firebase_auth",
]
