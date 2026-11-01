
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from security import verify_password
from user_model import User


class RegistrationTests(unittest.TestCase):

    def setUp(self):
        # Create a separate in-memory database for testing.
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

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.startup_patch.stop()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_successful_registration(self):
        response = self.client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["message"],
            "User registered successfully.",
        )
        self.assertEqual(
            response.json()["user"]["username"],
            "testuser",
        )

    def test_password_is_stored_as_hash(self):
        self.client.post(
            "/register",
            json={
                "username": "hashuser",
                "email": "hash@example.com",
                "password": "SecurePass123",
            },
        )

        db = self.TestingSessionLocal()
        try:
            user = db.query(User).filter(
                User.username == "hashuser"
            ).first()

            self.assertIsNotNone(user)
            self.assertNotEqual(
                user.hashed_password,
                "SecurePass123",
            )
            self.assertTrue(
                verify_password(
                    "SecurePass123",
                    user.hashed_password,
                )
            )
        finally:
            db.close()

    def test_response_does_not_expose_password_hash(self):
        response = self.client.post(
            "/register",
            json={
                "username": "safeuser",
                "email": "safe@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertNotIn(
            "hashed_password",
            response.json()["user"],
        )

    def test_duplicate_username_is_rejected(self):
        user_data = {
            "username": "duplicate",
            "email": "first@example.com",
            "password": "SecurePass123",
        }

        self.client.post("/register", json=user_data)

        duplicate_data = {
            "username": "duplicate",
            "email": "second@example.com",
            "password": "SecurePass123",
        }

        response = self.client.post(
            "/register",
            json=duplicate_data,
        )

        self.assertEqual(response.status_code, 409)

    def test_duplicate_email_is_rejected(self):
        user_data = {
            "username": "firstuser",
            "email": "duplicate@example.com",
            "password": "SecurePass123",
        }

        self.client.post("/register", json=user_data)

        duplicate_data = {
            "username": "seconduser",
            "email": "duplicate@example.com",
            "password": "SecurePass123",
        }

        response = self.client.post(
            "/register",
            json=duplicate_data,
        )

        self.assertEqual(response.status_code, 409)

    def test_short_password_is_rejected(self):
        response = self.client.post(
            "/register",
            json={
                "username": "shortpass",
                "email": "short@example.com",
                "password": "123",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_invalid_email_is_rejected(self):
        response = self.client.post(
            "/register",
            json={
                "username": "invalidemail",
                "email": "not-an-email",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
