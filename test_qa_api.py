
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class CybersecurityQAAPITests(unittest.TestCase):

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_cybersecurity_question_returns_answer(self, mock_answer):
        mock_answer.return_value = (
            "Use multi-factor authentication to strengthen account security."
        )

        response = client.post(
            "/ask",
            json={
                "question": "How can I secure my online accounts?"
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Use multi-factor authentication to strengthen account security.",
        )
        self.assertEqual(
            response.json()["question"],
            "How can I secure my online accounts?",
        )
        mock_answer.assert_awaited_once_with(
            "How can I secure my online accounts?"
        )

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_unrelated_question_returns_polite_message(self, mock_answer):
        mock_answer.return_value = (
            "This question does not appear to be related to cybersecurity. "
            "Please ask a cybersecurity-related question."
        )

        response = client.post(
            "/ask",
            json={"question": "What is the capital of France?"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("cybersecurity", response.json()["answer"].lower())

    def test_empty_question_is_rejected(self):
        response = client.post(
            "/ask",
            json={"question": "   "},
        )

        self.assertEqual(response.status_code, 422)

    def test_missing_question_is_rejected(self):
        response = client.post("/ask", json={})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
