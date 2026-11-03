
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from dotenv import load_dotenv

# Load environment variables from the project .env file.
load_dotenv()

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_secret_key() -> str:
    """
    Retrieve the JWT signing secret from an environment variable.
    """
    secret_key = os.getenv("CYBERTALK_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "CYBERTALK_SECRET_KEY environment variable is not configured."
        )

    return secret_key


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token with an expiration time.
    """
    payload = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})

    token = jwt.encode(
        payload,
        get_secret_key(),
        algorithm=ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Verify a JWT access token and return its payload.
    """
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[ALGORITHM],
        )

        return payload

    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired access token.") from exc
