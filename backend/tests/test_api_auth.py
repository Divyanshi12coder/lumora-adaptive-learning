def test_register_login_me_logout_flow(client, make_user):
    headers, user, email = make_user("Mia")
    assert user["display_name"] == "Mia"
    assert user["preferences"]["text_scale"] == 1.0

    r = client.post("/api/auth/login", json={"email": email.upper(), "password": "sunny1234"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    h2 = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/me", headers=h2).json()["email"] == email

    assert client.post("/api/auth/logout", headers=h2).status_code == 204
    # logout revokes every previously issued token
    assert client.get("/api/me", headers=h2).status_code == 401
    assert client.get("/api/me", headers=headers).status_code == 401


def test_password_is_hashed_never_stored_plain(client, make_user, db):
    from sqlalchemy import select

    from app.models import User

    _, _, email = make_user()
    stored = db.scalar(select(User).where(User.email == email))
    assert stored.password_hash != "sunny1234"
    assert stored.password_hash.startswith("$2")  # bcrypt


def test_duplicate_email_rejected(client, make_user):
    _, _, email = make_user()
    r = client.post("/api/auth/register", json={"email": email, "password": "sunny1234", "display_name": "X"})
    assert r.status_code == 409


def test_weak_password_gives_friendly_message(client):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "abcdefghi", "display_name": "A"})
    assert r.status_code == 422
    assert "letters and numbers" in r.json()["detail"]


def test_wrong_password_is_generic(client, make_user):
    _, _, email = make_user()
    r = client.post("/api/auth/login", json={"email": email, "password": "wrong-pass1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Email or password is not correct."


def test_protected_routes_require_valid_token(client):
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/dashboard", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_profile_update_persists_preferences(client, auth):
    r = client.put("/api/profile", headers=auth, json={
        "avatar": "owl", "weekly_goal_days": 4,
        "preferences": {"readable_font": True, "text_scale": 1.25, "explanation_length": "short"},
    })
    assert r.status_code == 200
    prefs = client.get("/api/profile", headers=auth).json()["preferences"]
    assert prefs["readable_font"] is True and prefs["text_scale"] == 1.25 and prefs["explanation_length"] == "short"


def test_profile_validation(client, auth):
    assert client.put("/api/profile", headers=auth, json={"preferences": {"text_scale": 5}}).status_code == 422


def test_delete_account_removes_data(client, make_user):
    headers, _, email = make_user()
    assert client.delete("/api/me", headers=headers).status_code == 204
    assert client.post("/api/auth/login", json={"email": email, "password": "sunny1234"}).status_code == 401
