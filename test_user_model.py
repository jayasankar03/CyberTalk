
import unittest

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from user_model import User


class UserModelTests(unittest.TestCase):

    def setUp(self):
        # Use an isolated in-memory database for testing
        self.engine = create_engine("sqlite:///:memory:")

        TestingSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.session = TestingSession()

        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_create_user(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="test_hashed_password"
        )

        self.session.add(user)
        self.session.commit()

        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, "user")
        self.assertIsNotNone(user.created_at)

    def test_username_must_be_unique(self):
        user1 = User(
            username="duplicate",
            email="first@example.com",
            hashed_password="hash1"
        )

        self.session.add(user1)
        self.session.commit()

        user2 = User(
            username="duplicate",
            email="second@example.com",
            hashed_password="hash2"
        )

        self.session.add(user2)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_email_must_be_unique(self):
        user1 = User(
            username="first",
            email="duplicate@example.com",
            hashed_password="hash1"
        )

        self.session.add(user1)
        self.session.commit()

        user2 = User(
            username="second",
            email="duplicate@example.com",
            hashed_password="hash2"
        )

        self.session.add(user2)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_required_fields(self):
        user = User(
            username=None,
            email="missing@example.com",
            hashed_password="test_hash"
        )

        self.session.add(user)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()


if __name__ == "__main__":
    unittest.main()
