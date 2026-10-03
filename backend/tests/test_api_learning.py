from sqlalchemy import select

from app.models import AdaptiveStrategyRecord, Answer, InteractionEvent, MasteryScore, ModelPrediction, QuizAttempt


def _quiz(client, auth, topic_id):
    r = client.post("/api/quiz/generate", headers=auth, json={"topic_id": topic_id})
    assert r.status_code == 201, r.text
    return r.json()


def _correct_index(db, attempt_id, qid):
    """Map the stored correct option to the *shown* (shuffled) index."""
    from app.models import Question

    attempt = db.get(QuizAttempt, attempt_id)
    shown = attempt.strategy["option_maps"][str(qid)]
    return shown.index(db.get(Question, qid).correct_index)


def test_subjects_and_topics(client, auth):
    subjects = client.get("/api/subjects", headers=auth).json()
    assert [s["slug"] for s in subjects] == ["mathematics", "science", "reading", "history"]
    assert all(len(s["topics"]) == 3 for s in subjects)
    topics = client.get("/api/topics?subject=science", headers=auth).json()
    assert {t["subject"]["slug"] for t in topics} == {"science"}
    assert len(client.get("/api/courses", headers=auth).json()) == 4


def test_lesson_is_adapted_and_tracked(client, auth, topic, db):
    r = client.post(f"/api/lessons/{topic['lesson_id']}/start", headers=auth)
    body = r.json()
    assert body["strategy"]["band"] in {"high_support", "guided", "balanced", "stretch"}
    shown = [s["key"] for s in body["sections"] if s["shown"]]
    assert "key_idea" in shown and "summary" in shown
    done = client.post(f"/api/lessons/{topic['lesson_id']}/complete", headers=auth, json={"seconds": 200, "progress": 1})
    assert done.status_code == 200
    assert client.get("/api/lessons/99999", headers=auth).status_code == 404


def test_interaction_tracking_validates_and_minimises(client, auth, db, topic):
    r = client.post("/api/interactions", headers=auth, json={"events": [
        {"event_type": "section_viewed", "topic_id": topic["id"], "payload": {"section": "steps", "secret": "x"}},
        {"event_type": "read_aloud_used", "topic_id": topic["id"]},
    ]})
    assert r.status_code == 201 and r.json()["recorded"] == 2
    ev = db.get(InteractionEvent, r.json()["ids"][0])
    assert ev.payload == {"section": "steps"}  # unknown keys dropped
    bad = client.post("/api/interactions", headers=auth, json={"event_type": "mouse_moved"})
    assert bad.status_code == 422


def test_sessions(client, auth):
    s = client.post("/api/sessions/start", headers=auth).json()
    assert client.post(f"/api/sessions/{s['session_id']}/end", headers=auth).json()["ended_at"]


def test_quiz_generate_submit_updates_mastery_and_persists(client, auth, topic, db):
    quiz = _quiz(client, auth, topic["id"])
    assert quiz["difficulty"] in {"easy", "medium", "hard"}
    assert 3 <= len(quiz["questions"]) <= 8
    assert all("option_map" not in q for q in quiz["questions"])
    assert all(len(q["options"]) == quiz["strategy"]["option_count"] for q in quiz["questions"])

    answers = [{"question_id": q["id"], "selected_index": _correct_index(db, quiz["attempt_id"], q["id"]),
                "response_ms": 12000, "confidence": 3} for q in quiz["questions"]]
    res = client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=auth, json={"answers": answers}).json()
    assert res["score"] == 1.0
    assert res["mastery_after"] > res["mastery_before"]
    assert res["celebrate"] is True
    assert res["next_difficulty"] in {"easy", "medium", "hard"}

    db.expire_all()
    attempt = db.get(QuizAttempt, quiz["attempt_id"])
    assert attempt.status == "completed"
    assert db.scalar(select(MasteryScore).where(MasteryScore.user_id == attempt.user_id)).attempts == len(answers)
    assert len(db.scalars(select(Answer).where(Answer.attempt_id == attempt.id)).all()) == len(answers)
    # engine decisions and ML predictions are audited
    assert db.scalars(select(AdaptiveStrategyRecord).where(AdaptiveStrategyRecord.user_id == attempt.user_id)).first()
    assert db.scalars(select(ModelPrediction).where(ModelPrediction.user_id == attempt.user_id)).first()

    again = client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=auth, json={"answers": answers})
    assert again.status_code == 409


