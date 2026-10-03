"""Learning-material uploads for the RAG library."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai import llm, prompts
from app.ai.providers.base import LLMRequest
from app.ai.safety import screen_output
from app.ai.schemas import DocumentSummary
from app.core.config import get_settings
from app.models import Document, Topic, User
from app.rag.extract import ExtractionError, extract_text, sanitize_filename
from app.rag.pipeline import ingest_document

MAX_DOCS_PER_USER = 25


def document_dict(d: Document, include_text: bool = False) -> dict:
    out = {
        "id": d.id, "title": d.title, "filename": d.filename, "content_type": d.content_type, "source": d.source,
        "status": d.status, "char_count": d.char_count, "chunk_count": d.chunk_count, "error": d.error,
        "topic_id": d.topic_id, "owned": d.owner_id is not None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None,
    }
    if include_text:
        out["preview"] = d.raw_text[:1500]
        out["chunks"] = [{"index": c.chunk_index, "section": (c.meta or {}).get("section"), "words": c.word_count,
                          "text": c.content[:400]} for c in d.chunks[:30]]
    return out


def create(db: Session, user: User, filename: str, data: bytes, title: str | None, topic_id: int | None) -> Document:
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(413, "That file is too big - please keep uploads under 5 MB.")
    owned = db.scalars(select(Document.id).where(Document.owner_id == user.id)).all()
    if len(owned) >= MAX_DOCS_PER_USER:
        raise HTTPException(409, f"You can keep up to {MAX_DOCS_PER_USER} documents. Delete one to add more.")
    if topic_id is not None and not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found.")
    try:
        extracted = extract_text(filename, data)
    except ExtractionError as exc:
        raise HTTPException(422, str(exc)) from exc
    safe_name = sanitize_filename(filename)
    doc = Document(owner_id=user.id, topic_id=topic_id, title=(title or safe_name.rsplit(".", 1)[0])[:200],
                   filename=safe_name, content_type=extracted.content_type, source="upload", status="uploaded",
                   raw_text=extracted.text, char_count=len(extracted.text))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_visible(db: Session, user: User, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if not doc or (doc.owner_id is not None and doc.owner_id != user.id):
        raise HTTPException(404, "Document not found.")
    return doc


def get_owned(db: Session, user: User, doc_id: int) -> Document:
    doc = get_visible(db, user, doc_id)
    if doc.owner_id != user.id:
        raise HTTPException(403, "Built-in library documents can't be changed.")
    return doc


def list_visible(db: Session, user: User) -> list[Document]:
    return list(db.scalars(
        select(Document).where(or_(Document.owner_id.is_(None), Document.owner_id == user.id))
        .order_by(Document.owner_id.is_(None), Document.created_at.desc())
    ).all())


def ingest(db: Session, user: User, doc_id: int) -> Document:
    return ingest_document(db, get_owned(db, user, doc_id))


def delete(db: Session, user: User, doc_id: int) -> None:
    db.delete(get_owned(db, user, doc_id))
    db.commit()


def summarize(db: Session, user: User, doc_id: int) -> dict:
    doc = get_visible(db, user, doc_id)
    result = llm.run(LLMRequest(task="summary", system=prompts.SYSTEM_PROMPT,
                                messages=prompts.build_summary_messages(doc.raw_text), schema=DocumentSummary,
                                context={"text": doc.raw_text}, max_tokens=700))
    out: DocumentSummary = result.output  # type: ignore[assignment]
    return {"document_id": doc.id, "summary": screen_output(out.summary).text,
            "key_points": [screen_output(k).text for k in out.key_points[:5]], "is_demo": result.is_demo}
