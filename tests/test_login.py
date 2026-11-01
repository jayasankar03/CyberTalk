import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import decode_access_token
from database import Base, get_db
from main import app
from user_model import User


class LoginTests(unittest.TestCase):

    def setUp(self):
        # Configure a temporary JWT secret for testing.
        self.secret_patch = patch.dict(
            os.environ,
            {
                "CYBERTALK_SECRET_KEY":
                    "test-secret-key-for-cybertalk-authentication-123456"
            },
        )
        self.secret_patch.start()

        # Create a separate in-memory database.
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        self.TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        Base.metadata.create_all(bind=self.engine)

        # Override the application's database dependency.
        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        # Prevent tests from initializing the real database.
        self.startup_patch = patch("main.create_db_tables")
        self.startup_patch.start()

        self.client = TestClient(app)

        # Register a test user for login tests.
        registration_response = self.client.post(
            "/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(registration_response.status_code, 201)

        db = self.TestingSessionLocal()
        try:
            user = db.query(User).filter(
                User.username == "loginuser"
            ).first()

            self.user_id = user.id
        finally:
            db.close()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.startup_patch.stop()
        self.secret_patch.stop()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_successful_login_with_username(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "loginuser",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertEqual(response.json()["expires_in"], 1800)
        self.assertIn("access_token", response.json())

    def test_successful_login_with_email(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "login@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

    def test_access_token_contains_user_id(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "loginuser",
                "password": "SecurePass123",
            },
        )

        token = response.json()["access_token"]
        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], str(self.user_id))

    def test_incorrect_password_is_rejected(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "loginuser",
                "password": "WrongPassword123",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_unknown_user_is_rejected(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "unknownuser",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_login_input_is_rejected(self):
        response = self.client.post(
            "/login",
            json={
                "identifier": "ab",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()