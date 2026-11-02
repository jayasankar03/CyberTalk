
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from user_model import User
from password_reset_model import PasswordResetToken


class PasswordResetModelTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

        TestingSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        self.session = TestingSession()

        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def create_test_user(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="test_hashed_password",
        )

        self.session.add(user)
        self.session.commit()

        return user

    def create_test_token(self, user_id, token_hash="test_token_hash"):
        return PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

    def test_create_password_reset_token(self):
        user = self.create_test_user()
        token = self.create_test_token(user.id)

        self.session.add(token)
        self.session.commit()

        self.assertIsNotNone(token.id)
        self.assertEqual(token.user_id, user.id)
        self.assertEqual(token.token_hash, "test_token_hash")
        self.assertIsNotNone(token.expires_at)
        self.assertIsNone(token.used_at)
        self.assertIsNotNone(token.created_at)

    def test_token_user_id_is_required(self):
        token = self.create_test_token(None)

        self.session.add(token)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_token_hash_is_required(self):
        user = self.create_test_user()

        token = PasswordResetToken(
            user_id=user.id,
            token_hash=None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        self.session.add(token)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_token_hash_must_be_unique(self):
        user = self.create_test_user()

        token1 = self.create_test_token(user.id, "duplicate_hash")
        token2 = self.create_test_token(user.id, "duplicate_hash")

        self.session.add(token1)
        self.session.commit()

        self.session.add(token2)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_token_expiration_is_required(self):
        user = self.create_test_user()

        token = PasswordResetToken(
            user_id=user.id,
            token_hash="expiration_test_hash",
            expires_at=None,
        )

        self.session.add(token)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_token_can_be_marked_as_used(self):
        user = self.create_test_user()
        token = self.create_test_token(user.id)

        self.session.add(token)
        self.session.commit()

        used_time = datetime.now(timezone.utc)
        token.used_at = used_time
        self.session.commit()

        self.assertIsNotNone(token.used_at)


if __name__ == "__main__":
    unittest.main()