def test_wrong_answers_give_kind_feedback_and_revision(client, auth, topic, db):
    quiz = _quiz(client, auth, topic["id"])
    answers = []
    for q in quiz["questions"]:
        right = _correct_index(db, quiz["attempt_id"], q["id"])
        answers.append({"question_id": q["id"], "selected_index": (right + 1) % len(q["options"])})
    answers[0]["selected_index"] = None  # skipped
    res = client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=auth, json={"answers": answers}).json()
    assert res["score"] == 0
    assert res["revision"]["needed"] is True
    assert all("wrong" not in r["feedback"].lower() for r in res["results"])
    assert res["results"][0]["skipped"] is True


def test_adaptivity_after_struggling(client, make_user, db):
    headers, _, _ = make_user("Leo")
    topic = client.get("/api/topics?subject=history", headers=headers).json()[0]
    for _ in range(3):
        quiz = _quiz(client, headers, topic["id"])
        answers = []
        for q in quiz["questions"]:
            right = _correct_index(db, quiz["attempt_id"], q["id"])
            answers.append({"question_id": q["id"], "selected_index": (right + 1) % len(q["options"]),
                            "response_ms": 60000, "hints_used": 1, "confidence": 1})
        client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=headers, json={"answers": answers})
    nxt = _quiz(client, headers, topic["id"])
    assert nxt["difficulty"] == "easy"
    assert nxt["strategy"]["hint_level"] in {"guided", "full"}
    assert nxt["strategy"]["option_count"] == 3


def test_quiz_ownership_and_hints(client, auth, make_user, topic):
    quiz = _quiz(client, auth, topic["id"])
    qid = quiz["questions"][0]["id"]
    hint = client.get(f"/api/quiz/{quiz['attempt_id']}/hint/{qid}", headers=auth).json()
    assert hint["hint"]
    other, _, _ = make_user("Other")
    assert client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=other, json={"answers": []}).status_code == 404
    assert client.get(f"/api/quiz/{quiz['attempt_id']}/hint/{qid}", headers=other).status_code == 404


def test_invalid_answer_index_rejected(client, auth, topic):
    quiz = _quiz(client, auth, topic["id"])
    r = client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=auth,
                    json={"answers": [{"question_id": quiz["questions"][0]["id"], "selected_index": 5}]})
    assert r.status_code == 422


def test_dashboard_analytics_recommendations(client, auth, topic, db):
    quiz = _quiz(client, auth, topic["id"])
    answers = [{"question_id": q["id"], "selected_index": 0, "response_ms": 9000} for q in quiz["questions"]]
    client.post(f"/api/quiz/{quiz['attempt_id']}/submit", headers=auth, json={"answers": answers})

    d = client.get("/api/dashboard", headers=auth).json()
    assert d["progress"]["questions_answered"] == len(answers)
    assert d["journey"]["current"] in d["journey"]["stages"]
    assert len(d["week"]) == 7
    assert d["today"]["topic"]["title"]
    assert any(a["key"] == "problem_solver" for a in d["achievements"])

    a = client.get("/api/analytics", headers=auth).json()
    assert a["summary"]["questions_answered"] == len(answers)
    assert a["ml"]["struggle_source"] in {"model", "fallback"}
    assert a["current_strategy"]["factors"]
    assert len(a["accuracy_trend"]) == 30

    recs = client.get("/api/recommendations?refresh=true", headers=auth).json()
    assert recs and recs[0]["score"] >= recs[-1]["score"]
    assert {"mastery", "readiness"} <= set(recs[0]["factors"])

    plan = client.post("/api/study-plan", headers=auth, json={"minutes_per_day": 10, "days": 3}).json()
    assert len(plan["items"]) == 3 and plan["is_demo"] is True

    card = client.get("/api/ml/model-card", headers=auth).json()
    assert "struggle_model" in card


def test_goals_crud(client, auth, topic):
    g = client.post("/api/goals", headers=auth, json={"title": "Master fractions", "topic_id": topic["id"]}).json()
    assert g["target_mastery"] == 0.8 and g["current_mastery"] is not None
    assert client.patch(f"/api/goals/{g['id']}", headers=auth, json={"status": "completed"}).json()["status"] == "completed"
    assert len(client.get("/api/goals", headers=auth).json()) == 1
    assert client.delete(f"/api/goals/{g['id']}", headers=auth).status_code == 204
    assert client.post("/api/goals", headers=auth, json={"title": "x"}).status_code == 422
