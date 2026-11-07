
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from user_model import User
from io import BytesIO

from PIL import Image

from main import PROFILE_PICTURE_DIR, MAX_PROFILE_PICTURE_SIZE

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

def create_test_image(image_format="JPEG"):
    """Create a small valid image for upload tests."""
    image_buffer = BytesIO()

    image = Image.new("RGB", (100, 100), color="blue")
    image.save(image_buffer, format=image_format)

    return image_buffer.getvalue()
def test_upload_profile_picture_success():
    user = create_test_user()
    token = get_profile_token(user)

    image_content = create_test_image()

    response = client.post(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": ("profile.jpg", image_content, "image/jpeg")
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Profile picture uploaded successfully."
    assert data["profile_picture"].endswith(".jpg")

    saved_file = PROFILE_PICTURE_DIR / data["profile_picture"]

    try:
        assert saved_file.is_file()
        assert saved_file.read_bytes() == image_content

        db = TestingSessionLocal()
        try:
            db_user = db.query(User).filter(
                User.id == user["id"]
            ).first()

            assert db_user.profile_picture == data["profile_picture"]
        finally:
            db.close()

    finally:
        saved_file.unlink(missing_ok=True)


def test_upload_profile_picture_without_token():
    image_content = create_test_image()

    response = client.post(
        "/users/me/profile-picture",
        files={
            "file": ("profile.jpg", image_content, "image/jpeg")
        },
    )

    assert response.status_code == 401


def test_upload_profile_picture_rejects_invalid_image():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.post(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": ("profile.jpg", b"this is not an image", "image/jpeg")
        },
    )

    assert response.status_code == 400


def test_upload_profile_picture_rejects_oversized_file():
    user = create_test_user()
    token = get_profile_token(user)

    oversized_content = b"x" * (MAX_PROFILE_PICTURE_SIZE + 1)

    response = client.post(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": ("profile.jpg", oversized_content, "image/jpeg")
        },
    )

    assert response.status_code == 413

def test_upload_profile_picture_replaces_previous_picture():
    user = create_test_user()
    token = get_profile_token(user)

    old_filename = "previous_test_picture.jpg"
    old_file = PROFILE_PICTURE_DIR / old_filename
    old_file.write_bytes(create_test_image())

    db = TestingSessionLocal()
    try:
        db_user = db.query(User).filter(
            User.id == user["id"]
        ).first()

        db_user.profile_picture = old_filename
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "new_profile.jpg",
                create_test_image(),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    new_filename = response.json()["profile_picture"]
    new_file = PROFILE_PICTURE_DIR / new_filename

    try:
        assert new_filename != old_filename
        assert new_file.is_file()
        assert not old_file.exists()

        db = TestingSessionLocal()
        try:
            db_user = db.query(User).filter(
                User.id == user["id"]
            ).first()

            assert db_user.profile_picture == new_filename
        finally:
            db.close()

    finally:
        new_file.unlink(missing_ok=True)
        old_file.unlink(missing_ok=True)
def test_get_my_profile_picture_success():
    user = create_test_user()
    token = get_profile_token(user)

    filename = "retrieval_test_picture.jpg"
    image_content = create_test_image()

    image_path = PROFILE_PICTURE_DIR / filename
    image_path.write_bytes(image_content)

    db = TestingSessionLocal()
    try:
        db_user = db.query(User).filter(
            User.id == user["id"]
        ).first()

        db_user.profile_picture = filename
        db.commit()
    finally:
        db.close()

    try:
        response = client.get(
            "/users/me/profile-picture",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.content == image_content
        assert response.headers["content-type"] == "image/jpeg"
        assert response.headers["cache-control"] == "private, no-store"

    finally:
        image_path.unlink(missing_ok=True)


def test_get_my_profile_picture_without_token():
    response = client.get("/users/me/profile-picture")

    assert response.status_code == 401


def test_get_my_profile_picture_when_none_exists():
    user = create_test_user()
    token = get_profile_token(user)

    response = client.get(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No profile picture has been uploaded."
    )


def test_get_my_profile_picture_when_file_is_missing():
    user = create_test_user()
    token = get_profile_token(user)

    db = TestingSessionLocal()
    try:
        db_user = db.query(User).filter(
            User.id == user["id"]
        ).first()

        db_user.profile_picture = "missing_picture.jpg"
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_get_my_profile_picture_rejects_unsafe_filename():
    user = create_test_user()
    token = get_profile_token(user)

    db = TestingSessionLocal()
    try:
        db_user = db.query(User).filter(
            User.id == user["id"]
        ).first()

        db_user.profile_picture = "../outside.jpg"
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
