"""Integration tests for the types command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestTypesList:
    """Integration tests for rs types list command."""

    def test_types_list_text_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        types_url_pattern: re.Pattern[str],
        sample_resource_types: list[dict[str, Any]],
    ) -> None:
        """Test listing resource types with text output."""
        httpx_mock.add_response(
            url=types_url_pattern,
            json=sample_resource_types,
        )

        result = cli_runner.invoke(main, ["types", "list"])

        assert result.exit_code == 0
        assert "Photo" in result.output
        assert "Document" in result.output
        assert "Video" in result.output
        assert "Audio" in result.output

    def test_types_list_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        types_url_pattern: re.Pattern[str],
        sample_resource_types: list[dict[str, Any]],
    ) -> None:
        """Test listing resource types with JSON output."""
        httpx_mock.add_response(
            url=types_url_pattern,
            json=sample_resource_types,
        )

        result = cli_runner.invoke(main, ["--json", "types", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["count"] == 4
        assert len(output["resource_types"]) == 4

    def test_types_list_empty(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        types_url_pattern: re.Pattern[str],
    ) -> None:
        """Test listing when no resource types exist."""
        httpx_mock.add_response(
            url=types_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["types", "list"])

        assert result.exit_code == 0
        assert "No resource types found" in result.output

    def test_types_list_empty_json(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        types_url_pattern: re.Pattern[str],
    ) -> None:
        """Test listing empty resource types with JSON output."""
        httpx_mock.add_response(
            url=types_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["--json", "types", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["count"] == 0
        assert output["resource_types"] == []
