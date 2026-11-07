import asyncio

import pytest

import main


async def run_application_startup():
    async with main.lifespan(main.app):
        pass


def test_startup_validates_configuration_before_database_initialization(
    monkeypatch,
):
    calls = []

    # Mock configuration validation functions.
    monkeypatch.setattr(
        main,
        "validate_environment",
        lambda: calls.append("validate_environment"),
    )
    monkeypatch.setattr(
        main,
        "get_secret_key",
        lambda: calls.append("get_secret_key"),
    )
    monkeypatch.setattr(
        main,
        "validate_ollama_configuration",
        lambda: calls.append("validate_ollama_configuration"),
    )

    # Mock database initialization and migrations.
    database_operations = [
        "create_db_tables",
        "migrate_user_account_lifecycle",
        "migrate_audit_log_account_status",
        "migrate_primary_admin",
        "migrate_user_auth_version",
    ]

    for operation in database_operations:
        monkeypatch.setattr(
            main,
            operation,
            lambda operation=operation: calls.append(operation),
        )

    asyncio.run(run_application_startup())

    assert calls == [
        "validate_environment",
        "get_secret_key",
        "validate_ollama_configuration",
        "create_db_tables",
        "migrate_user_account_lifecycle",
        "migrate_audit_log_account_status",
        "migrate_primary_admin",
        "migrate_user_auth_version",
    ]


@pytest.mark.parametrize(
    "failing_validator",
    [
        "validate_environment",
        "get_secret_key",
        "validate_ollama_configuration",
    ],
)
def test_startup_stops_when_configuration_validation_fails(
    monkeypatch,
    failing_validator,
):
    calls = []

    validators = [
        "validate_environment",
        "get_secret_key",
        "validate_ollama_configuration",
    ]

    for validator in validators:

        def mock_validator(validator=validator):
            calls.append(validator)

            if validator == failing_validator:
                raise RuntimeError("Configuration validation failed.")

        monkeypatch.setattr(main, validator, mock_validator)

    database_operations = [
        "create_db_tables",
        "migrate_user_account_lifecycle",
        "migrate_audit_log_account_status",
        "migrate_primary_admin",
        "migrate_user_auth_version",
    ]

    for operation in database_operations:
        monkeypatch.setattr(
            main,
            operation,
            lambda operation=operation: calls.append(operation),
        )

    with pytest.raises(
        RuntimeError,
        match="Configuration validation failed.",
    ):
        asyncio.run(run_application_startup())

    expected_calls = validators[:validators.index(failing_validator) + 1]

    assert calls == expected_calls

    assert not any(
        operation in calls
        for operation in database_operations
    )
