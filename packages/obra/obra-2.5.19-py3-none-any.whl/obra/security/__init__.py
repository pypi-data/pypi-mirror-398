"""Security components for Obra hybrid client.

This module provides prompt injection defense and context sanitization
for the hybrid client-server architecture.

Components:
    - PromptSanitizer: Sanitizes context data before prompt building
"""

from obra.security.prompt_sanitizer import (
    InjectionCheckResult,
    PromptSanitizer,
    sanitize_context,
)

__all__ = [
    "InjectionCheckResult",
    "PromptSanitizer",
    "sanitize_context",
]
