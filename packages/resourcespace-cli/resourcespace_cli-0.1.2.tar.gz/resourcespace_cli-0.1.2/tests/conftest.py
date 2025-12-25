"""Shared fixtures for ResourceSpace CLI tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import click
import pytest

from resourcespace_cli.config import Config


@pytest.fixture
def mock_config() -> Config:
    """Create a complete mock configuration."""
    return Config(
        api_url="https://example.com/api",
        api_key="test_api_key_12345",
        user="testuser",
    )


@pytest.fixture
def incomplete_config() -> Config:
    """Create an incomplete configuration (missing api_key)."""
    return Config(
        api_url="https://example.com/api",
        api_key=None,
        user="testuser",
    )


@pytest.fixture
def mock_click_context(request: pytest.FixtureRequest) -> click.Context:
    """Create a mock Click context.

    By default returns a context with json_output=False.
    Use @pytest.mark.parametrize or pass json_output via indirect fixture.
    """
    json_output = getattr(request, "param", False)

    ctx = MagicMock(spec=click.Context)
    ctx.obj = {"json_output": json_output}
    ctx.exit = MagicMock()
    return ctx


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary .env file for config tests.

    Yields the path to the temp .env file and cleans up after.
    """
    env_file = tmp_path / ".env"
    env_file.touch()

    # Store original env var if it exists
    original_env_path = os.environ.get("RESOURCESPACE_ENV_PATH")

    # Point config to use temp file
    os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

    yield env_file

    # Restore original env var
    if original_env_path is not None:
        os.environ["RESOURCESPACE_ENV_PATH"] = original_env_path
    else:
        os.environ.pop("RESOURCESPACE_ENV_PATH", None)


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Temporarily clear ResourceSpace environment variables.

    Useful for testing config loading without env var interference.
    """
    env_vars = [
        "RESOURCESPACE_API_URL",
        "RESOURCESPACE_API_KEY",
        "RESOURCESPACE_USER",
        "RESOURCESPACE_ENV_PATH",
    ]

    # Store original values
    original_values: dict[str, str | None] = {}
    for var in env_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)


@pytest.fixture
def sample_api_response() -> dict[str, Any]:
    """Sample API response for testing."""
    return {
        "ref": "123",
        "field8": "Test Resource",
        "resource_type": "1",
        "file_extension": "jpg",
    }


@pytest.fixture
def sample_collection_response() -> list[dict[str, Any]]:
    """Sample collection list response."""
    return [
        {"ref": "1", "name": "Collection A", "count": 10},
        {"ref": "2", "name": "Collection B", "count": 5},
    ]
