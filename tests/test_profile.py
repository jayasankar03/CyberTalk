
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from user_model import User

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

    token = get_profile_token(user)

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

    token = get_profile_token(
        user,
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
def get_profile_token(user, expires_delta=None):
    db = TestingSessionLocal()

    try:
        db_user = db.query(User).filter(User.id == user["id"]).first()

        if db_user is None:
            raise ValueError("Test user not found.")

        return create_access_token(
            data={
                "sub": str(db_user.id),
                "role": db_user.role,
                "auth_version": db_user.auth_version,
            },
            expires_delta=expires_delta,
        )
    finally:
        db.close()

def test_update_my_profile_success():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "updateduser",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "updated@example.com"
    assert "hashed_password" not in data


def test_update_my_profile_normalizes_input():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "  updateduser  ",
            "email": "  UPDATED@EXAMPLE.COM  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "updateduser"
    assert response.json()["email"] == "updated@example.com"


def test_update_my_profile_duplicate_username():
    user = create_test_user()

    client.post(
        "/register",
        json={
            "username": "anotheruser",
            "email": "another@example.com",
            "password": "SecurePass123",
        },
    )

    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "anotheruser",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already registered."


def test_update_my_profile_duplicate_email():
    user = create_test_user()

    client.post(
        "/register",
        json={
            "username": "anotheruser",
            "email": "another@example.com",
            "password": "SecurePass123",
        },
    )

    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "updateduser",
            "email": "another@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already registered."


def test_update_my_profile_without_token():
    response = client.put(
        "/users/me",
        json={
            "username": "updateduser",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 401


def test_update_my_profile_invalid_username():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "ab",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 422


def test_update_my_profile_invalid_email():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "updateduser",
            "email": "invalid-email",
        },
    )

    assert response.status_code == 422
