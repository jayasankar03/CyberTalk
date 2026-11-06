
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from user_model import User

# Configure a test-only JWT secret.
os.environ["CYBERTALK_SECRET_KEY"] = (
    "cybertalk-test-secret-key-for-tests"
)

from main import app
from auth import create_access_token
from database import Base, get_db


# Create an isolated in-memory database.
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


def create_test_user(username="historyuser"):
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
    db = TestingSessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise ValueError("Test user not found.")

        return create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
                "auth_version": user.auth_version,
            }
        )
    finally:
        db.close()

def auth_headers(user_id):
    token = create_token(user_id)

    return {
        "Authorization": f"Bearer {token}"
    }


def save_test_conversation(user_id, title="Test conversation"):
    return client.post(
        "/history",
        headers=auth_headers(user_id),
        json={
            "conversation_type": "qa",
            "title": title,
            "content": '{"question": "What is phishing?"}',
        },
    )


def test_save_chat_history_success():
    user = create_test_user()

    response = save_test_conversation(user["id"])

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["conversation_type"] == "qa"
    assert data["title"] == "Test conversation"
    assert "phishing" in data["content"]
    assert "created_at" in data


def test_save_dialogue_history_success():
    user = create_test_user()

    response = client.post(
        "/history",
        headers=auth_headers(user["id"]),
        json={
            "conversation_type": "dialogue",
            "title": "Network Security Discussion",
            "content": '{"topic": "Network Security"}',
        },
    )

    assert response.status_code == 201
    assert response.json()["conversation_type"] == "dialogue"


def test_save_history_without_token():
    response = client.post(
        "/history",
        json={
            "conversation_type": "qa",
            "title": "Test",
            "content": "Test content",
        },
    )

    assert response.status_code == 401


def test_save_history_with_invalid_token():
    response = client.post(
        "/history",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "conversation_type": "qa",
            "title": "Test",
            "content": "Test content",
        },
    )

    assert response.status_code == 401


def test_save_history_with_invalid_conversation_type():
    user = create_test_user()

    response = client.post(
        "/history",
        headers=auth_headers(user["id"]),
        json={
            "conversation_type": "invalid",
            "title": "Test",
            "content": "Test content",
        },
    )

    assert response.status_code == 422


def test_save_history_with_empty_title():
    user = create_test_user()

    response = client.post(
        "/history",
        headers=auth_headers(user["id"]),
        json={
            "conversation_type": "qa",
            "title": "   ",
            "content": "Test content",
        },
    )

    assert response.status_code == 422


