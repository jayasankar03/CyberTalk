
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure a test-only JWT secret.
os.environ["CYBERTALK_SECRET_KEY"] = "cybertalk-test-secret-key-for-tests"

from main import app
from auth import create_access_token
from database import get_db, Base


# Create an isolated in-memory test database.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# Reset the database before every test.
@pytest.fixture(autouse=True)
def reset_test_database():
    # Reapply the test database override before every test.
    app.dependency_overrides[get_db] = override_get_db

    # Start each test with a clean database.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    # Clean up after the test.
    Base.metadata.drop_all(bind=engine)


def create_test_user():
    response = client.post(
        "/register",
        json={
            "username": "profileuser",
            "email": "profile@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201

    return response.json()["user"]


def test_get_my_profile_success():
    user = create_test_user()

    token = create_access_token(
        data={"sub": str(user["id"]), "role": "user"}
    )

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user["id"]
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@example.com"
    assert data["role"] == "user"
    assert "created_at" in data
    assert "hashed_password" not in data


def test_get_my_profile_without_token():
    response = client.get("/users/me")

    assert response.status_code == 401


def test_get_my_profile_with_invalid_token():
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_get_my_profile_with_expired_token():
    user = create_test_user()

    token = create_access_token(
        data={"sub": str(user["id"]), "role": "user"},
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_get_my_profile_for_nonexistent_user():
    token = create_access_token(
        data={"sub": "99999", "role": "user"}
    )

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
