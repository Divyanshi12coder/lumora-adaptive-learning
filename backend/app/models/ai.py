from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow


class AIConversation(TimestampMixin, Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.id"
    )


class AIMessage(TimestampMixin, Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # structured tutor reply (steps, examples, ...)
    strategy: Mapped[dict | None] = mapped_column(JSON)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    provider: Mapped[str | None] = mapped_column(String(30))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_flags: Mapped[list] = mapped_column(JSON, default=list)
    feedback: Mapped[str | None] = mapped_column(String(20))

    conversation: Mapped[AIConversation] = relationship(back_populates="messages")


class AdaptiveStrategyRecord(TimestampMixin, Base):
    """Audit log of every teaching strategy the engine produced (explainability)."""

    __tablename__ = "adaptive_strategies"
    __table_args__ = (Index("ix_adaptive_strategies_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    context: Mapped[str] = mapped_column(String(20))  # quiz | tutor | lesson
    support_score: Mapped[float] = mapped_column(Float)
    strategy: Mapped[dict] = mapped_column(JSON)
    signals: Mapped[dict] = mapped_column(JSON)


class ModelPrediction(TimestampMixin, Base):
    __tablename__ = "model_predictions"
    __table_args__ = (Index("ix_model_predictions_user_model", "user_id", "model_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    model_name: Mapped[str] = mapped_column(String(60))
    model_version: Mapped[str] = mapped_column(String(60))
    features: Mapped[dict] = mapped_column(JSON)
    prediction: Mapped[float] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(20), default="model")  # model | fallback
    detail: Mapped[str | None] = mapped_column(Text)
