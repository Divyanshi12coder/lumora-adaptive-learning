from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import User
from app.rag import store
from app.services import documents

router = APIRouter(prefix="/documents", tags=["documents & RAG"])


@router.get("")
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [documents.document_dict(d) for d in documents.list_visible(db, user)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None, max_length=200),
    topic_id: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a .txt / .md / .pdf (max 5 MB). Call /ingest afterwards to index it."""
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, "That file is too big - please keep uploads under 5 MB.")
    doc = documents.create(db, user, file.filename or "document.txt", data, title, topic_id)
    return documents.document_dict(doc)


@router.get("/search")
def search(q: str, topic_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Semantic search over the learner's visible library (debug / transparency)."""
    if not q.strip() or len(q) > 300:
        raise HTTPException(422, "Query must be 1-300 characters.")
    return [r.__dict__ for r in store.search(db, q, user_id=user.id, topic_id=topic_id, k=5)]


@router.get("/{doc_id}")
def get_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return documents.document_dict(documents.get_visible(db, user, doc_id), include_text=True)


@router.post("/{doc_id}/ingest")
def ingest(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chunk -> embed -> store in the vector index."""
    return documents.document_dict(documents.ingest(db, user, doc_id))


@router.post("/{doc_id}/summary")
def summary(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return documents.summarize(db, user, doc_id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    documents.delete(db, user, doc_id)
