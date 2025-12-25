"""Integration tests for the collections command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestCollectionsList:
    """Integration tests for rs collections list command."""

    def test_collections_list_text_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        collections_url_pattern: re.Pattern[str],
        sample_collections: list[dict[str, Any]],
    ) -> None:
        """Test listing collections with default text output."""
        httpx_mock.add_response(
            url=collections_url_pattern,
            json=sample_collections,
        )

        result = cli_runner.invoke(main, ["collections", "list"])

        assert result.exit_code == 0
        assert "Nature Photos" in result.output
        assert "Architecture" in result.output
        assert "Portraits" in result.output
        assert "25" in result.output  # count

    def test_collections_list_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        collections_url_pattern: re.Pattern[str],
        sample_collections: list[dict[str, Any]],
    ) -> None:
        """Test listing collections with JSON output."""
        httpx_mock.add_response(
            url=collections_url_pattern,
            json=sample_collections,
        )

        result = cli_runner.invoke(main, ["--json", "collections", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["count"] == 3
        assert len(output["collections"]) == 3

    def test_collections_list_empty(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        collections_url_pattern: re.Pattern[str],
    ) -> None:
        """Test listing collections when none exist."""
        httpx_mock.add_response(
            url=collections_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["collections", "list"])

        assert result.exit_code == 0
        assert "No collections found" in result.output

    def test_collections_list_empty_json(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        collections_url_pattern: re.Pattern[str],
    ) -> None:
        """Test listing empty collections with JSON output."""
        httpx_mock.add_response(
            url=collections_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["--json", "collections", "list"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["count"] == 0
        assert output["collections"] == []
