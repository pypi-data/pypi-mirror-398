from typing import List

import pytest

from analysis3054.utils import (
    EnvVariableRequest,
    configure_snowflake_connector,
    ensure_env_variables,
)


def test_ensure_env_variables_prompts_missing(monkeypatch):
    captured: List[tuple[str, bool]] = []
    env = {}

    def fake_prompt(message: str, secret: bool = False) -> str:
        captured.append((message, secret))
        return "value"

    result = ensure_env_variables(
        [EnvVariableRequest("SNOWFLAKE_USER", "Enter username")],
        env=env,
        prompt_fn=fake_prompt,
    )

    assert result["SNOWFLAKE_USER"] == "value"
    assert env["SNOWFLAKE_USER"] == "value"
    assert captured == [("Enter username", False)]


def test_ensure_env_variables_skips_existing(monkeypatch):
    env = {"EXISTING": "present"}
    prompt_calls = []

    def fake_prompt(message: str, secret: bool = False) -> str:  # pragma: no cover - should not run
        prompt_calls.append((message, secret))
        return "ignored"

    result = ensure_env_variables(["EXISTING"], env=env, prompt_fn=fake_prompt)

    assert result["EXISTING"] == "present"
    assert prompt_calls == []


def test_configure_snowflake_connector_builds_kwargs(monkeypatch):
    responses = iter(
        [
            "user",
            "password",
            "account",
            "warehouse",
            "database",
            "schema",
            "role",
            "extra",
        ]
    )
    env = {}

    def fake_prompt(message: str, secret: bool = False) -> str:
        return next(responses)

    extra = {"name": "SNOWFLAKE_REGION", "prompt": "Enter region"}
    connector_kwargs = configure_snowflake_connector(
        variables=[extra], env=env, prompt_fn=fake_prompt
    )

    assert connector_kwargs["user"] == "user"
    assert connector_kwargs["password"] == "password"
    assert connector_kwargs["account"] == "account"
    assert connector_kwargs["warehouse"] == "warehouse"
    assert connector_kwargs["database"] == "database"
    assert connector_kwargs["schema"] == "schema"
    assert connector_kwargs["role"] == "role"
    # extra variable is collected and stored but not included in connector kwargs
    assert env["SNOWFLAKE_REGION"] == "extra"
