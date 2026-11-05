import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["CYBERTALK_SECRET_KEY"] = (
    "cybertalk-test-secret-key-for-admin-tests"
)

from main import app
from auth import create_access_token
from database import get_db, Base
from user_model import User


# Create an isolated in-memory test database.
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


def create_test_user(
    username="testuser",
    email="test@example.com",
):
    response = client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201

    return response.json()["user"]


def create_token(user_id, role="user"):
    return create_access_token(
        data={
            "sub": str(user_id),
            "role": role,
        }
    )


def promote_to_admin(user_id):
    db = TestingSessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        user.role = "admin"
        db.commit()

    finally:
        db.close()


def test_admin_can_list_all_users():
    admin = create_test_user(
        "adminuser",
        "admin@example.com",
    )

    normal_user = create_test_user(
        "normaluser",
        "normal@example.com",
    )

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.get(
        "/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    users = response.json()

    assert len(users) == 2
    assert users[0]["username"] == "adminuser"
    assert users[0]["role"] == "admin"
    assert users[1]["username"] == "normaluser"
    assert users[1]["role"] == "user"

    for user in users:
        assert "hashed_password" not in user
        assert "password" not in user


def test_normal_user_cannot_list_users():
    user = create_test_user()

    token = create_token(user["id"])

    response = client.get(
        "/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Administrator privileges are required."
    )


def test_admin_endpoint_rejects_missing_token():
    response = client.get("/admin/users")

    assert response.status_code == 401


def test_admin_role_is_verified_from_database():
    user = create_test_user()

    # The token claims admin privileges, but the database says user.
    token = create_token(
        user["id"],
        role="admin",
    )

    response = client.get(
        "/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_database_admin_does_not_depend_on_token_role():
    user = create_test_user()

    promote_to_admin(user["id"])

    # The token says user, but the database says admin.
    token = create_token(
        user["id"],
        role="user",
    )

    response = client.get(
        "/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["role"] == "admin"

def test_admin_can_search_users_by_username():
    admin = create_test_user("adminuser", "admin@example.com")
    create_test_user("johnsmith", "john@example.com")
    create_test_user("alice", "alice@example.com")

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.get(
        "/admin/users?search=john",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    users = response.json()

    assert len(users) == 1
    assert users[0]["username"] == "johnsmith"


def test_admin_can_search_users_by_email():
    admin = create_test_user("adminuser", "admin@example.com")
    create_test_user("johnsmith", "john@company.com")

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.get(
        "/admin/users?search=company.com",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "john@company.com"


def test_admin_can_view_individual_user():
    admin = create_test_user("adminuser", "admin@example.com")
    target = create_test_user("targetuser", "target@example.com")

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.get(
        f"/admin/users/{target['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "targetuser"
    assert "hashed_password" not in response.json()


def test_admin_user_details_not_found():
    admin = create_test_user()
    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.get(
        "/admin/users/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_admin_can_promote_user():
    admin = create_test_user("adminuser", "admin@example.com")
    target = create_test_user("targetuser", "target@example.com")

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.patch(
        f"/admin/users/{target['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_admin_can_demote_another_admin():
    admin = create_test_user("adminuser", "admin@example.com")
    target = create_test_user("targetuser", "target@example.com")

    promote_to_admin(admin["id"])
    promote_to_admin(target["id"])

    token = create_token(admin["id"])

    response = client.patch(
        f"/admin/users/{target['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "user"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"


def test_admin_cannot_change_own_role():
    admin = create_test_user()
    second_admin = create_test_user(
        "secondadmin",
        "second@example.com",
    )

    promote_to_admin(admin["id"])
    promote_to_admin(second_admin["id"])

    token = create_token(admin["id"])

    response = client.patch(
        f"/admin/users/{admin['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "user"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Administrators cannot change their own role."
    )


def test_last_admin_cannot_be_demoted():
    admin = create_test_user()
    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.patch(
        f"/admin/users/{admin['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "user"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "The last administrator cannot be demoted."
    )


def test_normal_user_cannot_change_roles():
    user = create_test_user()
    target = create_test_user(
        "targetuser",
        "target@example.com",
    )

    token = create_token(user["id"])

    response = client.patch(
        f"/admin/users/{target['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 403


def test_invalid_admin_role_is_rejected():
    admin = create_test_user()
    target = create_test_user(
        "targetuser",
        "target@example.com",
    )

    promote_to_admin(admin["id"])

    token = create_token(admin["id"])

    response = client.patch(
        f"/admin/users/{target['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "superadmin"},
    )

    assert response.status_code == 422
