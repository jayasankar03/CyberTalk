
import pytest

from config import get_environment, validate_environment


@pytest.mark.parametrize(
    "environment",
    ["development", "testing", "production"],
)
def test_validate_environment_accepts_supported_values(
    monkeypatch,
    environment,
):
    monkeypatch.setenv("CYBERTALK_ENV", environment)

    assert validate_environment() == environment


def test_validate_environment_normalizes_value(monkeypatch):
    monkeypatch.setenv("CYBERTALK_ENV", " PRODUCTION ")

    assert validate_environment() == "production"


def test_validate_environment_defaults_to_development(
    monkeypatch,
):
    monkeypatch.delenv("CYBERTALK_ENV", raising=False)

    assert get_environment() == "development"
    assert validate_environment() == "development"


def test_validate_environment_rejects_invalid_value(monkeypatch):
    monkeypatch.setenv("CYBERTALK_ENV", "prod")

    with pytest.raises(RuntimeError, match="Invalid CYBERTALK_ENV"):
        validate_environment()

@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:11434/api/chat",
        "https://ollama.example.com/api/chat",
    ],
)
def test_validate_ollama_configuration_accepts_valid_urls(
    monkeypatch,
    url,
):
    from config import validate_ollama_configuration

    monkeypatch.setenv("OLLAMA_URL", url)
    monkeypatch.setenv("MODEL_NAME", "llama3.2:3b")

    validate_ollama_configuration()


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://127.0.0.1:11434/api/chat",
        "http:///api/chat",
        "http://127.0.0.1:99999/api/chat",
        "http://user:password@127.0.0.1:11434/api/chat",
    ],
)
def test_validate_ollama_configuration_rejects_invalid_urls(
    monkeypatch,
    url,
):
    from config import validate_ollama_configuration

    monkeypatch.setenv("OLLAMA_URL", url)

    with pytest.raises(RuntimeError, match="OLLAMA_URL"):
        validate_ollama_configuration()


def test_validate_ollama_configuration_rejects_empty_model_name(
    monkeypatch,
):
    from config import validate_ollama_configuration

    monkeypatch.setenv(
        "OLLAMA_URL",
        "http://127.0.0.1:11434/api/chat",
    )
    monkeypatch.setenv("MODEL_NAME", "   ")

    with pytest.raises(RuntimeError, match="MODEL_NAME"):
        validate_ollama_configuration()
