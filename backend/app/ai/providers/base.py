from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ProviderError(RuntimeError):
    """Raised when a provider call fails or returns invalid output."""


class ProviderRefusal(ProviderError):
    """The upstream model declined the request (e.g. safety classifier)."""


@dataclass
class LLMRequest:
    """One provider-agnostic request.

    `system` + `messages` are what real LLMs see. `task` and `context` carry the
    same information in structured form so the offline demo provider can build a
    grounded answer without an LLM - keeping a single service interface.
    """

    task: str  # tutor | quiz | summary | study_plan
    system: str
    messages: list[dict]
    schema: type[BaseModel]
    context: dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1200


class LLMProvider(ABC):
    name: str
    model: str
    is_demo: bool = False

    @abstractmethod
    def generate(self, request: LLMRequest) -> BaseModel: ...

    @staticmethod
    def strict_schema(schema: type[BaseModel]) -> dict:
        """JSON schema with every property required (needed for strict modes)."""
        js = schema.model_json_schema()

        def fix(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    node["required"] = list(node["properties"].keys())
                    node["additionalProperties"] = False
                node.pop("title", None)
                node.pop("default", None)
                for v in node.values():
                    fix(v)
            elif isinstance(node, list):
                for v in node:
                    fix(v)

        fix(js)
        return js
