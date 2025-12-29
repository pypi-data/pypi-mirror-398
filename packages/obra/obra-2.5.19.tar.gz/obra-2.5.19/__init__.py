"""Obra - Cloud-native AI orchestration platform.

This is the main obra package that provides:
- Authentication with Firebase Auth
- Configuration management
- API client for Cloud Functions
- Hybrid orchestration with server intelligence
- Display utilities with Rich console
- Model registry for LLM provider configurations

Example:
    from obra.auth import login, get_current_auth
    from obra.config import load_config
    from obra.api import APIClient
    from obra.hybrid import HybridOrchestrator
    from obra import validate_model, MODEL_REGISTRY

    # Start a derivation session
    orchestrator = HybridOrchestrator.from_config()
    result = orchestrator.derive("Add user authentication")

    # Validate a model
    result = validate_model("anthropic", "sonnet")
"""

__version__ = "2.5.19"
__author__ = "Unpossible Creations, Inc."

# Model registry exports (migrated from obra_client)
from obra.model_registry import (
    MODEL_REGISTRY,
    REGISTRY_VERSION,
    ModelInfo,
    ModelStatus,
    ProviderConfig,
    ValidationResult,
    calculate_max_prompt_tokens,
    get_cli_args,
    get_default_model,
    get_default_output_budget,
    get_max_prompt_tokens_for_model,
    get_model_context_window,
    get_provider,
    get_provider_models,
    get_provider_names,
    resolve_alias,
    validate_model,
)

__all__ = [
    "MODEL_REGISTRY",
    "REGISTRY_VERSION",
    "ModelInfo",
    "ModelStatus",
    "ProviderConfig",
    "ValidationResult",
    "__author__",
    "__version__",
    "calculate_max_prompt_tokens",
    "get_cli_args",
    "get_default_model",
    "get_default_output_budget",
    "get_max_prompt_tokens_for_model",
    "get_model_context_window",
    "get_provider",
    "get_provider_models",
    "get_provider_names",
    "resolve_alias",
    "validate_model",
]
