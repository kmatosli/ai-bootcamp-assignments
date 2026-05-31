"""tests/test_students.py -- 10 tests covering the full CRUD cycle."""


def test_create_student_success(client):
    resp = client.post("/students", json={
        "name": "Alice Johnson",
        "email": "alice@student.edu",
        "track": "ai",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice Johnson"
    assert data["email"] == "alice@student.edu"
    assert data["status"] == "active"


def test_create_student_duplicate_email(client, sample_student):
    resp = client.post("/students", json={
        "name": "Another Student",
        "email": "test@student.edu",  # same email as sample_student
        "track": "data_science",
    })
    assert resp.status_code == 409


def test_create_student_missing_field(client):
    resp = client.post("/students", json={
        "name": "Incomplete Student",
        # missing email and track
    })
    assert resp.status_code == 422


def test_list_students_empty(client):
    resp = client.get("/students")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_students_with_data(client, sample_student):
    resp = client.get("/students")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_student_found(client, sample_student):
    student_id = sample_student["id"]
    resp = client.get(f"/students/{student_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == student_id


def test_get_student_not_found(client):
    resp = client.get("/students/99999")
    assert resp.status_code == 404


def test_patch_student_success(client, sample_student):
    student_id = sample_student["id"]
    resp = client.patch(f"/students/{student_id}", json={"track": "data_science"})
    assert resp.status_code == 200
    assert resp.json()["track"] == "data_science"


def test_delete_student_success(client, sample_student):
    student_id = sample_student["id"]
    resp = client.delete(f"/students/{student_id}")
    assert resp.status_code == 204
    # Confirm deleted
    resp2 = client.get(f"/students/{student_id}")
    assert resp2.status_code == 404


def test_delete_student_not_found(client):
    resp = client.delete("/students/99999")
    assert resp.status_code == 404
