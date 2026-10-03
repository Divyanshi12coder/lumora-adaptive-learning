"""Test configuration.

By default tests run against a throwaway SQLite database. Set TEST_DATABASE_URL
to a PostgreSQL URL (CI does this) to run the same suite against PostgreSQL +
pgvector; in that case run `alembic upgrade head` first.
"""

import os
import tempfile
import uuid
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="lumora-tests-"))
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ.setdefault("ENVIRONMENT", "test")
os.environ["AI_PROVIDER"] = "demo"
os.environ["EMBEDDING_PROVIDER"] = "local"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["SEED_ON_STARTUP"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        yield session


def _register(client, name="Ava"):
    email = f"{name.lower()}-{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sunny1234", "display_name": name})
    assert r.status_code == 201, r.text
    data = r.json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"], email


@pytest.fixture
def auth(client):
    headers, user, _ = _register(client)
    return headers


@pytest.fixture
def make_user(client):
    return lambda name="Kid": _register(client, name)


@pytest.fixture
def topic(client, auth):
    subjects = client.get("/api/subjects", headers=auth).json()
    return subjects[0]["topics"][0]  # Fractions
