from app.services.tutor import classify_intent


def test_intent_classifier():
    assert classify_intent("Can you give me a hint?") == "hint"
    assert classify_intent("quiz me on this") == "quiz"
    assert classify_intent("I don't understand") == "confused"
    assert classify_intent("make it easier please") == "easier"
    assert classify_intent("explain it differently") == "different"
    assert classify_intent("What is photosynthesis?") == "explain"


def test_chat_is_grounded_adapted_and_labelled_demo(client, auth, topic):
    r = client.post("/api/tutor/chat", headers=auth, json={"message": "Explain fractions to me", "topic_id": topic["id"]})
    assert r.status_code == 200
    body = r.json()
    msg = body["message"]
    assert msg["content"]
    assert msg["is_demo"] is True and "Demo mode" in body["notice"]
    assert msg["sources"] and any(s["used"] for s in msg["sources"])
    assert "Fractions" in msg["sources"][0]["title"]
    assert body["strategy"]["explanation_style"] in {"step_by_step", "worked_example", "guided_discovery", "concise"}


def test_topic_is_inferred_from_retrieval(client, auth):
    body = client.post("/api/tutor/chat", headers=auth, json={"message": "How do plants make food from sunlight?"}).json()
    assert body["topic_id"] is not None
    assert "Photosynthesis" in body["message"]["sources"][0]["title"]


def test_confused_intent_simplifies(client, auth, topic):
    body = client.post("/api/tutor/chat", headers=auth,
                       json={"message": "I don't understand this", "topic_id": topic["id"]}).json()
    assert body["strategy"]["difficulty"] == "easy"
    assert body["strategy"]["explanation_style"] == "step_by_step"
    assert "No worries" in body["message"]["content"]


def test_explain_differently_rotates_style(client, auth, topic):
    first = client.post("/api/tutor/chat", headers=auth, json={"message": "explain fractions", "topic_id": topic["id"]}).json()
    second = client.post("/api/tutor/chat", headers=auth, json={
        "message": "can you explain it differently?", "conversation_id": first["conversation_id"]}).json()
    assert second["strategy"]["explanation_style"] != first["strategy"]["explanation_style"]


def test_safety_and_privacy_in_chat(client, auth):
    body = client.post("/api/tutor/chat", headers=auth, json={"message": "I want to hurt myself"}).json()
    assert "trusted adult" in body["message"]["content"]
    body = client.post("/api/tutor/chat", headers=auth,
                       json={"message": "my email is kid@example.com, explain shapes"}).json()
    assert "kid@example.com" not in body["user_message"]["content"]


def test_feedback_updates_learner_preferences(client, auth, topic):
    body = client.post("/api/tutor/chat", headers=auth, json={"message": "explain fractions", "topic_id": topic["id"]}).json()
    mid = body["message"]["id"]
    fb = client.post(f"/api/tutor/messages/{mid}/feedback", headers=auth, json={"value": "too_long"}).json()
    assert fb["length_bias"] > 0
    assert client.post(f"/api/tutor/messages/{mid}/feedback", headers=auth, json={"value": "meh"}).status_code == 422


def test_history_and_isolation(client, auth, make_user, topic):
    body = client.post("/api/tutor/chat", headers=auth, json={"message": "explain fractions", "topic_id": topic["id"]}).json()
    convs = client.get("/api/tutor/history", headers=auth).json()
    assert any(c["id"] == body["conversation_id"] for c in convs)
    msgs = client.get(f"/api/tutor/history?conversation_id={body['conversation_id']}", headers=auth).json()["messages"]
    assert [m["role"] for m in msgs[:2]] == ["user", "assistant"]
    other, _, _ = make_user("Snoop")
    assert client.get(f"/api/tutor/history?conversation_id={body['conversation_id']}", headers=other).status_code == 404


def test_message_length_limit(client, auth):
    assert client.post("/api/tutor/chat", headers=auth, json={"message": "x" * 801}).status_code == 422
