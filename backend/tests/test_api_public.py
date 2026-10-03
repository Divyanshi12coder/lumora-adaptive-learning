from app.core.config import get_settings
from app.core.middleware import limiter


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "demo" and body["ai_demo_mode"] is True


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_cors_allows_frontend_origin(client):
    r = client.options("/api/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    r = client.options("/api/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers


def test_adaptive_preview_runs_real_engine(client):
    low = client.post("/api/adaptive/preview", json={"level": 5}).json()["strategy"]
    high = client.post("/api/adaptive/preview", json={"level": 95}).json()["strategy"]
    assert low["support_score"] > high["support_score"]
    assert (low["difficulty"], high["difficulty"]) == ("easy", "hard")
    assert client.post("/api/adaptive/preview", json={"level": 150}).status_code == 422


def test_tutor_demo_adapts_to_actions(client):
    confused = client.post("/api/demo/tutor", json={"action": "confused", "level": 50}).json()
    understood = client.post("/api/demo/tutor", json={"action": "understand", "level": 50}).json()
    assert confused["level"] < 50 < understood["level"]
    assert confused["strategy"]["explanation_style"] == "step_by_step"
    assert confused["reply"]["message"]
    assert confused["provider"] == "demo"


def test_request_size_limit(client):
    r = client.post("/api/adaptive/preview", content=b"{}", headers={"Content-Length": str(50 * 1024 * 1024),
                                                                  "Content-Type": "application/json"})
    assert r.status_code == 413


def test_rate_limiting(client):
    settings = get_settings()
    settings.rate_limit_enabled = True
    limiter.reset()
    try:
        codes = [client.post("/api/auth/login", json={"email": "x@example.com", "password": "nope1234"}).status_code
                 for _ in range(12)]
        assert 429 in codes
    finally:
        settings.rate_limit_enabled = False
        limiter.reset()


def test_openapi_documents_core_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    for p in ["/api/auth/register", "/api/quiz/generate", "/api/tutor/chat", "/api/documents/{doc_id}/ingest",
              "/api/analytics", "/api/interactions", "/api/lessons/{lesson_id}/start"]:
        assert p in paths


def test_unexpected_errors_are_child_friendly(client, monkeypatch):
    from app.services import dashboard

    def boom(*_a, **_k):
        raise RuntimeError("internal stack trace details")

    monkeypatch.setattr(dashboard, "build", boom)
    from tests.conftest import _register

    headers, _, _ = _register(client)
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/api/dashboard", headers=headers)
    assert r.status_code == 500
    assert "stack trace" not in r.text and "Oops" in r.json()["detail"]
