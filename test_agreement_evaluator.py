
import asyncio
import json
import unittest
from unittest.mock import patch

from agreement import AgreementResult
from agreement_evaluator import (
    AgreementEvaluationError,
    evaluate_agreement,
)


TOPIC = "Implement multi-factor authentication for remote access."


def make_transcript(security_message, operations_message):
    return [
        {
            "turn": 1,
            "speaker": "Security Officer",
            "message": security_message,
        },
        {
            "turn": 1,
            "speaker": "IT Operations Manager",
            "message": operations_message,
        },
    ]


class FakeResponse:
    """Simulate a response from Ollama."""

    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "message": {
                "content": self.content,
            }
        }


class FakeAsyncClient:
    """Simulate Ollama without network access."""

    content = ""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def post(self, *args, **kwargs):
        return FakeResponse(self.content)


class AgreementEvaluatorTests(unittest.TestCase):

    def evaluate_with_response(self, expected_result, transcript):
        FakeAsyncClient.content = json.dumps(expected_result)

        with patch(
            "agreement_evaluator.httpx.AsyncClient",
            FakeAsyncClient,
        ):
            return asyncio.run(
                evaluate_agreement(TOPIC, transcript)
            )

    def test_agreement_reached(self):
        expected = {
            "status": "agreement_reached",
            "explanation": "Both stakeholders accept a phased MFA rollout.",
            "shared_decision": (
                "Pilot MFA and complete the rollout within two weeks."
            ),
            "unresolved_disagreements": [],
            "next_actions": [
                "Start the MFA pilot.",
                "Complete rollout within two weeks.",
            ],
        }

        transcript = make_transcript(
            "I agree to a pilot and rollout within two weeks.",
            "Agreed. We will complete the rollout within two weeks.",
        )

        result = self.evaluate_with_response(expected, transcript)

        self.assertIsInstance(result, AgreementResult)
        self.assertEqual(result.status, "agreement_reached")
        self.assertIsNotNone(result.shared_decision)
        self.assertEqual(result.unresolved_disagreements, [])

    def test_partial_agreement(self):
        expected = {
            "status": "partial_agreement",
            "explanation": (
                "Both support MFA, but the rollout deadline remains disputed."
            ),
            "shared_decision": "Introduce MFA for remote access.",
            "unresolved_disagreements": [
                "The rollout deadline remains disputed."
            ],
            "next_actions": [
                "Agree on a realistic rollout deadline."
            ],
        }

        transcript = make_transcript(
            "MFA is necessary, and I require completion within one week.",
            "I support MFA, but I cannot commit to a one-week deadline.",
        )

        result = self.evaluate_with_response(expected, transcript)

        self.assertEqual(result.status, "partial_agreement")
        self.assertTrue(result.unresolved_disagreements)
        self.assertTrue(result.next_actions)

    def test_no_agreement(self):
        expected = {
            "status": "no_agreement",
            "explanation": (
                "The stakeholders have not accepted a common plan."
            ),
            "shared_decision": None,
            "unresolved_disagreements": [
                "They disagree on whether to implement MFA now."
            ],
            "next_actions": [
                "Discuss risks and alternative rollout options."
            ],
        }

        transcript = make_transcript(
            "MFA must be implemented immediately.",
            "I oppose the proposal and do not accept the plan.",
        )

        result = self.evaluate_with_response(expected, transcript)

        self.assertEqual(result.status, "no_agreement")
        self.assertIsNone(result.shared_decision)
        self.assertTrue(result.unresolved_disagreements)

    def test_empty_transcript_is_rejected(self):
        with self.assertRaises(ValueError):
            asyncio.run(evaluate_agreement(TOPIC, []))

    def test_invalid_status_is_rejected(self):
        expected = {
            "status": "unknown",
            "explanation": "Invalid status test.",
            "shared_decision": None,
            "unresolved_disagreements": [],
            "next_actions": [],
        }

        transcript = make_transcript(
            "We should implement MFA.",
            "We need to discuss the proposal.",
        )

        with self.assertRaises(ValueError):
            self.evaluate_with_response(expected, transcript)

    def test_malformed_ollama_response_is_rejected(self):
        FakeAsyncClient.content = "This is not valid JSON"

        with patch(
            "agreement_evaluator.httpx.AsyncClient",
            FakeAsyncClient,
        ):
            with self.assertRaises(AgreementEvaluationError):
                asyncio.run(
                    evaluate_agreement(
                        TOPIC,
                        make_transcript(
                            "We should implement MFA.",
                            "We need to discuss the proposal.",
                        ),
                    )
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
