
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest


class FrontendTests(unittest.TestCase):

    def run_authenticated_app(self, history_records=None, history_detail=None):
        """Start the frontend with a mocked authenticated user."""

        app = AppTest.from_file(
            str(Path(__file__).resolve().parent.parent / "frontend.py"),
            default_timeout=10
        ).run()

        app.session_state["access_token"] = "test-access-token"

        profile_response = Mock()
        profile_response.ok = True
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
        }

        history_response = Mock()
        history_response.ok = True
        history_response.status_code = 200
        history_response.json.return_value = (
            history_records if history_records is not None else []
        )

        detail_response = Mock()
        detail_response.ok = True
        detail_response.status_code = 200
        detail_response.json.return_value = (
            history_detail if history_detail is not None else {}
        )

        def mock_get(url, *args, **kwargs):
            if url.endswith("/users/me"):
                return profile_response

            if "/history/" in url:
                return detail_response

            if url.endswith("/history"):
                return history_response

            raise AssertionError(f"Unexpected GET request: {url}")

        get_patcher = patch(
            "requests.get",
            side_effect=mock_get
        )
        get_patcher.start()
        self.addCleanup(get_patcher.stop)

        app.run()

        return app
    def test_page_heading_and_custom_persona_guidance(self):
        app = self.run_authenticated_app()

        self.assertEqual(app.title[0].value, "🛡️ CyberTalk")

        self.assertTrue(
            any(
                "Enter your own stakeholder roles" in element.value
                for element in app.info
            )
        )

    def test_empty_cybersecurity_question_is_rejected(self):
        app = self.run_authenticated_app()

        app.text_input[0].set_value("   ")
        app.button[0].click().run(timeout=10)

        self.assertTrue(
            any(
                "Please enter a question." in element.value
                for element in app.error
            )
        )

    def test_short_topic_is_rejected(self):
        app = self.run_authenticated_app()

        app.text_area[0].set_value("AB")
        app.text_input[1].set_value("Security Architect")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "at least 3 characters" in element.value
                for element in app.error
            )
        )

    def test_short_stakeholder_name_is_rejected(self):
        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve network security")
        app.text_input[1].set_value("A")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "Stakeholder 1 must contain at least 2 characters."
                in element.value
                for element in app.error
            )
        )

    def test_identical_stakeholders_are_rejected(self):
        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve phishing protection")
        app.text_input[1].set_value("Security Officer")
        app.text_input[2].set_value(" security officer ")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "Please provide two different stakeholders."
                in element.value
                for element in app.error
            )
        )

    @patch("requests.post")
    def test_successful_cybersecurity_answer_is_displayed(
        self, mock_post
    ):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "answer": "Use MFA to strengthen account security."
        }

        mock_post.return_value = mock_response

        app = self.run_authenticated_app()

        app.text_input[0].set_value(
            "How can MFA improve account security?"
        )

        app.button[0].click().run(timeout=10)

        self.assertTrue(
            any(
                "Use MFA to strengthen account security."
                in element.value
                for element in app.markdown
            )
        )

    @patch("requests.post")
    def test_successful_dialogue_and_agreement_are_displayed(
        self, mock_post
    ):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "topic": "Improve cloud security",
            "stakeholders": [
                {"name": "Security Architect"},
                {"name": "Cloud Engineer"},
            ],
            "rounds": 1,
            "dialogue": [
                {
                    "turn": 1,
                    "speaker": "Security Architect",
                    "message": "We should enable MFA."
                },
                {
                    "turn": 1,
                    "speaker": "Cloud Engineer",
                    "message": "I agree with a phased rollout."
                },
                {
                    "turn": 2,
                    "speaker": "Security Architect",
                    "message": "I agree to the phased rollout."
                },
                {
                    "turn": 2,
                    "speaker": "Cloud Engineer",
                    "message": "We have a shared decision."
                },
            ],
            "agreement": {
                "status": "agreement_reached",
                "explanation": "Both stakeholders reached agreement.",
                "shared_decision": "Implement MFA through a phased rollout.",
                "unresolved_disagreements": [],
                "next_actions": ["Prepare the MFA rollout plan."],
            },
        }

        mock_post.return_value = mock_response

        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve cloud security")
        app.text_input[1].set_value("Security Architect")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "Discussion Results" in element.value
                for element in app.header
            )
        )

        self.assertTrue(
            any(
                "agreement_reached" in element.value
                or "Agreement reached" in element.value
                for element in app.markdown
            )
        )

        self.assertTrue(
            any(
                "Implement MFA through a phased rollout."
                in element.value
                for element in app.success
            )
        )

    @patch("requests.post")
    def test_qa_api_connection_error_is_handled(self, mock_post):
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError()

        app = self.run_authenticated_app()

        app.text_input[0].set_value("How does encryption work?")
        app.button[0].click().run(timeout=10)

        self.assertTrue(
            any(
                "Could not connect to the CyberTalk API."
                in element.value
                for element in app.error
            )
        )

    @patch("requests.post")
    def test_dialogue_api_timeout_is_handled(self, mock_post):
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve cloud security")
        app.text_input[1].set_value("Security Architect")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "The request timed out."
                in element.value
                for element in app.error
            )
        )

    @patch("requests.post")
    def test_dialogue_api_http_error_is_handled(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "Invalid dialogue request."
        }

        mock_post.return_value = mock_response

        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve cloud security")
        app.text_input[1].set_value("Security Architect")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "Invalid dialogue request." in element.value
                for element in app.error
            )
        )
    @patch("requests.post")
    def test_successful_qa_is_saved_to_history(self, mock_post):
        qa_response = Mock()
        qa_response.ok = True
        qa_response.json.return_value = {
            "answer": "Use MFA to protect user accounts."
        }

        save_response = Mock()
        save_response.status_code = 201

        mock_post.side_effect = [qa_response, save_response]

        app = self.run_authenticated_app()

        app.text_input[0].set_value(
            "How can MFA protect user accounts?"
        )
        app.button[0].click().run(timeout=10)

        self.assertEqual(mock_post.call_count, 2)

        save_call = mock_post.call_args_list[1]

        self.assertTrue(save_call.args[0].endswith("/history"))
        self.assertEqual(
            save_call.kwargs["headers"]["Authorization"],
            "Bearer test-access-token"
        )

        saved_data = save_call.kwargs["json"]

        self.assertEqual(saved_data["conversation_type"], "qa")
        self.assertEqual(
            saved_data["title"],
            "How can MFA protect user accounts?"
        )
        self.assertIn(
            "Use MFA to protect user accounts.",
            saved_data["content"]
        )

        self.assertTrue(
            any(
                "saved to chat history" in element.value.lower()
                for element in app.success
            )
        )

    @patch("requests.post")
    def test_successful_dialogue_is_saved_to_history(self, mock_post):
        dialogue_response = Mock()
        dialogue_response.ok = True
        dialogue_response.json.return_value = {
            "topic": "Improve cloud security",
            "stakeholders": [
                {"name": "Security Architect"},
                {"name": "Cloud Engineer"},
            ],
            "rounds": 1,
            "dialogue": [
                {
                    "turn": 1,
                    "speaker": "Security Architect",
                    "message": "We should enable MFA.",
                },
            ],
            "agreement": {
                "status": "partial_agreement",
                "explanation": "The stakeholders partially agree.",
                "shared_decision": "Plan an MFA rollout.",
                "unresolved_disagreements": [],
                "next_actions": ["Prepare a rollout plan."],
            },
        }

        save_response = Mock()
        save_response.status_code = 201

        mock_post.side_effect = [
            dialogue_response,
            save_response,
        ]

        app = self.run_authenticated_app()

        app.text_area[0].set_value("Improve cloud security")
        app.text_input[1].set_value("Security Architect")
        app.text_input[2].set_value("Cloud Engineer")

        app.button[1].click().run(timeout=10)

        self.assertEqual(mock_post.call_count, 2)

        save_call = mock_post.call_args_list[1]

        self.assertTrue(save_call.args[0].endswith("/history"))

        saved_data = save_call.kwargs["json"]

        self.assertEqual(
            saved_data["conversation_type"],
            "dialogue"
        )
        self.assertEqual(
            saved_data["title"],
            "Improve cloud security"
        )
        self.assertIn(
            "Security Architect",
            saved_data["content"]
        )

    def test_saved_conversation_can_be_opened(self):
        history_records = [
            {
                "id": 1,
                "conversation_type": "qa",
                "title": "How does MFA work?",
                "created_at": "2026-11-02T10:00:00",
            }
        ]

        history_detail = {
            "id": 1,
            "conversation_type": "qa",
            "title": "How does MFA work?",
            "content": (
                '{"question":"How does MFA work?",'
                '"answer":"MFA adds another layer of authentication."}'
            ),
            "created_at": "2026-11-02T10:00:00",
        }

        app = self.run_authenticated_app(
            history_records=history_records,
            history_detail=history_detail,
        )

        open_button = next(
            button
            for button in app.button
            if button.label == "Open Conversation"
        )

        open_button.click().run(timeout=10)

        self.assertTrue(
            any(
                "MFA adds another layer of authentication."
                in element.value
                for element in app.markdown
            )
        )

    @patch("requests.delete")
    def test_saved_conversation_can_be_deleted(self, mock_delete):
        history_records = [
            {
                "id": 1,
                "conversation_type": "qa",
                "title": "Old cybersecurity question",
                "created_at": "2026-11-02T10:00:00",
            }
        ]

        delete_response = Mock()
        delete_response.ok = True
        delete_response.status_code = 204

        mock_delete.return_value = delete_response

        app = self.run_authenticated_app(
            history_records=history_records
        )

        delete_button = next(
            button
            for button in app.button
            if button.label == "Delete Conversation"
        )

        delete_button.click().run(timeout=10)

        mock_delete.assert_called_once()

        delete_call = mock_delete.call_args

        self.assertTrue(
            delete_call.args[0].endswith("/history/1")
        )

        self.assertEqual(
            delete_call.kwargs["headers"]["Authorization"],
            "Bearer test-access-token"
        )

if __name__ == "__main__":
    unittest.main()
