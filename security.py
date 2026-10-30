
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


# Create an Argon2 password hasher
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Generate a secure Argon2 hash for a password.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify whether a password matches its stored Argon2 hash.
    """
    if not isinstance(password, str) or not isinstance(hashed_password, str):
        return False

    try:
        return password_hasher.verify(hashed_password, password)

    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
