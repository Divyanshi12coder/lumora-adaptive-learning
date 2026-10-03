from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import ChatRequest, FeedbackRequest
from app.services import tutor

router = APIRouter(prefix="/tutor", tags=["ai tutor"])


@router.post("/chat")
def chat(body: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ask Divi. The reply is adapted to the learner's strategy and grounded with RAG sources."""
    return tutor.chat(db, user, body.message, topic_id=body.topic_id, conversation_id=body.conversation_id,
                      intent=body.intent)


@router.get("/history")
def history(conversation_id: int | None = Query(default=None), user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    """List conversations, or the messages of one conversation."""
    if conversation_id is not None:
        return tutor.conversation_messages(db, user, conversation_id)
    return tutor.list_conversations(db, user)


@router.post("/messages/{message_id}/feedback")
def feedback(message_id: int, body: FeedbackRequest, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """Feedback adjusts the learner's preference biases used by the adaptive engine."""
    return tutor.give_feedback(db, user, message_id, body.value)
