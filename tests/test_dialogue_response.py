
import unittest

from main import (
    DialogueGenerationError,
    extract_dialogue_content,
)


class DialogueResponseTests(unittest.TestCase):

    def test_valid_response_returns_content(self):
        result = {
            "message": {
                "content": "Enable multi-factor authentication."
            }
        }

        content = extract_dialogue_content(result)

        self.assertEqual(
            content,
            "Enable multi-factor authentication."
        )

    def test_valid_response_trims_whitespace(self):
        result = {
            "message": {
                "content": "  We should improve security.  "
            }
        }

        content = extract_dialogue_content(result)

        self.assertEqual(
            content,
            "We should improve security."
        )

    def test_non_dictionary_response_is_rejected(self):
        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content("invalid response")

    def test_missing_message_is_rejected(self):
        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content({})

    def test_non_dictionary_message_is_rejected(self):
        result = {"message": "invalid"}

        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content(result)

    def test_missing_content_is_rejected(self):
        result = {"message": {}}

        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content(result)

    def test_empty_content_is_rejected(self):
        result = {"message": {"content": ""}}

        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content(result)

    def test_whitespace_content_is_rejected(self):
        result = {"message": {"content": "   "}}

        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content(result)

    def test_non_string_content_is_rejected(self):
        result = {"message": {"content": 123}}

        with self.assertRaises(DialogueGenerationError):
            extract_dialogue_content(result)


if __name__ == "__main__":
    unittest.main()
