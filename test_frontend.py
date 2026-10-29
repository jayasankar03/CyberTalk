
import unittest

from streamlit.testing.v1 import AppTest


class FrontendTests(unittest.TestCase):
    def test_page_heading_and_custom_persona_guidance(self):
        app = AppTest.from_file("frontend.py", default_timeout=10).run()

        self.assertEqual(app.title[0].value, "🛡️ CyberTalk")
        self.assertTrue(
            any(
                "Enter your own stakeholder roles" in element.value
                for element in app.info
            )
        )

    def test_empty_cybersecurity_question_is_rejected(self):
        app = AppTest.from_file("frontend.py", default_timeout=10).run()

        app.text_input[0].set_value("   ")
        app.button[0].click().run(timeout=10)

        self.assertTrue(
            any(
                "Please enter a question." in element.value
                for element in app.error
            )
        )

    def test_identical_stakeholders_are_rejected(self):
        app = AppTest.from_file("frontend.py", default_timeout=10).run()

        app.text_area[0].set_value("Improve phishing protection")
        app.text_input[1].set_value("Security Officer")
        app.text_input[2].set_value(" security officer ")
        app.button[1].click().run(timeout=10)

        self.assertTrue(
            any(
                "Please provide two different stakeholders." in element.value
                for element in app.error
            )
        )


if __name__ == "__main__":
    unittest.main()