def test_get_chat_history_success():
    user = create_test_user()

    save_test_conversation(user["id"], "Phishing")
    save_test_conversation(user["id"], "Password Security")

    response = client.get(
        "/history",
        headers=auth_headers(user["id"]),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_users_can_only_see_their_own_history():
    user1 = create_test_user("historyuser1")
    user2 = create_test_user("historyuser2")

    save_test_conversation(user1["id"], "User One")
    save_test_conversation(user2["id"], "User Two")

    response = client.get(
        "/history",
        headers=auth_headers(user1["id"]),
    )

    assert response.status_code == 200

    records = response.json()

    assert len(records) == 1
    assert records[0]["title"] == "User One"


def test_get_single_chat_history_success():
    user = create_test_user()

    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = client.get(
        f"/history/{history_id}",
        headers=auth_headers(user["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == history_id


def test_user_cannot_access_another_users_history():
    user1 = create_test_user("historyuser1")
    user2 = create_test_user("historyuser2")

    saved = save_test_conversation(user1["id"])
    history_id = saved.json()["id"]

    response = client.get(
        f"/history/{history_id}",
        headers=auth_headers(user2["id"]),
    )

    assert response.status_code == 404


def test_get_nonexistent_history():
    user = create_test_user()

    response = client.get(
        "/history/99999",
        headers=auth_headers(user["id"]),
    )

    assert response.status_code == 404


def test_get_history_without_token():
    response = client.get("/history")

    assert response.status_code == 401


def test_delete_chat_history_success():
    user = create_test_user()

    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = client.delete(
        f"/history/{history_id}",
        headers=auth_headers(user["id"]),
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Conversation deleted successfully."
    )

    check = client.get(
        f"/history/{history_id}",
        headers=auth_headers(user["id"]),
    )

    assert check.status_code == 404


def test_user_cannot_delete_another_users_history():
    user1 = create_test_user("historyuser1")
    user2 = create_test_user("historyuser2")

    saved = save_test_conversation(user1["id"])
    history_id = saved.json()["id"]

    response = client.delete(
        f"/history/{history_id}",
        headers=auth_headers(user2["id"]),
    )

    assert response.status_code == 404

    # Verify the original owner's conversation still exists.
    check = client.get(
        f"/history/{history_id}",
        headers=auth_headers(user1["id"]),
    )

    assert check.status_code == 200


def test_delete_history_without_token():
    response = client.delete("/history/1")

    assert response.status_code == 401
def test_rename_chat_history_success():
    user = create_test_user()

    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = client.put(
        f"/history/{history_id}",
        headers=auth_headers(user["id"]),
        json={"title": "Updated Phishing Discussion"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == (
        "Updated Phishing Discussion"
    )

    # Verify that the conversation content remains unchanged.
    assert "phishing" in response.json()["content"]


def test_user_cannot_rename_another_users_history():
    user1 = create_test_user("historyuser1")
    user2 = create_test_user("historyuser2")

    saved = save_test_conversation(user1["id"])
    history_id = saved.json()["id"]

    response = client.put(
        f"/history/{history_id}",
        headers=auth_headers(user2["id"]),
        json={"title": "Unauthorized Rename"},
    )

    assert response.status_code == 404

    # Verify that the original title remains unchanged.
    check = client.get(
        f"/history/{history_id}",
        headers=auth_headers(user1["id"]),
    )

    assert check.status_code == 200
    assert check.json()["title"] == "Test conversation"


def test_rename_nonexistent_chat_history():
    user = create_test_user()

    response = client.put(
        "/history/99999",
        headers=auth_headers(user["id"]),
        json={"title": "New Title"},
    )

    assert response.status_code == 404


def test_rename_chat_history_with_empty_title():
    user = create_test_user()

    saved = save_test_conversation(user["id"])
    history_id = saved.json()["id"]

    response = client.put(
        f"/history/{history_id}",
        headers=auth_headers(user["id"]),
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_rename_chat_history_without_token():
    response = client.put(
        "/history/1",
        json={"title": "Unauthorized"},
    )

    assert response.status_code == 401
def test_delete_all_chat_history_success():
    user1 = create_test_user("bulkuser1")
    user2 = create_test_user("bulkuser2")

    # Create two conversations for user 1.
    save_test_conversation(user1["id"], "Conversation One")
    save_test_conversation(user1["id"], "Conversation Two")

    # Create one conversation for user 2.
    save_test_conversation(user2["id"], "Other User Conversation")

    response = client.delete(
        "/history",
        headers=auth_headers(user1["id"]),
    )

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 2

    # User 1 should have no remaining conversations.
    user1_history = client.get(
        "/history",
        headers=auth_headers(user1["id"]),
    )

    assert user1_history.status_code == 200
    assert user1_history.json() == []

    # User 2's conversation must remain untouched.
    user2_history = client.get(
        "/history",
        headers=auth_headers(user2["id"]),
    )

    assert user2_history.status_code == 200
    assert len(user2_history.json()) == 1
    assert user2_history.json()[0]["title"] == (
        "Other User Conversation"
    )


def test_delete_all_chat_history_when_empty():
    user = create_test_user("emptybulkuser")

    response = client.delete(
        "/history",
        headers=auth_headers(user["id"]),
    )

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 0


def test_delete_all_chat_history_without_token():
    response = client.delete("/history")

    assert response.status_code == 401


def test_delete_all_chat_history_preserves_other_users_data():
    user1 = create_test_user("bulkowner")
    user2 = create_test_user("bulkother")

    save_test_conversation(user1["id"], "Owner Conversation")
    save_test_conversation(user2["id"], "Protected Conversation")

    response = client.delete(
        "/history",
        headers=auth_headers(user1["id"]),
    )

    assert response.status_code == 200

    remaining = client.get(
        "/history",
        headers=auth_headers(user2["id"]),
    )

    assert len(remaining.json()) == 1
    assert remaining.json()[0]["title"] == "Protected Conversation"