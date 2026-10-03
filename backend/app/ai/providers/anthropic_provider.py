from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.ai.providers.base import LLMProvider, LLMRequest, ProviderError, ProviderRefusal


class AnthropicProvider(LLMProvider):  # pragma: no cover - requires network + API key
    """Claude via the official SDK, using structured outputs (output_config.format)."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model

    def generate(self, request: LLMRequest) -> BaseModel:
        import anthropic

        try:
            resp = self.client.beta.messages.create(
                model=self.model,
                max_tokens=max(request.max_tokens, 2048),
                system=request.system,
                messages=request.messages,
                output_config={
                    # Short tutoring turns: low effort keeps latency child-friendly.
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": self.strict_schema(request.schema)},
                },
                # Server-side fallback if a safety classifier declines the request.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as exc:
            raise ProviderError("Anthropic rate limit") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"Anthropic API error {exc.status_code}") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError("Could not reach Anthropic") from exc

        if resp.stop_reason == "refusal":
            raise ProviderRefusal("Model declined the request")
        if resp.stop_reason == "max_tokens":
            raise ProviderError("Response was cut off (max_tokens)")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            return request.schema.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProviderError("Claude returned output that failed schema validation") from exc
