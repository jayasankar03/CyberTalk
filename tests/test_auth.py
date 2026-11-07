
import unittest
from datetime import timedelta
from unittest.mock import patch

from jwt.exceptions import InvalidTokenError

from auth import (
    create_access_token,
    decode_access_token,
    get_secret_key,
)


class AuthenticationTests(unittest.TestCase):

    def setUp(self):
        self.secret = "test-secret-key-for-cybertalk-authentication-123456"
        self.env_patch = patch.dict(
            "os.environ",
            {"CYBERTALK_SECRET_KEY": self.secret},
        )
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_successful_token_creation_and_decoding(self):
        token = create_access_token({"sub": "1"})

        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], "1")
        self.assertIn("exp", payload)

    def test_token_contains_expiration(self):
        token = create_access_token({"sub": "2"})

        payload = decode_access_token(token)

        self.assertIsNotNone(payload["exp"])

    def test_expired_token_is_rejected(self):
        token = create_access_token(
            {"sub": "3"},
            expires_delta=timedelta(seconds=-1),
        )

        with self.assertRaises(ValueError):
            decode_access_token(token)

    def test_tampered_token_is_rejected(self):
        token = create_access_token({"sub": "4"})

        tampered_token = token[:-1] + (
            "A" if token[-1] != "A" else "B"
        )

        with self.assertRaises(ValueError):
            decode_access_token(tampered_token)

    def test_invalid_token_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_access_token("invalid.token.value")

    def test_missing_secret_key_raises_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                get_secret_key()

    def test_production_rejects_short_secret_key(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_SECRET_KEY": "short-secret",
            },
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "at least 32 characters",
            ):
                get_secret_key()

    def test_production_rejects_placeholder_secret_key(self):
        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_SECRET_KEY": (
                    "replace-with-a-long-random-secret"
                ),
            },
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "placeholder value",
            ):
                get_secret_key()

    def test_production_accepts_strong_secret_key(self):
        strong_secret = (
            "production-secret-key-with-more-than-32-characters"
        )

        with patch.dict(
            "os.environ",
            {
                "CYBERTALK_ENV": "production",
                "CYBERTALK_SECRET_KEY": strong_secret,
            },
        ):
            self.assertEqual(get_secret_key(), strong_secret)

if __name__ == "__main__":
    unittest.main()
