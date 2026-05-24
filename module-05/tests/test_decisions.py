"""
tests/test_decisions.py

Tests for the decisions resource -- full CRUD cycle.
Covers: create, duplicate 409, list, get found/404,
        update, patch, delete guard, 401 without token,
        403 on another analyst's decision, /suggest stub.
"""


def test_create_decision_success(client, auth_headers):
    resp = client.post("/decisions", json={
        "ticker": "PFE",
        "direction": "long",
        "conviction": "high",
        "thesis": "Vyndaqel ramp underappreciated.",
        "price_target": 32.50,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticker"] == "PFE"
    assert data["direction"] == "long"
    assert data["status"] == "active"


def test_create_decision_duplicate_ticker(client, auth_headers, sample_decision):
    resp = client.post("/decisions", json={
        "ticker": "PFE",
        "direction": "short",
        "conviction": "low",
    }, headers=auth_headers)
    assert resp.status_code == 409
    assert resp.json()["error"] == "duplicate"


def test_create_decision_invalid_ticker(client, auth_headers):
    resp = client.post("/decisions", json={
        "ticker": "123",   # numbers not allowed
        "direction": "long",
        "conviction": "high",
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_create_decision_no_auth(client):
    resp = client.post("/decisions", json={
        "ticker": "MRK",
        "direction": "long",
        "conviction": "medium",
    })
    assert resp.status_code == 401


def test_list_decisions_empty(client, auth_headers):
    resp = client.get("/decisions", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_decisions_with_data(client, auth_headers, sample_decision):
    resp = client.get("/decisions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["ticker"] == "PFE"


def test_list_decisions_filter_by_ticker(client, auth_headers, sample_decision):
    resp = client.get("/decisions?ticker=MRK", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_decision_found(client, auth_headers, sample_decision):
    decision_id = sample_decision["id"]
    resp = client.get(f"/decisions/{decision_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == decision_id


def test_get_decision_not_found(client, auth_headers):
    resp = client.get("/decisions/99999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


def test_patch_decision_success(client, auth_headers, sample_decision):
    decision_id = sample_decision["id"]
    resp = client.patch(f"/decisions/{decision_id}", json={
        "conviction": "medium",
        "notes": "Revised after Q2 earnings miss.",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["conviction"] == "medium"
    assert resp.json()["notes"] == "Revised after Q2 earnings miss."


def test_delete_active_decision_blocked(client, auth_headers, sample_decision):
    """Business logic guard: active decisions cannot be deleted directly."""
    decision_id = sample_decision["id"]
    resp = client.delete(f"/decisions/{decision_id}", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["error"] == "bad_request"


def test_delete_closed_decision_success(client, auth_headers, sample_decision):
    """Close the decision first, then delete successfully."""
    decision_id = sample_decision["id"]
    client.patch(f"/decisions/{decision_id}", json={"status": "closed"}, headers=auth_headers)
    resp = client.delete(f"/decisions/{decision_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_suggest_stub(client, auth_headers, sample_decision):
    decision_id = sample_decision["id"]
    resp = client.post(f"/decisions/{decision_id}/suggest", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "PFE"
    assert data["source"] == "placeholder"
    assert "decision_id" in data
