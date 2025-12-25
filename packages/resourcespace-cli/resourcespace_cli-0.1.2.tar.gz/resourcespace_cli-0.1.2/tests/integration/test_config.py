"""Integration tests for the config command."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from resourcespace_cli.main import main


class TestConfigSet:
    """Integration tests for rs config set command."""

    def test_config_set_url(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test setting the API URL."""
        env_file = tmp_path / ".env"
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(
                main, ["config", "set", "url", "https://new.example.com/api"]
            )

            assert result.exit_code == 0
            assert "Successfully set" in result.output
            assert env_file.exists()
            assert "https://new.example.com/api" in env_file.read_text()
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_set_json_output(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test config set with JSON output."""
        env_file = tmp_path / ".env"
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(
                main, ["--json", "config", "set", "key", "my_api_key"]
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["status"] == "success"
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_set_alias_resolution(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test that aliases are resolved correctly."""
        env_file = tmp_path / ".env"
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "set", "user", "testuser"])

            assert result.exit_code == 0
            assert "RESOURCESPACE_USER" in env_file.read_text()
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)


class TestConfigGet:
    """Integration tests for rs config get command."""

    def test_config_get_all_values(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test getting all configuration values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com/api\n"
            "RESOURCESPACE_API_KEY=secret_key_12345678\n"
            "RESOURCESPACE_USER=admin\n"
        )
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "get"])

            assert result.exit_code == 0
            assert "https://example.com/api" in result.output
            assert "admin" in result.output
            # API key should be masked (first 4 + **** + last 4)
            assert "secr****5678" in result.output
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_get_specific_key(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test getting a specific configuration value."""
        env_file = tmp_path / ".env"
        env_file.write_text("RESOURCESPACE_API_URL=https://test.example.com/api\n")
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "get", "url"])

            assert result.exit_code == 0
            assert "https://test.example.com/api" in result.output
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_get_show_values_flag(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test --show-values reveals secrets."""
        env_file = tmp_path / ".env"
        env_file.write_text("RESOURCESPACE_API_KEY=my_secret_key_12345\n")
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "get", "--show-values"])

            assert result.exit_code == 0
            assert "my_secret_key_12345" in result.output
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_get_incomplete_warning(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test warning for incomplete configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text("RESOURCESPACE_API_URL=https://example.com\n")
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "get"])

            assert result.exit_code == 0
            assert "incomplete" in result.output.lower() or "Missing" in result.output
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_get_json_output(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test config get with JSON output."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com/api\n"
            "RESOURCESPACE_API_KEY=test_key\n"
            "RESOURCESPACE_USER=admin\n"
        )
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["--json", "config", "get"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "values" in output
            assert output["is_complete"] is True
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)


class TestConfigClear:
    """Integration tests for rs config clear command."""

    def test_config_clear_specific_key(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test clearing a specific configuration key."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com\n" "RESOURCESPACE_USER=admin\n"
        )
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "clear", "url", "--yes"])

            assert result.exit_code == 0
            assert "Cleared" in result.output
            content = env_file.read_text()
            assert "RESOURCESPACE_API_URL" not in content
            assert "RESOURCESPACE_USER" in content  # Should remain
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_clear_all(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test clearing all configuration values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com\n"
            "RESOURCESPACE_API_KEY=secret\n"
            "RESOURCESPACE_USER=admin\n"
        )
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "clear", "--all", "--yes"])

            assert result.exit_code == 0
            content = env_file.read_text()
            assert "RESOURCESPACE_API_URL" not in content
            assert "RESOURCESPACE_API_KEY" not in content
            assert "RESOURCESPACE_USER" not in content
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_clear_requires_key_or_all(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error when neither key nor --all provided."""
        env_file = tmp_path / ".env"
        env_file.touch()
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(main, ["config", "clear"])

            assert result.exit_code == 1
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)

    def test_config_clear_json_output(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test config clear with JSON output."""
        env_file = tmp_path / ".env"
        env_file.write_text("RESOURCESPACE_API_URL=https://example.com\n")
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            result = cli_runner.invoke(
                main, ["--json", "config", "clear", "url", "--yes"]
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["status"] == "success"
            assert output["count"] == 1
        finally:
            os.environ.pop("RESOURCESPACE_ENV_PATH", None)
