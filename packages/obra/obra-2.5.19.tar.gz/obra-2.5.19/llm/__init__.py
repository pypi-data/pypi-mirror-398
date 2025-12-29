"""Unified LLM invocation layer for Obra client.

This package provides:
- LLMInvoker: Unified interface for LLM invocation across providers
- ThinkingModeAdapter: Provider-agnostic extended thinking support
- OutputParser: Structured output parsing with schema validation
- Provider implementations: Anthropic, OpenAI, Google, Ollama

The LLM layer abstracts provider differences and provides consistent
interfaces for derivation, revision, and examination operations.

Example:
    from obra.llm import LLMInvoker, ThinkingLevel

    invoker = LLMInvoker()
    result = invoker.invoke(
        prompt="Analyze this code",
        provider="anthropic",
        thinking_level=ThinkingLevel.HIGH,
    )
    print(result.content)

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md
    - obra/execution/ (derivation/revision engines)
    - obra/hybrid/orchestrator.py
"""

from obra.llm.invoker import InvocationResult, LLMInvoker
from obra.llm.output_parser import OutputParser, ParsedOutput
from obra.llm.thinking_mode import (
    THINKING_LEVEL_TOKENS,
    ThinkingConfig,
    ThinkingLevel,
    ThinkingMode,
    ThinkingModeAdapter,
)

__all__ = [
    # Core invoker
    "LLMInvoker",
    "InvocationResult",
    # Thinking mode
    "ThinkingModeAdapter",
    "ThinkingMode",
    "ThinkingLevel",
    "ThinkingConfig",
    "THINKING_LEVEL_TOKENS",
    # Output parser
    "OutputParser",
    "ParsedOutput",
]
