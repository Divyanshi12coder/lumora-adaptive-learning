"""Request/response schemas for the REST API (validated by Pydantic)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# --- auth / profile -----------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=40)

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if v.isalpha() or v.isdigit():
            raise ValueError("Use a mix of letters and numbers (or symbols) in your password.")
        return v

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Please choose a display name.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    explanation_length: Literal["short", "medium", "detailed"]
    prefers_visuals: bool
    prefers_examples: bool
    pace: Literal["relaxed", "steady", "quick"]
    read_aloud: bool
    readable_font: bool
    text_scale: float
    line_spacing: float
    reduced_motion: bool
    focus_mode: bool
    high_contrast: bool


class PreferencesUpdate(BaseModel):
    explanation_length: Literal["short", "medium", "detailed"] | None = None
    prefers_visuals: bool | None = None
    prefers_examples: bool | None = None
    pace: Literal["relaxed", "steady", "quick"] | None = None
    read_aloud: bool | None = None
    readable_font: bool | None = None
    text_scale: float | None = Field(default=None, ge=0.85, le=1.6)
    line_spacing: float | None = Field(default=None, ge=1.3, le=2.2)
    reduced_motion: bool | None = None
    focus_mode: bool | None = None
    high_contrast: bool | None = None


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    avatar: str
    grade_band: str | None
    favorite_subject_id: int | None
    weekly_goal_days: int
    preferences: PreferencesOut


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    avatar: Literal["star", "owl", "rocket", "leaf", "book", "sun"] | None = None
    grade_band: Literal["early", "middle", "upper"] | None = None
    favorite_subject_id: int | None = None
    weekly_goal_days: int | None = Field(default=None, ge=1, le=7)
    preferences: PreferencesUpdate | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type, not a secret
    user: UserOut


# --- interactions ---------------------------------------------------------------
class InteractionIn(BaseModel):
    event_type: str = Field(max_length=40)
    topic_id: int | None = None
    lesson_id: int | None = None
    question_id: int | None = None
    session_id: int | None = None
    payload: dict = Field(default_factory=dict)


class InteractionBatch(BaseModel):
    events: list[InteractionIn] = Field(min_length=1, max_length=50)


class LessonComplete(BaseModel):
    seconds: int = Field(ge=0, le=7200)
    progress: float = Field(ge=0, le=1)


# --- quiz -------------------------------------------------------------------------
class QuizGenerateRequest(BaseModel):
    topic_id: int


class AnswerIn(BaseModel):
    question_id: int
    selected_index: int | None = Field(default=None, ge=0, le=5)  # None = skipped
    response_ms: int = Field(default=0, ge=0, le=3_600_000)
    hints_used: int = Field(default=0, ge=0, le=10)
    answer_changes: int = Field(default=0, ge=0, le=20)
    confidence: int | None = Field(default=None, ge=1, le=3)


class QuizSubmitRequest(BaseModel):
    answers: list[AnswerIn] = Field(max_length=10)
    session_id: int | None = None


# --- tutor ---------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=800)
    topic_id: int | None = None
    conversation_id: int | None = None
    intent: Literal["explain", "easier", "hint", "quiz", "confused", "different", "general"] | None = None


class FeedbackRequest(BaseModel):
    value: Literal["helpful", "not_helpful", "too_long", "too_hard", "too_easy"]


# --- goals ---------------------------------------------------------------------
class GoalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    topic_id: int | None = None
    target_mastery: float | None = Field(default=None, ge=0.3, le=1.0)
    due_date: date | None = None


class GoalUpdate(BaseModel):
    status: Literal["active", "completed", "archived"]


# --- demos -----------------------------------------------------------------------
class AdaptivePreviewRequest(BaseModel):
    level: float = Field(ge=0, le=100)
    explanation_length: Literal["short", "medium", "detailed"] = "medium"
    prefers_visuals: bool = True
    prefers_examples: bool = True
    pace: Literal["relaxed", "steady", "quick"] = "steady"


class TutorDemoRequest(BaseModel):
    action: Literal["understand", "confused", "hint", "different"]
    level: float = Field(default=45, ge=0, le=100)
    last_style: Literal["step_by_step", "worked_example", "guided_discovery", "concise"] | None = None


class StudyPlanRequest(BaseModel):
    minutes_per_day: int = Field(default=15, ge=5, le=60)
    days: int = Field(default=5, ge=3, le=7)
