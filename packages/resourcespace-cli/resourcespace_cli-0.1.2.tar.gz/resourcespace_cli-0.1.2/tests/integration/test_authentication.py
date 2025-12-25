"""Integration tests for authentication flows."""

from __future__ import annotations

import os
import re
from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestAuthenticationErrors:
    """Tests for authentication error handling."""

    def test_missing_configuration(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error when configuration is missing."""
        env_file = tmp_path / ".env"
        env_file.touch()  # Empty file

        # Clear any env vars
        original = {
            k: os.environ.pop(k, None)
            for k in [
                "RESOURCESPACE_API_URL",
                "RESOURCESPACE_API_KEY",
                "RESOURCESPACE_USER",
            ]
        }
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["search", "test"])

            assert result.exit_code == 1
            assert (
                "Configuration" in result.output or "incomplete" in result.output.lower()
            )
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)
            for k, v in original.items():
                if v:
                    os.environ[k] = v

    def test_missing_api_url(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error when API URL is missing."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RESOURCESPACE_API_KEY=test_key\n" "RESOURCESPACE_USER=testuser\n"
        )

        original = {
            k: os.environ.pop(k, None)
            for k in [
                "RESOURCESPACE_API_URL",
                "RESOURCESPACE_API_KEY",
                "RESOURCESPACE_USER",
            ]
        }
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["search", "test"])

            assert result.exit_code == 1
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)
            for k, v in original.items():
                if v:
                    os.environ[k] = v

    def test_invalid_api_key_401(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 401 Unauthorized response."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=401,
            json={"error": "Invalid API key"},
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1
        assert "401" in result.output or "Authentication" in result.output or "API" in result.output

    def test_forbidden_403(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 403 Forbidden response."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=403,
            json={"error": "Access denied"},
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1
        assert "403" in result.output or "API" in result.output

    def test_signature_included_in_request(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that requests include proper signature parameter."""
        # This will capture the request and we can verify the sign parameter
        httpx_mock.add_response(
            url=re.compile(r".*sign=[a-f0-9]{64}.*"),  # SHA256 is 64 hex chars
            json=[],
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 0
        # If we got here without error, the URL pattern matched
        # meaning the signature was included

    def test_user_included_in_request(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that requests include user parameter."""
        httpx_mock.add_response(
            url=re.compile(r".*user=integration_user.*"),
            json=[],
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 0


class TestAuthenticationJSON:
    """Tests for authentication error handling in JSON mode."""

    def test_missing_config_json_output(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error output format when config is missing in JSON mode."""
        import json

        env_file = tmp_path / ".env"
        env_file.touch()

        original = {
            k: os.environ.pop(k, None)
            for k in [
                "RESOURCESPACE_API_URL",
                "RESOURCESPACE_API_KEY",
                "RESOURCESPACE_USER",
            ]
        }
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["--json", "search", "test"])

            assert result.exit_code == 1
            output = json.loads(result.output)
            assert output["status"] == "error"
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)
            for k, v in original.items():
                if v:
                    os.environ[k] = v

    def test_401_error_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test 401 error in JSON mode has correct format."""
        import json

        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=401,
        )

        result = cli_runner.invoke(main, ["--json", "search", "test"])

        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["status"] == "error"
        assert "error_type" in output
