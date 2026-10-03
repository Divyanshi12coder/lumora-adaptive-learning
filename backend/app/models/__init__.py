"""Import every model so Base.metadata is complete (used by Alembic and tests)."""

from app.models.ai import AdaptiveStrategyRecord, AIConversation, AIMessage, ModelPrediction
from app.models.content import Course, Lesson, Question, Subject, Topic
from app.models.document import Document, DocumentChunk
from app.models.learning import (
    Answer,
    InteractionEvent,
    LearningGoal,
    LearningSession,
    MasteryHistory,
    MasteryScore,
    QuizAttempt,
    Recommendation,
)
from app.models.user import LearningPreferences, StudentProfile, User

__all__ = [
    "AIConversation",
    "AIMessage",
    "AdaptiveStrategyRecord",
    "Answer",
    "Course",
    "Document",
    "DocumentChunk",
    "InteractionEvent",
    "LearningGoal",
    "LearningPreferences",
    "LearningSession",
    "Lesson",
    "MasteryHistory",
    "MasteryScore",
    "ModelPrediction",
    "Question",
    "QuizAttempt",
    "Recommendation",
    "StudentProfile",
    "Subject",
    "Topic",
    "User",
]
