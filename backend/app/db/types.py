"""Portable column types.

`EmbeddingVector` is a pgvector `vector(n)` column on PostgreSQL and a JSON array
everywhere else. This keeps one ORM model for production (pgvector + HNSW index)
and for the SQLite-backed unit tests.
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class EmbeddingVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        values = [float(x) for x in value]
        if dialect.name == "postgresql":
            return values  # pgvector's bind processor handles list -> vector
        return values

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return None
        return [float(x) for x in value]
