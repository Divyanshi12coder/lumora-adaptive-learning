"""Vector search over document chunks.

PostgreSQL: pgvector cosine distance (`<=>`) with an HNSW index does the
candidate retrieval inside the database. Other dialects (SQLite in tests) fall
back to an exact numpy cosine scan - same results, no index.

Candidates are then re-ranked with a small lexical-overlap bonus and a bonus for
the topic the learner is currently studying (hybrid retrieval).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, bindparam, or_, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.rag.embeddings import get_embedder, tokenize

MIN_SCORE = 0.10


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    document_title: str
    section: str | None
    text: str
    score: float
    topic_id: int | None
    source: str


def _visible_docs_filter(user_id: int | None):
    cond = Document.owner_id.is_(None)
    if user_id is not None:
        cond = or_(cond, Document.owner_id == user_id)
    return cond


def search(
    db: Session,
    query: str,
    *,
    user_id: int | None,
    topic_id: int | None = None,
    k: int = 4,
    candidates: int = 24,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []
    qvec = get_embedder().embed_one(query)
    base = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == "ingested", _visible_docs_filter(user_id), DocumentChunk.embedding.is_not(None))
    )

    if db.get_bind().dialect.name == "postgresql":
        q_param = bindparam("qvec", qvec, type_=Vector(len(qvec)))
        distance = DocumentChunk.embedding.op("<=>", return_type=Float)(q_param)  # pgvector cosine distance
        rows = db.execute(base.add_columns(distance.label("dist")).order_by(distance).limit(candidates)).all()
        scored = [(chunk, doc, 1.0 - float(dist)) for chunk, doc, dist in rows]
    else:
        rows = db.execute(base).all()
        if not rows:
            return []
        mat = np.asarray([c.embedding for c, _ in rows], dtype=np.float64)
        q = np.asarray(qvec, dtype=np.float64)
        norms = np.linalg.norm(mat, axis=1) * (np.linalg.norm(q) or 1.0)
        sims = (mat @ q) / np.where(norms == 0, 1, norms)
        order = np.argsort(-sims)[:candidates]
        scored = [(rows[i][0], rows[i][1], float(sims[i])) for i in order]

    q_terms = set(tokenize(query))
    results: list[RetrievedChunk] = []
    for chunk, doc, sim in scored:
        overlap = len(q_terms & set(tokenize(chunk.content))) / max(1, len(q_terms))
        score = 0.8 * sim + 0.2 * overlap
        if topic_id is not None and doc.topic_id == topic_id:
            score += 0.08
        results.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=doc.id,
                document_title=doc.title,
                section=(chunk.meta or {}).get("section"),
                text=chunk.content,
                score=round(score, 4),
                topic_id=doc.topic_id,
                source=doc.source,
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return [r for r in results if r.score >= MIN_SCORE][:k]
