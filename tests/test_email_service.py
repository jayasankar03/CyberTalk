
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs
import html

from email_service import (
    build_password_reset_link,
    send_password_reset_email,
)
from unittest.mock import MagicMock

class PasswordResetURLSecurityTests(unittest.TestCase):

    def setUp(self):
        self.environment = patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "development",
                "CYBERTALK_PASSWORD_RESET_URL":
                    "http://localhost:8501/",
            },
            clear=False,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def build_link(
        self,
        reset_url="http://localhost:8501/",
        token="secure_test_token",
        email="user@example.com",
    ):
        return build_password_reset_link(
            reset_url=reset_url,
            reset_token=token,
            recipient_email=email,
        )

    # Development URL tests

    def test_accepts_localhost_http(self):
        link = self.build_link()

        self.assertTrue(
            link.startswith("http://localhost:8501/")
        )

    def test_accepts_localhost_ip(self):
        link = self.build_link(
            reset_url="http://127.0.0.1:8501/"
        )

        self.assertTrue(
            link.startswith("http://127.0.0.1:8501/")
        )

    def test_accepts_localhost_ipv6(self):
        link = self.build_link(
            reset_url="http://[::1]:8501/"
        )

        self.assertTrue(
            link.startswith("http://[::1]:8501/")
        )

    def test_rejects_unexpected_local_port(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="http://localhost:8000/"
            )

    def test_rejects_external_http_host(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="http://example.com/"
            )

    def test_rejects_https_in_development(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="https://localhost:8501/"
            )

    # Production URL tests

    def test_accepts_trusted_production_https_url(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS":
                    "cybertalk.example.com",
            },
        ):
            link = self.build_link(
                reset_url="https://cybertalk.example.com/reset"
            )

        self.assertTrue(
            link.startswith(
                "https://cybertalk.example.com/reset"
            )
        )

    def test_rejects_http_in_production(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS":
                    "cybertalk.example.com",
            },
        ):
            with self.assertRaises(RuntimeError):
                self.build_link(
                    reset_url="http://cybertalk.example.com/"
                )

    def test_rejects_untrusted_production_host(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS":
                    "cybertalk.example.com",
            },
        ):
            with self.assertRaises(RuntimeError):
                self.build_link(
                    reset_url="https://evil.example.com/"
                )

    def test_rejects_missing_production_allowlist(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
            },
        ):
            with self.assertRaises(RuntimeError):
                self.build_link(
                    reset_url="https://cybertalk.example.com/"
                )

    def test_rejects_unexpected_production_port(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS":
                    "cybertalk.example.com",
            },
        ):
            with self.assertRaises(RuntimeError):
                self.build_link(
                    reset_url="https://cybertalk.example.com:8443/"
                )

    # Unsafe URL tests

    def test_rejects_javascript_scheme(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="javascript:alert(1)"
            )

    def test_rejects_data_scheme(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="data:text/html,test"
            )

    def test_rejects_file_scheme(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="file:///etc/passwd"
            )

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url=(
                    "http://attacker@localhost:8501/"
                )
            )

    def test_rejects_password_in_url(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url=(
                    "http://user:password@localhost:8501/"
                )
            )

    def test_rejects_url_with_fragment(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="http://localhost:8501/#section"
            )

    def test_rejects_url_with_backslash(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="http://localhost:8501/\\evil"
            )

    def test_rejects_url_with_whitespace(self):
        with self.assertRaises(RuntimeError):
            self.build_link(
                reset_url="http://localhost:8501/ reset"
            )

    def test_rejects_missing_environment(self):
        with patch.dict(
            "os.environ",
            {},
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                self.build_link()

    def test_rejects_unsupported_environment(self):
        with patch.dict(
            "os.environ",
            {"CYBERTALK_ENV": "testing"},
        ):
            with self.assertRaises(RuntimeError):
                self.build_link()

    # Query parameter encoding tests

    def test_token_and_email_are_safely_encoded(self):
        token = "token+with/special=characters"
        email = "user+test@example.com"

        link = self.build_link(
            token=token,
            email=email,
        )

        query = parse_qs(urlsplit(link).query)

        self.assertEqual(query["token"], [token])
        self.assertEqual(query["email"], [email])

    def test_existing_token_and_email_are_replaced(self):
        link = self.build_link(
            reset_url=(
                "http://localhost:8501/"
                "?token=attacker&email=evil@example.com"
            ),
        )

        query = parse_qs(urlsplit(link).query)

        self.assertEqual(
            query["token"],
            ["secure_test_token"],
        )

        self.assertEqual(
            query["email"],
            ["user@example.com"],
        )

        self.assertEqual(len(query["token"]), 1)
        self.assertEqual(len(query["email"]), 1)

    # HTML escaping tests

    def test_html_escape_protects_url_attributes(self):
        link = (
            "http://localhost:8501/"
            "?token=abc&email=user@example.com"
        )

        safe_link = html.escape(link, quote=True)

        self.assertIn("&amp;", safe_link)
        self.assertEqual(
            html.unescape(safe_link),
            link,
        )

    def test_html_escape_protects_quotes_and_tags(self):
        malicious_value = (
            '"><script>alert("attack")</script>'
        )

        safe_value = html.escape(
            malicious_value,
            quote=True,
        )

        self.assertNotIn("<script>", safe_value)
        self.assertNotIn('"', safe_value)
        self.assertIn("&lt;script&gt;", safe_value)


    def test_generated_email_contains_validated_reset_link(self):
        smtp_settings = {
            "CYBERTALK_ENV": "development",
            "CYBERTALK_PASSWORD_RESET_URL":
                "http://localhost:8501/",
            "CYBERTALK_SMTP_HOST": "smtp.gmail.com",
            "CYBERTALK_SMTP_PORT": "587",
            "CYBERTALK_SMTP_USERNAME": "test@gmail.com",
            "CYBERTALK_SMTP_PASSWORD": "test_password",
            "CYBERTALK_SMTP_FROM_EMAIL": "test@gmail.com",
        }

        mock_server = MagicMock()

        with patch.dict("os.environ", smtp_settings):
            with patch(
                "email_service.smtplib.SMTP"
            ) as mock_smtp:

                mock_smtp.return_value.__enter__.return_value = (
                    mock_server
                )

                send_password_reset_email(
                    recipient_email="user@example.com",
                    reset_token="integration_test_token",
                )

        mock_smtp.assert_called_once()

        message = mock_server.send_message.call_args.args[0]

        plain_body = message.get_body(
            preferencelist=("plain",)
        ).get_content()

        html_body = message.get_body(
            preferencelist=("html",)
        ).get_content()

        self.assertIn(
            "http://localhost:8501/",
            plain_body,
        )

        self.assertIn(
            "integration_test_token",
            plain_body,
        )

        self.assertIn(
            "Reset Password",
            html_body,
        )

        self.assertIn(
            "integration_test_token",
            html_body,
        )

    def test_generated_html_email_escapes_query_parameters(self):
        smtp_settings = {
            "CYBERTALK_ENV": "development",
            "CYBERTALK_PASSWORD_RESET_URL":
                "http://localhost:8501/",
            "CYBERTALK_SMTP_HOST": "smtp.gmail.com",
            "CYBERTALK_SMTP_PORT": "587",
            "CYBERTALK_SMTP_USERNAME": "test@gmail.com",
            "CYBERTALK_SMTP_PASSWORD": "test_password",
            "CYBERTALK_SMTP_FROM_EMAIL": "test@gmail.com",
        }

        mock_server = MagicMock()

        with patch.dict("os.environ", smtp_settings):
            with patch(
                "email_service.smtplib.SMTP"
            ) as mock_smtp:

                mock_smtp.return_value.__enter__.return_value = (
                    mock_server
                )

                send_password_reset_email(
                    recipient_email="user+test@example.com",
                    reset_token="token+special/value",
                )

        message = mock_server.send_message.call_args.args[0]

        html_body = message.get_body(
            preferencelist=("html",)
        ).get_content()

        # Query separators must be HTML-escaped.
        self.assertIn("&amp;", html_body)

        # Raw query separators must not appear in HTML href values.
        self.assertNotIn("&email=", html_body)

        self.assertEqual(
            html_body.count("&amp;"),
            3,
        )

        self.assertNotIn(
            "<script>",
            html_body,
        )

    def test_email_generation_rejects_untrusted_url(self):
        smtp_settings = {
            "CYBERTALK_ENV": "development",
            "CYBERTALK_PASSWORD_RESET_URL":
                "http://evil.example.com/",
            "CYBERTALK_SMTP_HOST": "smtp.gmail.com",
            "CYBERTALK_SMTP_PORT": "587",
            "CYBERTALK_SMTP_USERNAME": "test@gmail.com",
            "CYBERTALK_SMTP_PASSWORD": "test_password",
            "CYBERTALK_SMTP_FROM_EMAIL": "test@gmail.com",
        }

        with patch.dict("os.environ", smtp_settings):
            with patch(
                "email_service.smtplib.SMTP"
            ) as mock_smtp:

                with self.assertRaises(RuntimeError):
                    send_password_reset_email(
                        recipient_email="user@example.com",
                        reset_token="test_token",
                    )

                # SMTP must never be contacted for an unsafe URL.
                mock_smtp.assert_not_called()

    def test_generated_email_uses_escaped_url_in_both_html_links(self):
        smtp_settings = {
            "CYBERTALK_ENV": "development",
            "CYBERTALK_PASSWORD_RESET_URL":
                "http://localhost:8501/",
            "CYBERTALK_SMTP_HOST": "smtp.gmail.com",
            "CYBERTALK_SMTP_PORT": "587",
            "CYBERTALK_SMTP_USERNAME": "test@gmail.com",
            "CYBERTALK_SMTP_PASSWORD": "test_password",
            "CYBERTALK_SMTP_FROM_EMAIL": "test@gmail.com",
        }

        mock_server = MagicMock()

        with patch.dict("os.environ", smtp_settings):
            with patch(
                "email_service.smtplib.SMTP"
            ) as mock_smtp:

                mock_smtp.return_value.__enter__.return_value = (
                    mock_server
                )

                send_password_reset_email(
                    recipient_email="user@example.com",
                    reset_token="html_link_test_token",
                )

        message = mock_server.send_message.call_args.args[0]

        html_body = message.get_body(
            preferencelist=("html",)
        ).get_content()

        # Both the button and fallback link must be present.
        self.assertEqual(
            html_body.count(
                'href="http://localhost:8501/?token='
            ),
            2,
        )

        self.assertEqual(
            html_body.count("&amp;"),
            3,
        )

        self.assertEqual(
            html_body.count("html_link_test_token"),
            3,
        )

if __name__ == "__main__":
    unittest.main()
