from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.ai.providers.base import LLMProvider, LLMRequest, ProviderError, ProviderRefusal


class OpenAIProvider(LLMProvider):  # pragma: no cover - requires network + API key
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model

    def generate(self, request: LLMRequest) -> BaseModel:
        import openai

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=request.max_tokens,
                temperature=0.4,
                messages=[{"role": "system", "content": request.system}, *request.messages],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.schema.__name__,
                        "strict": True,
                        "schema": self.strict_schema(request.schema),
                    },
                },
            )
        except openai.APIError as exc:
            raise ProviderError(f"OpenAI error: {exc.__class__.__name__}") from exc

        choice = resp.choices[0]
        if getattr(choice.message, "refusal", None):
            raise ProviderRefusal("Model refused the request")
        try:
            return request.schema.model_validate(json.loads(choice.message.content or "{}"))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProviderError("OpenAI returned output that failed schema validation") from exc
