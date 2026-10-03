"""Embedding providers behind one interface.

* `local`  - deterministic, offline feature-hashing embeddings (word unigrams,
             bigrams and character trigrams, signed hashing, sublinear TF,
             L2-normalised). No downloads or API keys, so the whole RAG pipeline
             runs in demo mode and in CI. It captures lexical rather than deep
             semantic similarity - documented as a limitation.
* `openai` - text-embedding-3-small with `dimensions=EMBEDDING_DIM`, so the
             pgvector column size stays the same whichever provider is used.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from functools import lru_cache

import numpy as np

from app.core.config import get_settings

STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its", "of", "on", "or", "our", "she", "so", "that", "the", "their", "them", "then", "there", "these", "they", "this", "to", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "you", "your", "can", "do", "does", "did", "not", "no", "yes", "about", "into", "than", "too", "very", "just", "also", "how"]
)
TOKEN = re.compile(r"[a-z0-9]+")


def _stem(tok: str) -> str:
    for suf in ("ing", "edly", "ed", "es", "s", "ly"):
        if len(tok) > len(suf) + 2 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


class EmbeddingProvider(ABC):
    name: str
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class HashingEmbeddings(EmbeddingProvider):
    name = "local-hashing-v1"

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def _bucket(self, feature: str) -> tuple[int, float]:
        h = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        n = int.from_bytes(h, "little")
        return n % self.dim, (1.0 if (n >> 63) & 1 else -1.0)

    def _vector(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float64)
        toks = tokenize(text)
        counts: dict[str, float] = {}
        for t in toks:
            counts["w:" + t] = counts.get("w:" + t, 0) + 1.0
        for a, b in zip(toks, toks[1:], strict=False):
            counts[f"b:{a}_{b}"] = counts.get(f"b:{a}_{b}", 0) + 0.6
        for t in toks:
            padded = f"#{t}#"
            for i in range(len(padded) - 2):
                key = "c:" + padded[i : i + 3]
                counts[key] = counts.get(key, 0) + 0.25
        for feat, c in counts.items():
            idx, sign = self._bucket(feat)
            vec[idx] += sign * (1 + math.log(c)) if c >= 1 else sign * c
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class OpenAIEmbeddings(EmbeddingProvider):  # pragma: no cover - needs network + key
    name = "openai"

    def __init__(self, dim: int, model: str, api_key: str) -> None:
        from openai import OpenAI

        self.dim = dim
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=30)

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            resp = self.client.embeddings.create(model=self.model, input=texts[i : i + 64], dimensions=self.dim)
            out.extend(d.embedding for d in resp.data)
        return out


@lru_cache
def get_embedder() -> EmbeddingProvider:
    s = get_settings()
    if s.embedding_provider == "openai":
        key = s.embedding_api_key or (s.ai_api_key if s.ai_provider == "openai" else None)
        if not key:
            raise RuntimeError("EMBEDDING_PROVIDER=openai requires EMBEDDING_API_KEY (or AI_API_KEY with AI_PROVIDER=openai)")
        return OpenAIEmbeddings(s.embedding_dim, s.embedding_model, key)
    return HashingEmbeddings(s.embedding_dim)
