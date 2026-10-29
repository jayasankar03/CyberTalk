
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from qa_service import (
    OUT_OF_SCOPE_MESSAGE,
    answer_cybersecurity_question,
    check_cybersecurity_relevance,
)


class CybersecurityQAServiceTests(unittest.IsolatedAsyncioTestCase):

    def mock_ollama_response(self, content):
        """Create a mock response matching httpx response behavior."""
        response = MagicMock()
        response.json.return_value = {
            "message": {"content": content}
        }
        response.raise_for_status.return_value = None
        return response

    async def test_relevant_question_is_classified_yes(self):
        mock_response = self.mock_ollama_response("YES")

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            result = await check_cybersecurity_relevance(
                "How can I prevent phishing attacks?"
            )

        self.assertTrue(result)

    async def test_unrelated_question_is_classified_no(self):
        mock_response = self.mock_ollama_response("NO")

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            result = await check_cybersecurity_relevance(
                "What is the capital of France?"
            )

        self.assertFalse(result)

    async def test_unrelated_question_is_not_answered_by_llm(self):
        with patch(
            "qa_service.check_cybersecurity_relevance",
            new=AsyncMock(return_value=False),
        ), patch("qa_service.httpx.AsyncClient") as client_class:

            result = await answer_cybersecurity_question(
                "Tell me a joke."
            )

        self.assertEqual(result, OUT_OF_SCOPE_MESSAGE)
        client_class.assert_not_called()

    async def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            await answer_cybersecurity_question("   ")


if __name__ == "__main__":
    unittest.main()
