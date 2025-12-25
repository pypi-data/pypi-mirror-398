"""Integration tests for the search command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestSearchCommand:
    """Integration tests for rs search command."""

    def test_search_basic_query_text_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        search_url_pattern: re.Pattern[str],
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test basic search with default text output."""
        httpx_mock.add_response(
            url=search_url_pattern,
            json=sample_search_results,
        )

        result = cli_runner.invoke(main, ["search", "landscape"])

        assert result.exit_code == 0
        assert "Sunset Landscape" in result.output
        assert "101" in result.output

    def test_search_basic_query_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        search_url_pattern: re.Pattern[str],
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test search with JSON output."""
        httpx_mock.add_response(
            url=search_url_pattern,
            json=sample_search_results,
        )

        result = cli_runner.invoke(main, ["--json", "search", "landscape"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["count"] == 3
        assert len(output["results"]) == 3

    def test_search_with_type_filter(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test search with resource type filter."""
        # Filter to only type 1 resources
        filtered = [r for r in sample_search_results if r["resource_type"] == "1"]

        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*restypes=1.*"),
            json=filtered,
        )

        result = cli_runner.invoke(main, ["search", "photo", "--type", "1"])

        assert result.exit_code == 0

    def test_search_with_collection_filter(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test search with collection filter."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=sample_search_results[:1],
        )

        result = cli_runner.invoke(main, ["search", "photo", "--collection", "5"])

        assert result.exit_code == 0

    def test_search_with_pagination(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test search with pagination options."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=sample_search_results,
        )

        result = cli_runner.invoke(main, ["search", "photo", "--page", "3", "--limit", "10"])

        assert result.exit_code == 0
        assert "Page 3" in result.output

    def test_search_empty_results(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        search_url_pattern: re.Pattern[str],
    ) -> None:
        """Test search with no results."""
        httpx_mock.add_response(
            url=search_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_search_empty_results_json(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        search_url_pattern: re.Pattern[str],
    ) -> None:
        """Test search with no results in JSON mode."""
        httpx_mock.add_response(
            url=search_url_pattern,
            json=[],
        )

        result = cli_runner.invoke(main, ["--json", "search", "nonexistent"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["count"] == 0
        assert output["results"] == []

    def test_search_invalid_page_number(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test search with invalid page number."""
        result = cli_runner.invoke(main, ["search", "photo", "--page", "0"])

        assert result.exit_code == 1

    def test_search_invalid_limit(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test search with invalid limit."""
        result = cli_runner.invoke(main, ["search", "photo", "--limit", "-5"])

        assert result.exit_code == 1

    def test_search_shows_preview_urls(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        search_url_pattern: re.Pattern[str],
        sample_search_results: list[dict[str, Any]],
    ) -> None:
        """Test that search results display preview URLs."""
        httpx_mock.add_response(
            url=search_url_pattern,
            json=sample_search_results,
        )

        result = cli_runner.invoke(main, ["search", "landscape"])

        assert result.exit_code == 0
        # Check that preview URL domain is shown (may be truncated by Rich table)
        assert "resourcespace.example.com" in result.output or "previews" in result.output
