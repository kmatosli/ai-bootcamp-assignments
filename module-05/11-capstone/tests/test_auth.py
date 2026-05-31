"""
tests/test_auth.py

Tests for authentication endpoints:
  register, login, /users/me, token validation.
"""


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "name": "Amennai Beyeen",
        "email": "abeyeen@rhenman.com",
        "password": "securepass123",
        "role": "analyst",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    payload = {
        "name": "Analyst One",
        "email": "same@rhenman.com",
        "password": "password123",
        "role": "analyst",
    }
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error"] == "duplicate"


def test_login_success(client, registered_analyst):
    resp = client.post("/auth/login", json=registered_analyst)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, registered_analyst):
    resp = client.post("/auth/login", json={
        "email": registered_analyst["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "analyst@test.com"
    assert data["role"] == "analyst"


def test_get_me_no_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
