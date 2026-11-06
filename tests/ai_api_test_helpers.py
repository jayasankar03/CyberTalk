
import os

os.environ["CYBERTALK_SECRET_KEY"] = (
    "cybertalk-test-secret-key-for-ai-api-tests"
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from main import app
from auth import create_access_token
from database import Base, get_db
from user_model import User


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


def configure_test_auth(client):
    """Reset the test database and authenticate a registered user."""

    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post(
        "/register",
        json={
            "username": "ai_test_user",
            "email": "ai_test@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201, response.text

    user_id = response.json()["user"]["id"]

    db = TestingSessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
                "auth_version": user.auth_version,
            }
        )
    finally:
        db.close()

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return token

def create_unauthenticated_client():
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return TestClient(app)
