from __future__ import annotations

import os
from typing import Any

from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider


PROVIDER_API_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
FALLBACK_ORDER = ("gemini", "openai", "anthropic", "openrouter")


def configured_provider_names() -> list[str]:
    return [name for name in FALLBACK_ORDER if os.getenv(PROVIDER_API_KEYS[name])]


def resolve_provider_name(requested_name: str) -> str:
    if requested_name not in PROVIDER_API_KEYS:
        raise ValueError(f"Unknown provider: {requested_name}")
    if os.getenv(PROVIDER_API_KEYS[requested_name]):
        return requested_name
    configured = configured_provider_names()
    if configured:
        return configured[0]
    expected = ", ".join(PROVIDER_API_KEYS.values())
    raise RuntimeError(
        f"Missing {PROVIDER_API_KEYS[requested_name]} and no fallback provider is configured. "
        f"Set one of: {expected}"
    )


def make_provider(name: str) -> Any:
    resolved_name = resolve_provider_name(name)
    factories = {
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
    }
    provider = factories[resolved_name]()
    provider.requested_name = name
    provider.provider_name = resolved_name
    provider.used_fallback = resolved_name != name
    return provider
