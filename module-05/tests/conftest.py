"""
tests/conftest.py

Test fixtures for the Caduceus decision-app API.
Uses an in-memory SQLite database -- isolated from development data.
Every test function gets a fresh database state via function-scoped fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database -- in-memory SQLite, isolated per test session
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test_caduceus.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(reset_db):
    """FastAPI TestClient with the test database injected."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_analyst(client):
    """Register a test analyst and return their credentials."""
    resp = client.post("/auth/register", json={
        "name": "Test Analyst",
        "email": "analyst@test.com",
        "password": "testpassword123",
        "role": "analyst",
    })
    assert resp.status_code == 201
    return {"email": "analyst@test.com", "password": "testpassword123"}


@pytest.fixture
def auth_headers(client, registered_analyst):
    """Login and return Authorization headers for protected endpoints."""
    resp = client.post("/auth/login", json=registered_analyst)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_decision(client, auth_headers):
    """Create a sample PFE decision and return the response JSON."""
    resp = client.post("/decisions", json={
        "ticker": "PFE",
        "direction": "long",
        "conviction": "high",
        "thesis": "Vyndaqel ramp underappreciated by market.",
        "price_target": 32.50,
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()
