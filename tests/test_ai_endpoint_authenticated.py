
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from ai_api_test_helpers import configure_test_auth
from main import app


class AIEndpointAuthenticatedTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        configure_test_auth(self.client)

    @patch("main.answer_cybersecurity_question", new_callable=AsyncMock)
    def test_ask_accepts_authenticated_user(self, mock_answer):
        mock_answer.return_value = (
            "Use multi-factor authentication to protect accounts."
        )

        response = self.client.post(
            "/ask",
            json={
                "question": "How can I prevent phishing attacks?"
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["question"],
            "How can I prevent phishing attacks?",
        )
        self.assertEqual(
            response.json()["answer"],
            "Use multi-factor authentication to protect accounts.",
        )
        mock_answer.assert_awaited_once()

    @patch("main.generate_persona_response", new_callable=AsyncMock)
    def test_chat_accepts_authenticated_user(self, mock_generate):
        mock_generate.return_value = (
            "Use firewalls, network segmentation, and MFA."
        )

        response = self.client.post(
            "/chat",
            json={
                "message": "How can I protect my network?"
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["reply"],
            "Use firewalls, network segmentation, and MFA.",
        )
        mock_generate.assert_awaited_once()

    @patch("main.evaluate_agreement", new_callable=AsyncMock)
    @patch("main.generate_persona_response", new_callable=AsyncMock)
    def test_dialogue_accepts_authenticated_user(
        self,
        mock_generate,
        mock_evaluate,
    ):
        mock_generate.return_value = (
            "Implement strong access controls and continuous monitoring."
        )

        mock_evaluate.return_value = SimpleNamespace(
            model_dump=lambda: {
                "status": "agreement_reached",
                "explanation": "Both stakeholders agree.",
                "shared_decision": "Implement stronger access controls.",
                "unresolved_disagreements": [],
                "next_actions": ["Deploy MFA."],
            }
        )

        response = self.client.post(
            "/dialogue",
            json={
                "topic": "How should we improve cloud security?",
                "stakeholder_1": "Security Architect",
                "stakeholder_2": "Cloud Engineer",
                "rounds": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(
            result["topic"],
            "How should we improve cloud security?",
        )
        self.assertEqual(result["rounds"], 1)
        self.assertEqual(len(result["dialogue"]), 4)
        self.assertEqual(
            result["agreement"]["status"],
            "agreement_reached",
        )

        self.assertEqual(mock_generate.await_count, 4)
        mock_evaluate.assert_awaited_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
