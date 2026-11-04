import os
import hashlib
from datetime import datetime, timedelta, timezone

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
from database import Base, get_db
from share_link_model import ShareLink


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


def create_test_user(username="shareuser"):
    response = client.post(
        "/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201

    return response.json()["user"]


def create_token(user_id):
    return create_access_token(
        data={
            "sub": str(user_id),
            "role": "user",
        }
    )


def auth_headers(user_id):
    return {
        "Authorization": f"Bearer {create_token(user_id)}"
    }


def save_test_conversation(user_id):
    return client.post(
        "/history",
        headers=auth_headers(user_id),
        json={
            "conversation_type": "qa",
            "title": "Phishing Awareness",
            "content": '{"question": "What is phishing?"}',
        },
    )


def create_test_share(user_id, history_id, expires_in_days=None):
    payload = {}

    if expires_in_days is not None:
        payload["expires_in_days"] = expires_in_days

    return client.post(
        f"/history/{history_id}/share",
        headers=auth_headers(user_id),
        json=payload,
    )


def test_create_share_link_success():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = create_test_share(user["id"], history_id)

    assert response.status_code == 201

    data = response.json()

    assert data["share_id"] is not None
    assert data["share_url"].startswith("http://testserver/shared/")
    assert data["expires_at"] is None


def test_create_share_link_with_expiry():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = create_test_share(
        user["id"],
        history_id,
        expires_in_days=7,
    )

    assert response.status_code == 201
    assert response.json()["expires_at"] is not None


def test_create_share_link_rejects_invalid_expiry():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = create_test_share(
        user["id"],
        history_id,
        expires_in_days=500,
    )

    assert response.status_code == 422


def test_user_cannot_share_another_users_conversation():
    owner = create_test_user("shareowner")
    other_user = create_test_user("shareother")

    saved = save_test_conversation(owner["id"])
    history_id = saved.json()["id"]

    response = create_test_share(other_user["id"], history_id)

    assert response.status_code == 404


def test_create_share_link_without_authentication():
    response = client.post(
        "/history/1/share",
        json={},
    )

    assert response.status_code == 401


def test_public_shared_conversation_access():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    created = create_test_share(user["id"], history_id)
    share_url = created.json()["share_url"]

    response = client.get(share_url.replace("http://testserver", ""))

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Phishing Awareness"
    assert data["conversation_type"] == "qa"
    assert "phishing" in data["content"]

    assert "user_id" not in data
    assert "username" not in data
    assert "email" not in data
    assert "hashed_password" not in data


def test_invalid_share_token_returns_404():
    response = client.get("/shared/invalid-token")

    assert response.status_code == 404


def test_expired_share_link_returns_404():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    created = create_test_share(user["id"], history_id)
    share_url = created.json()["share_url"]

    token = share_url.rsplit("/", 1)[-1]
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    db = TestingSessionLocal()

    try:
        share = (
            db.query(ShareLink)
            .filter(ShareLink.token_hash == token_hash)
            .first()
        )

        share.expires_at = (
            datetime.now(timezone.utc) - timedelta(days=1)
        )

        db.commit()
    finally:
        db.close()

    response = client.get(
        share_url.replace("http://testserver", "")
    )

    assert response.status_code == 404
    assert "expired" in response.json()["detail"].lower()


def test_revoke_share_link_success():
    user = create_test_user()
    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    created = create_test_share(user["id"], history_id)
    data = created.json()

    revoke = client.delete(
        f"/history/{history_id}/share/{data['share_id']}",
        headers=auth_headers(user["id"]),
    )

    assert revoke.status_code == 200

    public_response = client.get(
        data["share_url"].replace("http://testserver", "")
    )

    assert public_response.status_code == 404


def test_user_cannot_revoke_another_users_share_link():
    owner = create_test_user("revokeowner")
    other_user = create_test_user("revokeother")

    saved = save_test_conversation(owner["id"])
    history_id = saved.json()["id"]

    created = create_test_share(owner["id"], history_id)
    share_id = created.json()["share_id"]

    response = client.delete(
        f"/history/{history_id}/share/{share_id}",
        headers=auth_headers(other_user["id"]),
    )

    assert response.status_code == 404


def test_revoke_share_link_without_authentication():
    response = client.delete(
        "/history/1/share/1"
    )

    assert response.status_code == 401