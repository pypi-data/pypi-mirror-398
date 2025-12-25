"""Tests for error handling utilities."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import click
import pytest

from resourcespace_cli.exceptions import (
    APIError,
    ConfigurationError,
    ConnectionError,
    DownloadError,
    ResourceSpaceError,
    UploadError,
    ValidationError,
)
from resourcespace_cli.utils.errors import (
    ERROR_SUGGESTIONS,
    BatchResult,
    _format_api_error,
    _format_connection_error,
    handle_exception,
)


class TestHandleException:
    """Tests for handle_exception function."""

    @pytest.fixture
    def exit_context(self) -> click.Context:
        """Create a mock Click context that raises SystemExit on exit."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"json_output": False}
        ctx.exit = MagicMock(side_effect=SystemExit(1))
        return ctx

    def test_validation_error(self, exit_context: click.Context) -> None:
        """Test handling ValidationError."""
        error = ValidationError("Invalid input")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_configuration_error(self, exit_context: click.Context) -> None:
        """Test handling ConfigurationError."""
        error = ConfigurationError("Missing API key")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_connection_error(self, exit_context: click.Context) -> None:
        """Test handling ConnectionError."""
        error = ConnectionError("Network unreachable")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_api_error(self, exit_context: click.Context) -> None:
        """Test handling APIError."""
        error = APIError("Request failed", status_code=500)

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_download_error(self, exit_context: click.Context) -> None:
        """Test handling DownloadError."""
        error = DownloadError("Download failed")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_upload_error(self, exit_context: click.Context) -> None:
        """Test handling UploadError."""
        error = UploadError("Upload failed")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_base_resourcespace_error(self, exit_context: click.Context) -> None:
        """Test handling base ResourceSpaceError."""
        error = ResourceSpaceError("Generic error")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_unexpected_error(self, exit_context: click.Context) -> None:
        """Test handling unexpected exception types."""
        error = RuntimeError("Unexpected error")

        with pytest.raises(SystemExit):
            handle_exception(exit_context, error)

        exit_context.exit.assert_called_once_with(1)

    def test_json_output_format(self) -> None:
        """Test that JSON output format is used when json_output=True."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"json_output": True}
        ctx.exit = MagicMock(side_effect=SystemExit(1))

        error = ValidationError("Invalid input")

        with patch("click.echo") as mock_echo:
            with pytest.raises(SystemExit):
                handle_exception(ctx, error)

            # Verify JSON was output
            call_args = mock_echo.call_args[0][0]
            output = json.loads(call_args)
            assert output["status"] == "error"
            assert output["error_type"] == "Validation Error"
            assert output["message"] == "Invalid input"


class TestFormatConnectionError:
    """Tests for _format_connection_error function."""

    def test_timeout_error(self) -> None:
        """Test formatting timeout errors."""
        error = ConnectionError("Connection timed out")
        error_type, message, suggestion = _format_connection_error(error)

        assert error_type == "Request Timeout"
        assert "timed out" in message
        assert suggestion == ERROR_SUGGESTIONS["timeout"]

    def test_generic_connection_error(self) -> None:
        """Test formatting generic connection errors."""
        error = ConnectionError("Network unreachable")
        error_type, message, suggestion = _format_connection_error(error)

        assert error_type == "Connection Error"
        assert "Network unreachable" in message
        assert suggestion == ERROR_SUGGESTIONS["connection"]


class TestFormatApiError:
    """Tests for _format_api_error function."""

    def test_auth_error_401(self) -> None:
        """Test formatting 401 authentication error."""
        error = APIError("Unauthorized", status_code=401)
        error_type, message, suggestion = _format_api_error(error)

        assert error_type == "Authentication Failed"
        assert suggestion == ERROR_SUGGESTIONS["auth"]

    def test_auth_error_403(self) -> None:
        """Test formatting 403 forbidden error."""
        error = APIError("Forbidden", status_code=403)
        error_type, message, suggestion = _format_api_error(error)

        assert error_type == "Authentication Failed"
        assert suggestion == ERROR_SUGGESTIONS["auth"]

    def test_not_found_error(self) -> None:
        """Test formatting 404 not found error."""
        error = APIError("Not found", status_code=404)
        error_type, message, suggestion = _format_api_error(error)

        assert error_type == "Resource Not Found"
        assert suggestion == ERROR_SUGGESTIONS["not_found"]

    def test_server_error(self) -> None:
        """Test formatting 500+ server errors."""
        error = APIError("Internal server error", status_code=500)
        error_type, message, suggestion = _format_api_error(error)

        assert error_type == "Server Error"
        assert suggestion == ERROR_SUGGESTIONS["server_error"]

    def test_generic_api_error(self) -> None:
        """Test formatting generic API error without status code."""
        error = APIError("API error")
        error_type, message, suggestion = _format_api_error(error)

        assert error_type == "API Error"
        assert "try again" in suggestion.lower()


class TestBatchResult:
    """Tests for BatchResult class."""

    def test_init_empty(self) -> None:
        """Test BatchResult initializes with empty lists."""
        result = BatchResult()
        assert result.succeeded == []
        assert result.failed == []

    def test_add_success(self) -> None:
        """Test adding successful items."""
        result = BatchResult()
        result.add_success({"file": "test.jpg", "resource_id": 123})

        assert len(result.succeeded) == 1
        assert result.succeeded[0]["file"] == "test.jpg"

    def test_add_failure(self) -> None:
        """Test adding failed items."""
        result = BatchResult()
        result.add_failure("test.jpg", "File not found", path="/tmp/test.jpg")

        assert len(result.failed) == 1
        assert result.failed[0]["id"] == "test.jpg"
        assert result.failed[0]["error"] == "File not found"
        assert result.failed[0]["path"] == "/tmp/test.jpg"

    def test_has_failures_true(self) -> None:
        """Test has_failures returns True when there are failures."""
        result = BatchResult()
        result.add_failure("test.jpg", "Error")

        assert result.has_failures is True

    def test_has_failures_false(self) -> None:
        """Test has_failures returns False when no failures."""
        result = BatchResult()
        result.add_success({"file": "test.jpg"})

        assert result.has_failures is False

    def test_all_failed_true(self) -> None:
        """Test all_failed returns True when only failures exist."""
        result = BatchResult()
        result.add_failure("test.jpg", "Error")

        assert result.all_failed is True

    def test_all_failed_false_with_success(self) -> None:
        """Test all_failed returns False when some succeeded."""
        result = BatchResult()
        result.add_success({"file": "test1.jpg"})
        result.add_failure("test2.jpg", "Error")

        assert result.all_failed is False

    def test_all_failed_false_empty(self) -> None:
        """Test all_failed returns False when empty."""
        result = BatchResult()
        assert result.all_failed is False

    def test_total(self) -> None:
        """Test total count of operations."""
        result = BatchResult()
        result.add_success({"file": "test1.jpg"})
        result.add_success({"file": "test2.jpg"})
        result.add_failure("test3.jpg", "Error")

        assert result.total == 3

    def test_to_dict_success(self) -> None:
        """Test to_dict with successful items."""
        result = BatchResult()
        result.add_success({"file": "test.jpg", "resource_id": 123})

        d = result.to_dict()
        assert d["status"] == "success"
        assert d["succeeded"] == 1
        assert d["failed"] == 0
        assert len(d["items"]) == 1
        assert d["errors"] == []

    def test_to_dict_all_failed(self) -> None:
        """Test to_dict when all operations failed."""
        result = BatchResult()
        result.add_failure("test.jpg", "Error")

        d = result.to_dict()
        assert d["status"] == "error"
        assert d["succeeded"] == 0
        assert d["failed"] == 1

    def test_to_dict_partial_failure(self) -> None:
        """Test to_dict with partial failure."""
        result = BatchResult()
        result.add_success({"file": "test1.jpg"})
        result.add_failure("test2.jpg", "Error")

        d = result.to_dict()
        # Partial success still counts as success
        assert d["status"] == "success"
        assert d["succeeded"] == 1
        assert d["failed"] == 1

    def test_get_exit_code_success(self) -> None:
        """Test exit code is 0 when at least one succeeded."""
        result = BatchResult()
        result.add_success({"file": "test.jpg"})

        assert result.get_exit_code() == 0

    def test_get_exit_code_partial_failure(self) -> None:
        """Test exit code is 0 with partial failure."""
        result = BatchResult()
        result.add_success({"file": "test1.jpg"})
        result.add_failure("test2.jpg", "Error")

        assert result.get_exit_code() == 0

    def test_get_exit_code_all_failed(self) -> None:
        """Test exit code is 1 when all failed."""
        result = BatchResult()
        result.add_failure("test.jpg", "Error")

        assert result.get_exit_code() == 1

    def test_output_json(self) -> None:
        """Test output_json produces valid JSON."""
        result = BatchResult()
        result.add_success({"file": "test.jpg"})

        with patch("click.echo") as mock_echo:
            result.output_json()

            call_args = mock_echo.call_args[0][0]
            output = json.loads(call_args)
            assert output["status"] == "success"

    def test_output_respects_context(self, mock_click_context: click.Context) -> None:
        """Test output method respects json_output setting."""
        result = BatchResult()
        result.add_success({"file": "test.jpg"})

        with patch.object(result, "print_summary") as mock_summary:
            with patch.object(result, "output_json") as mock_json:
                result.output(mock_click_context, "file")

                # json_output is False in mock_click_context by default
                mock_summary.assert_called_once()
                mock_json.assert_not_called()

    def test_print_summary(self, mock_click_context: click.Context) -> None:
        """Test print_summary outputs correct format."""
        result = BatchResult()
        result.add_success({"file": "test1.jpg"})
        result.add_failure("test2.jpg", "Download failed")

        with patch("resourcespace_cli.utils.errors.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            result.print_summary(mock_click_context, "file")

            # Verify console.print was called
            assert mock_console.print.called
