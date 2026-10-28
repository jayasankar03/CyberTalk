
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agreement import AgreementResult
from main import app


client = TestClient(app)


class DialogueRequestTests(unittest.TestCase):

    @patch("main.evaluate_agreement", new_callable=AsyncMock)
    @patch("main.generate_persona_response", new_callable=AsyncMock)
    def test_custom_stakeholders_are_accepted(
        self,
        mock_generate,
        mock_evaluate,
    ):
        mock_generate.side_effect = [
            "We should introduce phishing-resistant MFA.",
            "We can introduce it in phases.",
            "I agree to a phased rollout.",
            "I agree to the phased rollout.",
        ]

        mock_evaluate.return_value = AgreementResult(
            status="agreement_reached",
            explanation="Both stakeholders support a phased rollout.",
            shared_decision="Introduce phishing-resistant MFA in phases.",
            unresolved_disagreements=[],
            next_actions=["Plan the phased rollout."],
        )

        response = client.post(
            "/dialogue",
            json={
                "topic": "Should we require phishing-resistant MFA?",
                "stakeholder_1": "Chief Financial Officer",
                "stakeholder_2": "Cloud Infrastructure Engineer",
                "rounds": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()

        # Verify the custom stakeholder names are preserved.
        self.assertEqual(
            result["stakeholders"][0]["name"],
            "Chief Financial Officer",
        )
        self.assertEqual(
            result["stakeholders"][1]["name"],
            "Cloud Infrastructure Engineer",
        )

        # One regular round plus two closing statements.
        self.assertEqual(len(result["dialogue"]), 4)

        # Verify the stakeholders alternate in the expected order.
        self.assertEqual(
            [item["speaker"] for item in result["dialogue"]],
            [
                "Chief Financial Officer",
                "Cloud Infrastructure Engineer",
                "Chief Financial Officer",
                "Cloud Infrastructure Engineer",
            ],
        )

        # The closing statements use the next turn number.
        self.assertEqual(
            [item["turn"] for item in result["dialogue"]],
            [1, 1, 2, 2],
        )

        # Verify the generated messages match the mocked responses.
        self.assertEqual(
            [item["message"] for item in result["dialogue"]],
            [
                "We should introduce phishing-resistant MFA.",
                "We can introduce it in phases.",
                "I agree to a phased rollout.",
                "I agree to the phased rollout.",
            ],
        )

        # Verify only the final two generation calls are closing calls.
        generate_calls = mock_generate.await_args_list

        self.assertEqual(
            [
                call.kwargs.get("closing", False)
                for call in generate_calls
            ],
            [False, False, True, True],
        )

        # Verify agreement evaluation runs once on the completed dialogue.
        self.assertEqual(
            result["agreement"]["status"],
            "agreement_reached",
        )
        self.assertEqual(
            result["agreement"]["shared_decision"],
            "Introduce phishing-resistant MFA in phases.",
        )
        self.assertEqual(
            mock_generate.await_count,
            4,
        )
        mock_evaluate.assert_awaited_once()

        # Confirm the evaluator receives all four dialogue messages.
        evaluated_transcript = mock_evaluate.await_args.kwargs["transcript"]
        self.assertEqual(len(evaluated_transcript), 4)

    def test_identical_stakeholders_are_rejected(self):
        response = client.post(
            "/dialogue",
            json={
                "topic": "Should we require MFA?",
                "stakeholder_1": "Security Architect",
                "stakeholder_2": "security architect",
                "rounds": 1,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "Please provide two different stakeholders.",
        )

    def test_short_stakeholder_name_is_rejected(self):
        response = client.post(
            "/dialogue",
            json={
                "topic": "Should we require MFA?",
                "stakeholder_1": "A",
                "stakeholder_2": "Cloud Engineer",
                "rounds": 1,
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
