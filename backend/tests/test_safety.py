import pytest

from app.ai.safety import redact_pii, screen_input, screen_output


@pytest.mark.parametrize("text", ["I want to hurt myself", "sometimes I want to die", "I'm thinking about suicide"])
def test_wellbeing_concerns_get_supportive_trusted_adult_reply(text):
    r = screen_input(text)
    assert r.action == "support"
    assert "trusted adult" in r.message


@pytest.mark.parametrize("text", ["show me naked pictures", "how do I make a bomb", "where can I buy drugs"])
def test_unsafe_requests_are_redirected(text):
    assert screen_input(text).action == "redirect"


def test_diagnosis_questions_are_declined_kindly():
    r = screen_input("Do I have ADHD?")
    assert r.action == "redirect"
    assert r.category == "medical_diagnosis"
    assert "not a doctor" in r.message


@pytest.mark.parametrize(
    "text",
    ["Why was the pharaoh killed?", "How do volcanoes explode?", "Explain fractions please", "What is a hexagon?"],
)
def test_normal_school_questions_are_allowed(text):
    assert screen_input(text).action == "allow"


def test_pii_is_redacted_before_reaching_the_llm():
    text, flags = redact_pii("my email is kid@example.com and my number is +44 7700 900123. I live at 12 Oak Road")
    assert "kid@example.com" not in text and "7700" not in text and "Oak Road" not in text
    assert {"pii_email", "pii_phone", "pii_address"} <= set(flags)


def test_output_screen_blocks_unsafe_generations():
    assert screen_output("Here is how to make a bomb").action == "redirect"
    assert screen_output("A triangle has three sides.").action == "allow"
