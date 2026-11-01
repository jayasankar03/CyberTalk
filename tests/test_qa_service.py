
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

    async def test_missing_message_in_ollama_response_is_rejected(self):
        from qa_service import OllamaResponseError

        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "response"}
        mock_response.raise_for_status.return_value = None

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            with self.assertRaises(OllamaResponseError):
                await check_cybersecurity_relevance(
                    "How can I prevent phishing attacks?"
                )

    async def test_missing_content_in_ollama_response_is_rejected(self):
        from qa_service import OllamaResponseError

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {}}
        mock_response.raise_for_status.return_value = None

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            with self.assertRaises(OllamaResponseError):
                await check_cybersecurity_relevance(
                    "How can I prevent phishing attacks?"
                )

    async def test_empty_ollama_content_is_rejected(self):
        from qa_service import OllamaResponseError

        mock_response = self.mock_ollama_response("   ")

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            with self.assertRaises(OllamaResponseError):
                await check_cybersecurity_relevance(
                    "How can I prevent phishing attacks?"
                )

    async def test_non_dictionary_ollama_response_is_rejected(self):
        from qa_service import OllamaResponseError

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock()

            mock_response = MagicMock()
            mock_response.json.return_value = ["invalid response"]
            mock_response.raise_for_status.return_value = None
            client.post.return_value = mock_response

            with self.assertRaises(OllamaResponseError):
                await check_cybersecurity_relevance(
                    "How can I prevent phishing attacks?"
                )

    async def test_non_string_ollama_content_is_rejected(self):
        from qa_service import OllamaResponseError

        mock_response = self.mock_ollama_response(None)

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            with self.assertRaises(OllamaResponseError):
                await check_cybersecurity_relevance(
                    "How can I prevent phishing attacks?"
                )

    async def test_ollama_content_is_stripped(self):
        from qa_service import extract_ollama_content

        result = extract_ollama_content({
            "message": {"content": "  YES  "}
        })

        self.assertEqual(result, "YES")

    async def test_unclear_classification_is_treated_as_unrelated(self):
        mock_response = self.mock_ollama_response(
            "YES, this is probably related."
        )

        with patch("qa_service.httpx.AsyncClient") as client_class:
            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            result = await check_cybersecurity_relevance(
                "How can I protect my account?"
            )

        self.assertFalse(result)

    async def test_valid_cybersecurity_answer_is_returned(self):
        mock_response = self.mock_ollama_response(
            "Use MFA and a strong password to protect your account."
        )

        with patch(
            "qa_service.check_cybersecurity_relevance",
            new=AsyncMock(return_value=True),
        ), patch("qa_service.httpx.AsyncClient") as client_class:

            client = client_class.return_value.__aenter__.return_value
            client.post = AsyncMock(return_value=mock_response)

            result = await answer_cybersecurity_question(
                "How can I protect my account?"
            )

        self.assertEqual(
            result,
            "Use MFA and a strong password to protect your account."
        )

if __name__ == "__main__":
    unittest.main()
