
import unittest
from unittest.mock import AsyncMock, patch
from urllib import response

import httpx

from fastapi.testclient import TestClient

from ai_api_test_helpers import configure_test_auth
from main import app

from qa_service import OllamaResponseError
client = TestClient(app)


class CybersecurityQAAPITests(unittest.TestCase):
    def setUp(self):
        configure_test_auth(client)

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
    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_malformed_ollama_response_returns_502(self, mock_answer):
        mock_answer.side_effect = OllamaResponseError(
            "Ollama returned an invalid response."
        )

        response = client.post(
            "/ask",
            json={"question": "How can I prevent phishing attacks?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The AI service returned an invalid response. Please try again.",
        )
    def test_empty_question_is_rejected(self):
        response = client.post(
            "/ask",
            json={"question": "   "},
        )

        self.assertEqual(response.status_code, 422)

    def test_missing_question_is_rejected(self):
        response = client.post("/ask", json={})

        self.assertEqual(response.status_code, 422)

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_ollama_connection_error_returns_502(self, mock_answer):
        mock_answer.side_effect = httpx.ConnectError(
            "Unable to connect to Ollama."
        )

        response = client.post(
            "/ask",
            json={"question": "How can I prevent phishing attacks?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The AI service is temporarily unavailable. Please try again.",
        )
        self.assertNotIn(
            "ConnectError",
            response.json()["detail"],
        )

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_ollama_timeout_returns_502(self, mock_answer):
        mock_answer.side_effect = httpx.ReadTimeout(
            "Ollama request timed out."
        )

        response = client.post(
            "/ask",
            json={"question": "How can I protect my network?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The AI service is temporarily unavailable. Please try again.",
        )
        self.assertNotIn(
            "ReadTimeout",
            response.json()["detail"],
        )

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_unexpected_service_error_returns_500(self, mock_answer):
        mock_answer.side_effect = RuntimeError(
            "Unexpected internal error."
        )

        response = client.post(
            "/ask",
            json={"question": "How can I improve password security?"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "An unexpected error occurred in the QA service.",
        )
    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_empty_answer_returns_502(self, mock_answer):
        mock_answer.return_value = "   "

        response = client.post(
            "/ask",
            json={"question": "How can I prevent malware?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The AI service returned an invalid response. Please try again.",
        )

if __name__ == "__main__":
    unittest.main()
