"""Pydantic schemas that every LLM output must validate against.

Schemas avoid defaults and numeric constraints so they translate directly into
strict JSON Schema for OpenAI `json_schema` mode and Anthropic structured
outputs. Semantic checks (e.g. a valid `correct_index`) happen after parsing.
"""

from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TutorReply(_Strict):
    message: str  # main explanation, adapted to the teaching strategy
    steps: list[str]  # numbered steps (may be empty for concise style)
    examples: list[str]
    check_question: str | None  # a gentle "can you try?" question
    encouragement: str
    follow_ups: list[str]  # suggested next prompts for the learner
    used_source_numbers: list[int]  # which [n] context passages were used


class GeneratedQuestion(_Strict):
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str
    hint: str


class GeneratedQuiz(_Strict):
    questions: list[GeneratedQuestion]


class DocumentSummary(_Strict):
    summary: str
    key_points: list[str]


class StudyPlanItem(_Strict):
    day: str
    focus: str
    activity: str
    minutes: int


class StudyPlan(_Strict):
    title: str
    items: list[StudyPlanItem]
    note: str
