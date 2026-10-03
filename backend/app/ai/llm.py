"""LLM abstraction layer: provider selection, validation, safety and fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseModel

from app.ai.providers.base import LLMProvider, LLMRequest, ProviderError, ProviderRefusal
from app.ai.providers.demo import DemoProvider
from app.core.config import get_settings

log = logging.getLogger("lumora.ai")


@lru_cache
def get_provider() -> LLMProvider:
    s = get_settings()
    if s.ai_provider == "demo":
        return DemoProvider()
    if not s.ai_api_key:
        log.warning("AI_PROVIDER=%s but AI_API_KEY is empty - using demo provider.", s.ai_provider)
        return DemoProvider()
    if s.ai_provider == "openai":
        from app.ai.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(s.ai_api_key, s.resolved_ai_model, s.ai_timeout_seconds)
    from app.ai.providers.anthropic_provider import AnthropicProvider

    return AnthropicProvider(s.ai_api_key, s.resolved_ai_model, s.ai_timeout_seconds)


@dataclass
class LLMResult:
    output: BaseModel
    provider: str
    model: str
    is_demo: bool
    fallback_reason: str | None = None


_demo = DemoProvider()


def run(request: LLMRequest) -> LLMResult:
    """Call the configured provider; on any failure fall back to the demo provider
    so a child never sees a crash. Fallbacks are recorded for observability."""
    provider = get_provider()
    try:
        out = provider.generate(request)
        return LLMResult(out, provider.name, provider.model, provider.is_demo)
    except ProviderRefusal:
        log.info("Provider refused request; using grounded demo answer.")
        reason = "refusal"
    except ProviderError as exc:
        log.warning("Provider error (%s); using demo fallback.", exc)
        reason = "provider_error"
    out = _demo.generate(request)
    return LLMResult(out, _demo.name, _demo.model, True, fallback_reason=reason)
