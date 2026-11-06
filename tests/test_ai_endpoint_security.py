
import unittest
from fastapi.testclient import TestClient

from ai_api_test_helpers import (
    create_unauthenticated_client,
    configure_test_auth,
)

from main import app


class AIEndpointSecurityTests(unittest.TestCase):

    def setUp(self):
        self.client = create_unauthenticated_client()

    def test_ask_rejects_missing_token(self):
        response = self.client.post(
            "/ask",
            json={"question": "How can I prevent phishing?"},
        )
        self.assertEqual(response.status_code, 401)

    def test_chat_rejects_missing_token(self):
        response = self.client.post(
            "/chat",
            json={"message": "How can I protect my network?"},
        )
        self.assertEqual(response.status_code, 401)

    def test_dialogue_rejects_missing_token(self):
        response = self.client.post(
            "/dialogue",
            json={
                "topic": "How should we improve cloud security?",
                "stakeholder_1": "Security Architect",
                "stakeholder_2": "Cloud Engineer",
                "rounds": 1,
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_ask_rejects_invalid_token(self):
        response = self.client.post(
            "/ask",
            headers={"Authorization": "Bearer invalid.token.value"},
            json={"question": "How can I prevent phishing?"},
        )
        self.assertEqual(response.status_code, 401)

    def test_chat_rejects_invalid_token(self):
        response = self.client.post(
            "/chat",
            headers={"Authorization": "Bearer invalid.token.value"},
            json={"message": "How can I protect my network?"},
        )
        self.assertEqual(response.status_code, 401)

    def test_dialogue_rejects_invalid_token(self):
        response = self.client.post(
            "/dialogue",
            headers={"Authorization": "Bearer invalid.token.value"},
            json={
                "topic": "How should we improve cloud security?",
                "stakeholder_1": "Security Architect",
                "stakeholder_2": "Cloud Engineer",
                "rounds": 1,
            },
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
