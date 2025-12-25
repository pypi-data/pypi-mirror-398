"""Tests for output formatting utilities."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import click
import pytest
from rich.table import Table

from resourcespace_cli.output import (
    get_console,
    print_dim,
    print_error,
    print_success,
    print_table,
)


class TestGetConsole:
    """Tests for get_console function."""

    def test_without_context(self) -> None:
        """Test get_console without Click context."""
        console = get_console()
        assert console is not None
        # Default should have color enabled
        assert console.no_color is False

    def test_with_context_no_color_false(self) -> None:
        """Test get_console with no_color=False."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"no_color": False}

        console = get_console(ctx)
        assert console.no_color is False

    def test_with_context_no_color_true(self) -> None:
        """Test get_console with no_color=True."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"no_color": True}

        console = get_console(ctx)
        assert console.no_color is True

    def test_with_context_missing_no_color(self) -> None:
        """Test get_console when no_color key is missing."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {}

        console = get_console(ctx)
        # Should default to False (color enabled)
        assert console.no_color is False


class TestPrintError:
    """Tests for print_error function."""

    def test_print_error_text_mode(self) -> None:
        """Test error output in text mode."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"json_output": False, "no_color": True}

        with patch("resourcespace_cli.output.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            print_error(ctx, "Something went wrong")

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Error:" in call_args
            assert "Something went wrong" in call_args

    def test_print_error_text_mode_custom_type(self) -> None:
        """Test error output with custom error type."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"json_output": False, "no_color": True}

        with patch("resourcespace_cli.output.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            print_error(ctx, "Config missing", error_type="Configuration Error")

            call_args = mock_console.print.call_args[0][0]
            assert "Configuration Error:" in call_args

    def test_print_error_json_mode(self) -> None:
        """Test error output in JSON mode."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"json_output": True}

        with patch("click.echo") as mock_echo:
            print_error(ctx, "Something went wrong")

            mock_echo.assert_called_once()
            output = json.loads(mock_echo.call_args[0][0])
            assert output["status"] == "error"
            assert output["message"] == "Something went wrong"


class TestPrintSuccess:
    """Tests for print_success function."""

    def test_print_success(self) -> None:
        """Test success message output."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"no_color": True}

        with patch("resourcespace_cli.output.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            print_success(ctx, "Operation completed")

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Operation completed" in call_args
            assert "[green]" in call_args


class TestPrintTable:
    """Tests for print_table function."""

    def test_print_table(self) -> None:
        """Test table output."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"no_color": True}

        table = Table(title="Test Table")
        table.add_column("Name")
        table.add_row("Value")

        with patch("resourcespace_cli.output.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            print_table(ctx, table)

            mock_console.print.assert_called_once_with(table)


class TestPrintDim:
    """Tests for print_dim function."""

    def test_print_dim(self) -> None:
        """Test dim message output."""
        ctx = MagicMock(spec=click.Context)
        ctx.obj = {"no_color": True}

        with patch("resourcespace_cli.output.get_console") as mock_get_console:
            mock_console = MagicMock()
            mock_get_console.return_value = mock_console

            print_dim(ctx, "Hint: Try this")

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Hint: Try this" in call_args
            assert "[dim]" in call_args
