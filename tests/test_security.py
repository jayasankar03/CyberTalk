
import unittest

from security import hash_password, verify_password


class PasswordSecurityTests(unittest.TestCase):

    def test_password_is_hashed(self):
        password = "StrongPassword123!"
        hashed = hash_password(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(hashed.startswith("$argon2id$"))

    def test_same_password_generates_different_hashes(self):
        password = "StrongPassword123!"

        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, second_hash)

    def test_correct_password_is_verified(self):
        password = "StrongPassword123!"
        hashed = hash_password(password)

        self.assertTrue(verify_password(password, hashed))

    def test_incorrect_password_is_rejected(self):
        hashed = hash_password("StrongPassword123!")

        self.assertFalse(
            verify_password("WrongPassword123!", hashed)
        )

    def test_invalid_hash_is_rejected(self):
        self.assertFalse(
            verify_password("password", "not-a-valid-hash")
        )

    def test_empty_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("")

    def test_non_string_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password(None)

    def test_non_string_verification_input_is_rejected(self):
        self.assertFalse(verify_password(None, "some-hash"))
        self.assertFalse(verify_password("password", None))


if __name__ == "__main__":
    unittest.main()
