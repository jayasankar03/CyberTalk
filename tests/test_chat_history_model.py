
import unittest

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from user_model import User
from chat_history_model import ChatHistory


class ChatHistoryModelTests(unittest.TestCase):

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

    def create_test_user(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="test_hashed_password"
        )

        self.session.add(user)
        self.session.commit()

        return user

    def test_create_chat_history(self):
        user = self.create_test_user()

        history = ChatHistory(
            user_id=user.id,
            conversation_type="qa",
            title="What is phishing?",
            content='{"question": "What is phishing?"}'
        )

        self.session.add(history)
        self.session.commit()

        self.assertIsNotNone(history.id)
        self.assertEqual(history.user_id, user.id)
        self.assertEqual(history.conversation_type, "qa")
        self.assertEqual(history.title, "What is phishing?")
        self.assertEqual(
            history.content,
            '{"question": "What is phishing?"}'
        )
        self.assertIsNotNone(history.created_at)

    def test_user_can_have_multiple_history_records(self):
        user = self.create_test_user()

        history1 = ChatHistory(
            user_id=user.id,
            conversation_type="qa",
            title="Phishing",
            content='{"topic": "Phishing"}'
        )

        history2 = ChatHistory(
            user_id=user.id,
            conversation_type="dialogue",
            title="Network Security",
            content='{"topic": "Network Security"}'
        )

        self.session.add_all([history1, history2])
        self.session.commit()

        records = (
            self.session.query(ChatHistory)
            .filter(ChatHistory.user_id == user.id)
            .all()
        )

        self.assertEqual(len(records), 2)

    def test_user_id_is_required(self):
        history = ChatHistory(
            user_id=None,
            conversation_type="qa",
            title="Test",
            content="Test content"
        )

        self.session.add(history)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_conversation_type_is_required(self):
        user = self.create_test_user()

        history = ChatHistory(
            user_id=user.id,
            conversation_type=None,
            title="Test",
            content="Test content"
        )

        self.session.add(history)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_title_is_required(self):
        user = self.create_test_user()

        history = ChatHistory(
            user_id=user.id,
            conversation_type="qa",
            title=None,
            content="Test content"
        )

        self.session.add(history)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_content_is_required(self):
        user = self.create_test_user()

        history = ChatHistory(
            user_id=user.id,
            conversation_type="qa",
            title="Test",
            content=None
        )

        self.session.add(history)

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()


if __name__ == "__main__":
    unittest.main()
