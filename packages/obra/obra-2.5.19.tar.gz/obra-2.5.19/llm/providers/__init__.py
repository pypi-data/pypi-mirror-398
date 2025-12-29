"""LLM provider implementations.

This package provides provider-specific implementations:
- AnthropicProvider: Claude models via Anthropic API
- OpenAIProvider: GPT and O1 models via OpenAI API
- GoogleProvider: Gemini models via Google AI API
- OllamaProvider: Local models via Ollama

Each provider implements the LLMProvider protocol and handles
provider-specific API calls, authentication, and response parsing.

Example:
    from obra.llm.providers import AnthropicProvider

    provider = AnthropicProvider()
    provider.initialize(api_key="sk-...")
    response = provider.generate(
        prompt="Analyze this code",
        model="claude-3-sonnet-20240229",
    )

Related:
    - obra/llm/invoker.py
    - obra/llm/thinking_mode.py
"""

from obra.llm.providers.anthropic import AnthropicProvider
from obra.llm.providers.base import LLMProvider, ProviderResponse
from obra.llm.providers.google import GoogleProvider
from obra.llm.providers.ollama import OllamaProvider
from obra.llm.providers.openai import OpenAIProvider

__all__ = [
    # Base
    "LLMProvider",
    "ProviderResponse",
    # Providers
    "AnthropicProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "OllamaProvider",
]
