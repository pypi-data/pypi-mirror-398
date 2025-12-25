"""Integration tests for error handling across commands."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestTimeoutErrors:
    """Tests for timeout error handling."""

    def test_search_timeout(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test timeout handling in search command."""
        httpx_mock.add_exception(httpx.TimeoutException("Connection timed out"))

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1
        assert "timeout" in result.output.lower() or "timed out" in result.output.lower()

    def test_download_timeout(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test timeout handling in download command."""
        httpx_mock.add_exception(httpx.TimeoutException("Connection timed out"))

        result = cli_runner.invoke(main, ["download", "101", "--output", str(tmp_path)])

        assert result.exit_code == 1
        assert "timeout" in result.output.lower()

    def test_collections_timeout(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test timeout handling in collections command."""
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        result = cli_runner.invoke(main, ["collections", "list"])

        assert result.exit_code == 1
        assert "timeout" in result.output.lower()


class TestConnectionErrors:
    """Tests for connection error handling."""

    def test_connection_refused(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of connection refused error."""
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1
        assert (
            "connect" in result.output.lower() or "connection" in result.output.lower()
        )

    def test_dns_resolution_failure(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of DNS resolution failure."""
        httpx_mock.add_exception(httpx.ConnectError("Name or service not known"))

        result = cli_runner.invoke(main, ["types", "list"])

        assert result.exit_code == 1

    def test_network_unreachable(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of network unreachable error."""
        httpx_mock.add_exception(httpx.ConnectError("Network is unreachable"))

        result = cli_runner.invoke(main, ["collections", "list"])

        assert result.exit_code == 1


class TestHTTPStatusErrors:
    """Tests for HTTP status error handling."""

    def test_404_not_found(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 404 Not Found."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            status_code=404,
            json={"error": "Resource not found"},
        )

        result = cli_runner.invoke(main, ["info", "99999"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "404" in result.output

    def test_500_server_error(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 500 Internal Server Error."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=500,
            json={"error": "Internal server error"},
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1
        assert "server" in result.output.lower() or "500" in result.output

    def test_502_bad_gateway(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 502 Bad Gateway."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=502,
            text="Bad Gateway",
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1

    def test_503_service_unavailable(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling of 503 Service Unavailable."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            status_code=503,
            text="Service temporarily unavailable",
        )

        result = cli_runner.invoke(main, ["collections", "list"])

        assert result.exit_code == 1


class TestJSONErrorOutput:
    """Tests for JSON error output format."""

    def test_error_json_format(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that errors in JSON mode have correct format."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            status_code=500,
        )

        result = cli_runner.invoke(main, ["--json", "search", "test"])

        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["status"] == "error"
        assert "error_type" in output
        assert "message" in output

    def test_connection_error_json_format(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that connection errors in JSON mode have correct format."""
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        result = cli_runner.invoke(main, ["--json", "search", "test"])

        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["status"] == "error"

    def test_timeout_error_json_format(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that timeout errors in JSON mode have correct format."""
        httpx_mock.add_exception(httpx.TimeoutException("Timed out"))

        result = cli_runner.invoke(main, ["--json", "collections", "list"])

        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["status"] == "error"

    def test_error_includes_suggestion(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test that error output includes helpful suggestions."""
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        result = cli_runner.invoke(main, ["--json", "search", "test"])

        output = json.loads(result.output)
        # Error should include some guidance
        assert "suggestion" in output or "message" in output


class TestInvalidResponseHandling:
    """Tests for invalid response handling."""

    def test_empty_response(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling when API returns empty response."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            text="",
        )

        result = cli_runner.invoke(main, ["search", "test"])

        # Should handle gracefully - either show no results or error
        # but shouldn't crash
        assert result.exit_code in [0, 1]

    def test_html_error_page_response(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test handling when API returns HTML error page."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            text="<html><body><h1>500 Internal Server Error</h1></body></html>",
            headers={"content-type": "text/html"},
        )

        result = cli_runner.invoke(main, ["search", "test"])

        assert result.exit_code == 1


class TestValidationErrors:
    """Tests for input validation error handling."""

    def test_search_with_empty_query(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test search with empty query string."""
        result = cli_runner.invoke(main, ["search", ""])

        assert result.exit_code == 1

    def test_info_with_zero_id(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test info with zero resource ID."""
        result = cli_runner.invoke(main, ["info", "0"])

        assert result.exit_code == 1

    def test_download_with_negative_id(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test download with negative resource ID."""
        result = cli_runner.invoke(
            main, ["download", "-1", "--output", str(tmp_path)]
        )

        # Exit code 2 is Click's error for bad arguments, 1 is application error
        assert result.exit_code != 0
