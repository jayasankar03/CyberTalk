import os

from urllib.parse import urlsplit
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/chat",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2:3b",
)

def get_environment() -> str:
    """Return the normalized CyberTalk environment."""
    return (
        os.getenv("CYBERTALK_ENV") or "development"
    ).strip().lower()


def validate_environment() -> str:
    """
    Validate the configured CyberTalk environment.

    Supported environments:
    - development
    - testing
    - production
    """
    environment = get_environment()

    allowed_environments = {
        "development",
        "testing",
        "production",
    }

    if environment not in allowed_environments:
        raise RuntimeError(
            "Invalid CYBERTALK_ENV configuration. "
            "Expected development, testing, or production."
        )

    return environment

def validate_ollama_configuration() -> None:
    """Validate Ollama connection settings without contacting the server."""

    ollama_url = os.getenv("OLLAMA_URL", OLLAMA_URL).strip()
    model_name = os.getenv("MODEL_NAME", MODEL_NAME).strip()

    if not ollama_url:
        raise RuntimeError(
            "OLLAMA_URL must not be empty."
        )

    try:
        parsed_url = urlsplit(ollama_url)
        hostname = parsed_url.hostname
        port = parsed_url.port
    except ValueError as exc:
        raise RuntimeError(
            "OLLAMA_URL is not a valid URL."
        ) from exc

    if parsed_url.scheme not in {"http", "https"} or not hostname:
        raise RuntimeError(
            "OLLAMA_URL must be a valid HTTP or HTTPS URL with a hostname."
        )

    if parsed_url.username or parsed_url.password:
        raise RuntimeError(
            "OLLAMA_URL must not contain embedded credentials."
        )

    if port is not None and not (1 <= port <= 65535):
        raise RuntimeError(
            "OLLAMA_URL contains an invalid port."
        )

    if not model_name:
        raise RuntimeError(
            "MODEL_NAME must not be empty."
        )
