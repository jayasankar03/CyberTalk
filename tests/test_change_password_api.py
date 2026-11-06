
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["CYBERTALK_SECRET_KEY"] = (
    "cybertalk-test-secret-key-for-tests"
)

from main import app
from auth import create_access_token
from database import get_db, Base
from user_model import User
from security import verify_password
from password_reset_model import PasswordResetToken


# Isolated in-memory test database.
engine = create_engine(
    "sqlite://",
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


@pytest.fixture(autouse=True)
def reset_test_database():
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


def create_test_user():
    response = client.post(
        "/register",
        json={
            "username": "changepassuser",
            "email": "changepass@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201

    return response.json()["user"]


def get_auth_headers(user):
    db = TestingSessionLocal()

    try:
        db_user = db.query(User).filter(User.id == user["id"]).first()

        if db_user is None:
            raise ValueError("Test user not found.")

        token = create_access_token(
            data={
                "sub": str(db_user.id),
                "role": db_user.role,
                "auth_version": db_user.auth_version,
            }
        )
    finally:
        db.close()

    return {
        "Authorization": f"Bearer {token}"
    }

def change_password(
    headers,
    current_password="SecurePass123",
    new_password="NewSecurePass456",
    confirm_new_password="NewSecurePass456",
):
    return client.post(
        "/change-password",
        headers=headers,
        json={
            "current_password": current_password,
            "new_password": new_password,
            "confirm_new_password": confirm_new_password,
        },
    )


def test_change_password_success():
    user = create_test_user()
    headers = get_auth_headers(user)

    response = change_password(headers)

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Password changed successfully."
    )
    old_token_response = client.get(
        "/users/me",
        headers=headers,
    )

    assert old_token_response.status_code == 401
    db = TestingSessionLocal()
    try:
        stored_user = db.query(User).filter(
            User.id == user["id"]
        ).first()

        assert verify_password(
            "NewSecurePass456",
            stored_user.hashed_password,
        )

        assert not verify_password(
            "SecurePass123",
            stored_user.hashed_password,
        )
    finally:
        db.close()


def test_change_password_without_token():
    response = client.post(
        "/change-password",
        json={
            "current_password": "SecurePass123",
            "new_password": "NewSecurePass456",
            "confirm_new_password": "NewSecurePass456",
        },
    )

    assert response.status_code == 401


def test_change_password_with_invalid_token():
    response = client.post(
        "/change-password",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "current_password": "SecurePass123",
            "new_password": "NewSecurePass456",
            "confirm_new_password": "NewSecurePass456",
        },
    )

    assert response.status_code == 401


def test_change_password_incorrect_current_password():
    user = create_test_user()
    headers = get_auth_headers(user)

    response = change_password(
        headers,
        current_password="WrongPassword123",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Current password is incorrect."
    )


def test_change_password_mismatched_new_passwords():
    user = create_test_user()
    headers = get_auth_headers(user)

    response = change_password(
        headers,
        confirm_new_password="DifferentPassword456",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New passwords do not match."
    )


def test_change_password_same_as_current_password():
    user = create_test_user()
    headers = get_auth_headers(user)

    response = change_password(
        headers,
        new_password="SecurePass123",
        confirm_new_password="SecurePass123",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New password must be different from the current password."
    )


@pytest.mark.parametrize(
    "new_password",
    [
        "",
        "short",
        "1234567",
    ],
)
def test_change_password_rejects_short_passwords(new_password):
    user = create_test_user()
    headers = get_auth_headers(user)

    response = change_password(
        headers,
        new_password=new_password,
        confirm_new_password=new_password,
    )

    assert response.status_code == 422


def test_change_password_rejects_missing_fields():
    user = create_test_user()
    headers = get_auth_headers(user)

    response = client.post(
        "/change-password",
        headers=headers,
        json={
            "current_password": "SecurePass123",
        },
    )

    assert response.status_code == 422


def test_change_password_invalidates_reset_tokens():
    user = create_test_user()
    headers = get_auth_headers(user)

    db = TestingSessionLocal()
    try:
        reset_token = PasswordResetToken(
            user_id=user["id"],
            token_hash="a" * 64,
            expires_at=(
                __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ) + timedelta(minutes=30)
            ),
        )

        db.add(reset_token)
        db.commit()
        reset_token_id = reset_token.id
    finally:
        db.close()

    response = change_password(headers)

    assert response.status_code == 200

    db = TestingSessionLocal()
    try:
        stored_token = db.query(
            PasswordResetToken
        ).filter(
            PasswordResetToken.id == reset_token_id
        ).first()

        assert stored_token.used_at is not None
    finally:
        db.close()
