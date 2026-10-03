"""Child-safety guardrails applied before and after every LLM call.

This is a conservative, rule-based first line of defence (fast, offline,
testable). Real providers additionally receive a strict system prompt. In
production you would add a provider moderation endpoint as a second layer.

Actions:
  allow    - normal tutoring
  redirect - off-limits topic: refuse kindly and steer back to learning
  support  - wellbeing concern: respond with care and point to a trusted adult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SELF_HARM = [
    r"\bkill(ing)? myself\b", r"\bsuicid", r"\bwant(s)? to die\b", r"\bhurt(ing)? myself\b",
    r"\bself[- ]?harm", r"\bcut(ting)? myself\b", r"\bend my life\b", r"\bno reason to live\b",
]
ABUSE = [
    r"\b(someone|somebody|he|she|they|my \w+) (hits|hurts|touches) me\b", r"\bbeing (abused|bullied)\b",
    r"\bi('m| am) (scared|afraid) (to go )?home\b",
]
SEXUAL = [r"\bsex(ual|y)?\b", r"\bporn", r"\bnude(s)?\b", r"\bnaked\b", r"\berotic", r"\bhorny\b"]
DANGEROUS = [
    r"\b(make|build|create)\b.{0,30}\b(bomb|explosive|weapon|gun|poison)", r"\bhow to (hack|steal|shoplift)",
    r"\b(buy|get|use|take)\b.{0,20}\b(drugs|cocaine|weed|vape|alcohol)\b", r"\bhurt (someone|somebody|people)\b",
]
DIAGNOSIS = [
    r"\b(do|does|could|might) (i|he|she|my \w+) have (adhd|autism|dyslexia|add|a disorder|a disability)",
    r"\bam i (autistic|dyslexic|adhd)", r"\bdiagnos(e|is)\b",
]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(\+?\d[\d\s().-]{7,}\d)(?!\d)")
ADDRESS = re.compile(r"\b(i live (at|on)|my address is)\b[^.?!\n]*", re.I)

SUPPORT_MESSAGE = (
    "I'm really glad you told me, and I care about how you're feeling. I'm an AI learning helper, so I can't help "
    "with this the way a person can. Please talk to a trusted adult right now - like a parent, carer, teacher or "
    "school counsellor. If you ever feel in danger, contact your local emergency number or a children's helpline."
)
REDIRECT_MESSAGE = (
    "That's not something I can help with - I'm here to help you learn. Let's get back to your lessons! "
    "You could ask me to explain a topic, give you an example, or quiz you."
)
DIAGNOSIS_MESSAGE = (
    "That's a really thoughtful question. I'm a learning helper, not a doctor, so I can't tell whether someone has "
    "ADHD, dyslexia, autism or any other condition. A trusted adult can talk with a doctor or specialist about it. "
    "What I *can* do is change how I teach so it works better for you - shorter steps, more pictures, read-aloud and more!"
)


@dataclass
class SafetyResult:
    action: str = "allow"
    category: str | None = None
    message: str | None = None
    text: str = ""
    flags: list[str] = field(default_factory=list)


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def redact_pii(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    if EMAIL.search(text):
        text = EMAIL.sub("[email removed]", text)
        flags.append("pii_email")
    if ADDRESS.search(text):
        text = ADDRESS.sub("[address removed]", text)
        flags.append("pii_address")
    if PHONE.search(text):
        text = PHONE.sub("[number removed]", text)
        flags.append("pii_phone")
    return text, flags


def screen_input(text: str) -> SafetyResult:
    clean, flags = redact_pii(text)
    if _any(SELF_HARM, text) or _any(ABUSE, text):
        return SafetyResult("support", "wellbeing", SUPPORT_MESSAGE, clean, [*flags, "wellbeing"])
    if _any(SEXUAL, text):
        return SafetyResult("redirect", "sexual_content", REDIRECT_MESSAGE, clean, [*flags, "sexual_content"])
    if _any(DANGEROUS, text):
        return SafetyResult("redirect", "dangerous", REDIRECT_MESSAGE, clean, [*flags, "dangerous"])
    if _any(DIAGNOSIS, text):
        return SafetyResult("redirect", "medical_diagnosis", DIAGNOSIS_MESSAGE, clean, [*flags, "medical_diagnosis"])
    return SafetyResult("allow", None, None, clean, flags)


def screen_output(text: str) -> SafetyResult:
    """Check generated text before it reaches a child."""
    if _any(SEXUAL, text) or _any(DANGEROUS, text) or _any(SELF_HARM, text):
        return SafetyResult("redirect", "unsafe_output", REDIRECT_MESSAGE, REDIRECT_MESSAGE, ["unsafe_output"])
    clean, flags = redact_pii(text)
    return SafetyResult("allow", None, None, clean, flags)
