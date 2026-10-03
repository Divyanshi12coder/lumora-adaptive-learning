"""Content, lessons, sessions, interactions and quizzes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import InteractionBatch, InteractionIn, LessonComplete, QuizGenerateRequest, QuizSubmitRequest
from app.services import content, interactions, quiz

router = APIRouter()


# --- content ---------------------------------------------------------------------
@router.get("/subjects", tags=["content"])
def subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Subjects with topics and the learner's progress in each."""
    return content.list_subjects(db, user)


@router.get("/courses", tags=["content"])
def courses(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content.list_courses(db)


@router.get("/topics", tags=["content"])
def topics(subject: str | None = Query(default=None, max_length=60), user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    return content.list_topics(db, user, subject)


@router.get("/lessons/{lesson_id}", tags=["content"])
def get_lesson(lesson_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lesson with sections chosen/expanded by the adaptive engine for this learner."""
    return content.lesson_view(db, user, lesson_id)


@router.post("/lessons/{lesson_id}/start", tags=["content"])
def start_lesson(lesson_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content.lesson_view(db, user, lesson_id, start=True)


@router.post("/lessons/{lesson_id}/complete", tags=["content"])
def complete_lesson(lesson_id: int, body: LessonComplete, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return content.complete_lesson(db, user, lesson_id, body.seconds, body.progress)


# --- sessions & interaction tracking ------------------------------------------
@router.post("/sessions/start", tags=["interactions"], status_code=status.HTTP_201_CREATED)
def session_start(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = interactions.active_session(db, user, create=True)
    return {"session_id": s.id, "started_at": s.started_at.isoformat()}


@router.post("/sessions/{session_id}/end", tags=["interactions"])
def session_end(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = interactions.end_session(db, user, session_id)
    return {"session_id": s.id, "ended_at": s.ended_at.isoformat() if s.ended_at else None}


@router.post("/interactions", tags=["interactions"], status_code=status.HTTP_201_CREATED)
def track(body: InteractionBatch | InteractionIn, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    """Record one event or a batch (the frontend batches and flushes periodically)."""
    events = body.events if isinstance(body, InteractionBatch) else [body]
    ids = []
    for e in events:
        ev = interactions.record_event(db, user, e.event_type, session_id=e.session_id, topic_id=e.topic_id,
                                       lesson_id=e.lesson_id, question_id=e.question_id, payload=e.payload,
                                       commit=False)
        ids.append(ev)
    db.commit()
    return {"recorded": len(ids), "ids": [e.id for e in ids]}


# --- quizzes -------------------------------------------------------------------------
@router.post("/quiz/generate", tags=["quiz"], status_code=status.HTTP_201_CREATED)
def generate(body: QuizGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Build a personalised quiz: difficulty, length, answer-choice count and review
    questions are chosen by the adaptive engine."""
    data = quiz.generate_quiz(db, user, body.topic_id)
    for q in data["questions"]:
        q.pop("option_map", None)  # server-side only
    return data


@router.get("/quiz/{attempt_id}/hint/{question_id}", tags=["quiz"])
def hint(attempt_id: int, question_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return quiz.get_hint(db, user, attempt_id, question_id)


@router.post("/quiz/{attempt_id}/submit", tags=["quiz"])
def submit(attempt_id: int, body: QuizSubmitRequest, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    return quiz.submit_quiz(db, user, attempt_id, [a.model_dump() for a in body.answers], session_id=body.session_id)
