
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
from security import (
    hash_reset_token,
    verify_password,
)
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
        first_token = "first_unique_reset_token"
        second_token = "second_unique_reset_token"

        with patch(
            "main.generate_password_reset_token",
            side_effect=[first_token, second_token],
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
            tokens = db.query(PasswordResetToken).all()

            self.assertEqual(len(tokens), 2)

            first_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash
                == hash_reset_token(first_token)
            ).first()

            second_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash
                == hash_reset_token(second_token)
            ).first()

            self.assertIsNotNone(first_record)
            self.assertIsNotNone(second_record)

            self.assertNotEqual(
                first_record.token_hash,
                second_record.token_hash,
            )

            # The previous token must be invalidated.
            self.assertIsNotNone(first_record.used_at)

            # The newest token must remain active.
            self.assertIsNone(second_record.used_at)

        finally:
            db.close()

        # The previous token must no longer work.
        first_confirm_response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": first_token,
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(first_confirm_response.status_code, 400)

        # The newest token must still work.
        second_confirm_response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": second_token,
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(second_confirm_response.status_code, 200)

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
        raw_token = "email_failure_reset_token_123"

        self.email_sender_mock.side_effect = RuntimeError(
            "SMTP connection failed"
        )

        with patch(
            "main.generate_password_reset_token",
            return_value=raw_token,
        ):
            response = self.client.post(
                "/password-reset/request",
                json={"email": "reset@example.com"},
            )

        # The response must remain generic.
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

        # Verify that the failed-delivery token is invalidated.
        db = self.TestingSessionLocal()
        try:
            token_record = db.query(
                PasswordResetToken
            ).filter(
                PasswordResetToken.token_hash
                == hash_reset_token(raw_token)
            ).first()

            self.assertIsNotNone(token_record)
            self.assertIsNotNone(token_record.used_at)

        finally:
            db.close()

        # The undelivered token must not be usable.
        confirm_response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": raw_token,
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(confirm_response.status_code, 400)

    def test_invalid_email_is_rejected(self):
        response = self.client.post(
            "/password-reset/request",
            json={"email": "invalid-email"},
        )

        self.assertEqual(response.status_code, 422)


    def create_reset_token(self, raw_token, expires_in_minutes=30):
        """Create a reset token directly in the test database."""
        db = self.TestingSessionLocal()
        try:
            user = db.query(User).filter(
                User.email == "reset@example.com"
            ).first()

            token_record = PasswordResetToken(
                user_id=user.id,
                token_hash=hash_reset_token(raw_token),
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(minutes=expires_in_minutes)
                ),
            )

            db.add(token_record)
            db.commit()
        finally:
            db.close()

    def test_password_reset_confirmation_updates_password(self):
        raw_token = "valid_password_reset_token_123"
        new_password = "NewSecurePass456"

        self.create_reset_token(raw_token)

        response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": raw_token,
                "new_password": new_password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Password has been reset successfully.",
        )

        db = self.TestingSessionLocal()
        try:
            user = db.query(User).filter(
                User.email == "reset@example.com"
            ).first()

            self.assertTrue(
                verify_password(
                    new_password,
                    user.hashed_password,
                )
            )
            self.assertFalse(
                verify_password(
                    "SecurePass123",
                    user.hashed_password,
                )
            )
        finally:
            db.close()

    def test_password_reset_confirmation_rejects_invalid_token(self):
        response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": "invalid_password_reset_token_123",
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_password_reset_confirmation_rejects_expired_token(self):
        raw_token = "expired_password_reset_token_123"
        self.create_reset_token(raw_token, expires_in_minutes=-1)

        response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": raw_token,
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_password_reset_confirmation_rejects_token_reuse(self):
        raw_token = "single_use_password_reset_token_123"
        self.create_reset_token(raw_token)

        payload = {
            "token": raw_token,
            "new_password": "NewSecurePass456",
        }

        first_response = self.client.post(
            "/password-reset/confirm",
            json=payload,
        )

        second_response = self.client.post(
            "/password-reset/confirm",
            json=payload,
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 400)

    def test_password_reset_invalidates_other_outstanding_tokens(self):
        first_token = "first_outstanding_reset_token_123"
        second_token = "second_outstanding_reset_token_123"

        self.create_reset_token(first_token)
        self.create_reset_token(second_token)

        response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": first_token,
                "new_password": "NewSecurePass456",
            },
        )

        self.assertEqual(response.status_code, 200)

        second_response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": second_token,
                "new_password": "AnotherSecurePass789",
            },
        )

        self.assertEqual(second_response.status_code, 400)

    def test_password_reset_confirmation_rejects_short_password(self):
        raw_token = "short_password_test_reset_token_123"
        self.create_reset_token(raw_token)

        response = self.client.post(
            "/password-reset/confirm",
            json={
                "token": raw_token,
                "new_password": "short",
            },
        )

        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
