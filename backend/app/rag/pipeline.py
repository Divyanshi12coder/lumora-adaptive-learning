"""Ingestion pipeline: document -> chunks -> embeddings -> vector store."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk
from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embedder


def ingest_document(db: Session, doc: Document) -> Document:
    """Idempotent: re-ingesting replaces previous chunks."""
    settings = get_settings()
    try:
        chunks = chunk_text(doc.raw_text, settings.chunk_size_words, settings.chunk_overlap_words)
        if not chunks:
            raise ValueError("No text to index.")
        embedder = get_embedder()
        # Contextual embeddings: prefix each chunk with document title + section so short
        # chunks ("Words to know") still carry what they are about.
        vectors = embedder.embed([" - ".join(filter(None, [doc.title, c.meta.get("section")])) + ": " + c.text
                                  for c in chunks])
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        for c, vec in zip(chunks, vectors, strict=True):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.index,
                    content=c.text,
                    word_count=c.word_count,
                    embedding=vec,
                    meta={**c.meta, "embedder": embedder.name},
                )
            )
        doc.status = "ingested"
        doc.chunk_count = len(chunks)
        doc.error = None
        doc.ingested_at = datetime.now(UTC)
    except Exception as exc:
        doc.status = "failed"
        doc.error = str(exc)[:500]
    db.commit()
    db.refresh(doc)
    return doc
