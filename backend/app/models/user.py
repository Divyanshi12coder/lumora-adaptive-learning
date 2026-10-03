from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(20), default="learner")
    # Incremented on logout -> invalidates every previously issued JWT.
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences: Mapped["LearningPreferences"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(TimestampMixin, Base):
    """Deliberately minimal: no birth date, school, location or health data."""

    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    avatar: Mapped[str] = mapped_column(String(30), default="star")
    grade_band: Mapped[str | None] = mapped_column(String(20))  # "early" | "middle" | "upper"
    favorite_subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    learner_cluster: Mapped[str | None] = mapped_column(String(40))
    weekly_goal_days: Mapped[int] = mapped_column(Integer, default=3)

    user: Mapped[User] = relationship(back_populates="profile")


class LearningPreferences(Base):
    __tablename__ = "learning_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    explanation_length: Mapped[str] = mapped_column(String(10), default="medium")  # short|medium|detailed
    prefers_visuals: Mapped[bool] = mapped_column(Boolean, default=True)
    prefers_examples: Mapped[bool] = mapped_column(Boolean, default=True)
    pace: Mapped[str] = mapped_column(String(10), default="steady")  # relaxed|steady|quick
    read_aloud: Mapped[bool] = mapped_column(Boolean, default=False)
    readable_font: Mapped[bool] = mapped_column(Boolean, default=False)
    text_scale: Mapped[float] = mapped_column(Float, default=1.0)
    line_spacing: Mapped[float] = mapped_column(Float, default=1.6)
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False)
    focus_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    high_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    # Learned from tutor feedback ("too long", "too hard"): small biases in [-1, 1].
    length_bias: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_bias: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="preferences")
