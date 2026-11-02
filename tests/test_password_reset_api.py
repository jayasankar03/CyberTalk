
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from password_reset_model import PasswordResetToken
from security import hash_reset_token
from user_model import User


class PasswordResetAPITests(unittest.TestCase):

    def setUp(self):
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

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        self.startup_patch = patch("main.create_db_tables")
        self.startup_patch.start()
        self.email_sender_patch = patch(
            "main.send_password_reset_email"
        )
        self.email_sender_mock = self.email_sender_patch.start()
        self.client = TestClient(app)

        # Create a test user.
        registration_response = self.client.post(
            "/register",
            json={
                "username": "resetuser",
                "email": "reset@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertEqual(registration_response.status_code, 201)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.email_sender_patch.stop()
        self.startup_patch.stop()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_password_reset_request_creates_token(self):
        raw_token = "test_secure_reset_token"

        with patch(
            "main.generate_password_reset_token",
            return_value=raw_token,
        ):
            response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        self.assertEqual(response.status_code, 200)

        db = self.TestingSessionLocal()
        try:
            token_record = db.query(
                PasswordResetToken
            ).first()

            self.assertIsNotNone(token_record)
            self.assertEqual(
                token_record.token_hash,
                hash_reset_token(raw_token),
            )
        finally:
            db.close()

    def test_original_token_is_not_stored(self):
        raw_token = "another_secure_reset_token"

        with patch(
            "main.generate_password_reset_token",
            return_value=raw_token,
        ):
            self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        db = self.TestingSessionLocal()
        try:
            token_record = db.query(
                PasswordResetToken
            ).first()

            self.assertNotEqual(
                token_record.token_hash,
                raw_token,
            )

            self.assertEqual(
                len(token_record.token_hash),
                64,
            )
        finally:
            db.close()

    def test_reset_token_expires_after_30_minutes(self):
        with patch(
            "main.generate_password_reset_token",
            return_value="expiration_test_token",
        ):
            response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        self.assertEqual(response.status_code, 200)

        db = self.TestingSessionLocal()
        try:
            token_record = db.query(
                PasswordResetToken
            ).first()

            expires_at = token_record.expires_at

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            remaining_time = (
                expires_at - datetime.now(timezone.utc)
            )

            self.assertGreater(
                remaining_time.total_seconds(),
                29 * 60,
            )

            self.assertLessEqual(
                remaining_time.total_seconds(),
                30 * 60,
            )
        finally:
            db.close()

    def test_unknown_email_returns_generic_response(self):
        response = self.client.post(
            "/password-reset/request",
            json={"email": "unknown@example.com"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "message": (
                    "If an account exists with this email, "
                    "password reset instructions will be sent."
                )
            },
        )

        db = self.TestingSessionLocal()
        try:
            token_count = db.query(
                PasswordResetToken
            ).count()

            self.assertEqual(token_count, 0)
        finally:
            db.close()

    def test_existing_and_unknown_emails_have_same_response(self):
        existing_response = self.client.post(
            "/password-reset/request",
            json={"email": "reset@example.com"},
        )

        unknown_response = self.client.post(
            "/password-reset/request",
            json={"email": "unknown@example.com"},
        )

        self.assertEqual(
            existing_response.json(),
            unknown_response.json(),
        )

    def test_reset_token_is_not_returned_in_response(self):
        raw_token = "private_reset_token"

        with patch(
            "main.generate_password_reset_token",
            return_value=raw_token,
        ):
            response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(raw_token, response.text)

    def test_multiple_requests_generate_unique_tokens(self):
        with patch(
            "main.generate_password_reset_token",
            side_effect=[
                "first_unique_reset_token",
                "second_unique_reset_token",
            ],
        ):
            first_response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

            second_response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        db = self.TestingSessionLocal()
        try:
            tokens = db.query(
                PasswordResetToken
            ).all()

            self.assertEqual(len(tokens), 2)

            self.assertNotEqual(
                tokens[0].token_hash,
                tokens[1].token_hash,
            )
        finally:
            db.close()
    def test_password_reset_email_is_sent_with_original_token(self):
        raw_token = "email_delivery_test_token"

        with patch(
            "main.generate_password_reset_token",
            return_value=raw_token,
        ):
            response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        self.assertEqual(response.status_code, 200)

        self.email_sender_mock.assert_called_once_with(
            recipient_email="reset@example.com",
            reset_token=raw_token,
        )

        self.assertNotIn(raw_token, response.text)

    def test_email_delivery_failure_keeps_generic_response(self):
        self.email_sender_mock.side_effect = RuntimeError(
            "SMTP connection failed"
        )

        response = self.client.post(
            "/password-reset/request",
            json={"email": "reset@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": (
                    "If an account exists with this email, "
                    "password reset instructions will be sent."
                )
            },
        )
    def test_invalid_email_is_rejected(self):
        response = self.client.post(
            "/password-reset/request",
            json={"email": "invalid-email"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
