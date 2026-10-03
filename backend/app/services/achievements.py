"""Encouraging achievements computed from real activity.

Designed to celebrate effort and variety - no leaderboards, no loss aversion,
no penalties for taking a break.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AIConversation,
    AIMessage,
    Answer,
    Course,
    InteractionEvent,
    MasteryScore,
    QuizAttempt,
    Subject,
    Topic,
    User,
)


def _quizzes_in_subject(db: Session, user_id: int, slug: str) -> int:
    return db.scalar(
        select(func.count(QuizAttempt.id))
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .join(Course, Course.id == Topic.course_id)
        .join(Subject, Subject.id == Course.subject_id)
        .where(QuizAttempt.user_id == user_id, QuizAttempt.status == "completed", Subject.slug == slug)
    ) or 0


def compute(db: Session, user: User) -> list[dict]:
    uid = user.id
    correct = db.scalar(select(func.count(Answer.id)).where(Answer.user_id == uid, Answer.is_correct.is_(True))) or 0
    questions_asked = db.scalar(
        select(func.count(AIMessage.id)).join(AIConversation, AIConversation.id == AIMessage.conversation_id)
        .where(AIConversation.user_id == uid, AIMessage.role == "user")
    ) or 0
    quizzes = db.scalar(
        select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == uid, QuizAttempt.status == "completed")
    ) or 0
    days = db.execute(select(InteractionEvent.created_at).where(InteractionEvent.user_id == uid)).scalars().all()
    learning_days = len({d.date() for d in days})
    best_reading = db.scalar(
        select(func.max(MasteryScore.p_mastery))
        .join(Topic, Topic.id == MasteryScore.topic_id)
        .join(Course, Course.id == Topic.course_id)
        .join(Subject, Subject.id == Course.subject_id)
        .where(MasteryScore.user_id == uid, Subject.slug == "reading")
    ) or 0.0
    lessons_done = db.scalar(
        select(func.count(InteractionEvent.id))
        .where(InteractionEvent.user_id == uid, InteractionEvent.event_type == "lesson_completed")
    ) or 0

    defs = [
        ("first_steps", "First Steps", "Finish your very first lesson.", "footprints", lessons_done, 1),
        ("curious_learner", "Curious Learner", "Ask Divi 5 questions.", "message-circle-question", questions_asked, 5),
        ("problem_solver", "Problem Solver", "Get 20 answers right.", "puzzle", correct, 20),
        ("math_explorer", "Math Explorer", "Complete 3 maths quizzes.", "calculator", _quizzes_in_subject(db, uid, "mathematics"), 3),
        ("science_star", "Science Star", "Complete 3 science quizzes.", "flask", _quizzes_in_subject(db, uid, "science"), 3),
        ("reading_champion", "Reading Champion", "Reach 80% mastery in a reading topic.", "book-open", round(best_reading * 100), 80),
        ("time_traveller", "Time Traveller", "Complete a history quiz.", "landmark", _quizzes_in_subject(db, uid, "history"), 1),
        ("steady_learner", "Steady Learner", "Learn on 5 different days (any days!).", "calendar-heart", learning_days, 5),
        ("quiz_adventurer", "Quiz Adventurer", "Finish 5 quizzes.", "trophy", quizzes, 5),
    ]
    return [
        {"key": k, "title": t, "description": d, "icon": i, "progress": min(cur, target), "target": target,
         "earned": cur >= target}
        for k, t, d, i, cur, target in defs
    ]
