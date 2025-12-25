"""Centralized error handling utilities for ResourceSpace CLI."""

from __future__ import annotations

import json
from typing import Any, NoReturn

import click

from resourcespace_cli.output import get_console

# Error message templates with helpful suggestions
ERROR_SUGGESTIONS: dict[str, str] = {
    "connection": (
        "Please check your network connection and try again. "
        "Verify that the ResourceSpace server is reachable."
    ),
    "timeout": (
        "The server took too long to respond. "
        "Please try again later or check if the server is under heavy load."
    ),
    "config_missing": (
        "Run 'rs config set <key> <value>' to configure the CLI. "
        "Required: url, key, user"
    ),
    "auth": (
        "Verify your API key and username are correct. "
        "Run 'rs config get' to check current settings."
    ),
    "not_found": "The requested resource does not exist or you don't have permission to access it.",
    "server_error": (
        "The ResourceSpace server encountered an error. "
        "Please try again later or contact your administrator."
    ),
    "file_not_found": "Please check that the file path is correct and the file exists.",
    "permission_denied": "Please check that you have permission to access the file or directory.",
}


def handle_exception(ctx: click.Context, error: Exception) -> NoReturn:
    """Handle exceptions with user-friendly messages.

    Provides centralized exception handling that:
    - Maps exception types to helpful messages
    - Formats output consistently (text/JSON)
    - Includes suggestions for resolution
    - Exits with appropriate code (always 1 for errors)

    Args:
        ctx: Click context.
        error: The exception to handle.

    Raises:
        SystemExit: Always exits with code 1.
    """
    from resourcespace_cli.exceptions import (
        APIError,
        ConfigurationError,
        ConnectionError,
        DownloadError,
        ResourceSpaceError,
        UploadError,
        ValidationError,
    )

    error_type: str
    message: str
    suggestion: str | None = None

    if isinstance(error, ValidationError):
        error_type = "Validation Error"
        message = str(error)
        # Validation errors are self-explanatory, no suggestion needed
    elif isinstance(error, ConfigurationError):
        error_type = "Configuration Error"
        message = str(error)
        suggestion = ERROR_SUGGESTIONS["config_missing"]
    elif isinstance(error, ConnectionError):
        error_type, message, suggestion = _format_connection_error(error)
    elif isinstance(error, APIError):
        error_type, message, suggestion = _format_api_error(error)
    elif isinstance(error, DownloadError):
        error_type = "Download Error"
        message = str(error)
        suggestion = "Please try again. If the problem persists, verify the resource exists."
    elif isinstance(error, UploadError):
        error_type = "Upload Error"
        message = str(error)
        suggestion = "Please check the file and try again."
    elif isinstance(error, ResourceSpaceError):
        error_type = "Error"
        message = str(error)
    else:
        # Unexpected exception - still handle gracefully
        error_type = "Unexpected Error"
        message = str(error)
        suggestion = "If this problem persists, please report it as a bug."

    _print_error_with_suggestion(ctx, message, error_type, suggestion)
    ctx.exit(1)


def _format_connection_error(error: Exception) -> tuple[str, str, str]:
    """Format connection-related errors with helpful suggestions.

    Args:
        error: The connection error.

    Returns:
        Tuple of (error_type, message, suggestion).
    """
    message = str(error)

    if "timeout" in message.lower() or "timed out" in message.lower():
        return "Request Timeout", message, ERROR_SUGGESTIONS["timeout"]

    return "Connection Error", message, ERROR_SUGGESTIONS["connection"]


def _format_api_error(error: Any) -> tuple[str, str, str]:
    """Format API errors with context-aware suggestions.

    Args:
        error: The API error (with optional status_code attribute).

    Returns:
        Tuple of (error_type, message, suggestion).
    """
    message = str(error)
    status_code = getattr(error, "status_code", None)

    if status_code == 401 or status_code == 403:
        return "Authentication Failed", message, ERROR_SUGGESTIONS["auth"]
    elif status_code == 404:
        return "Resource Not Found", message, ERROR_SUGGESTIONS["not_found"]
    elif status_code is not None and status_code >= 500:
        return "Server Error", message, ERROR_SUGGESTIONS["server_error"]

    return "API Error", message, "Please try again or check your request parameters."


def _print_error_with_suggestion(
    ctx: click.Context,
    message: str,
    error_type: str = "Error",
    suggestion: str | None = None,
) -> None:
    """Print error with optional suggestion line.

    Args:
        ctx: Click context.
        message: The error message.
        error_type: Type of error for the prefix.
        suggestion: Optional suggestion for resolution.
    """
    json_output = ctx.obj.get("json_output", False)

    if json_output:
        output: dict[str, Any] = {
            "status": "error",
            "error_type": error_type,
            "message": message,
        }
        if suggestion:
            output["suggestion"] = suggestion
        click.echo(json.dumps(output))
    else:
        console = get_console(ctx)
        console.print(f"[red]{error_type}:[/red] {message}")
        if suggestion:
            console.print(f"[dim]Suggestion: {suggestion}[/dim]")


class BatchResult:
    """Track results of batch operations with partial failure support.

    Use this class to track the outcomes of batch operations like
    downloading or uploading multiple files.
    """

    def __init__(self) -> None:
        """Initialize empty result tracking."""
        self.succeeded: list[dict[str, Any]] = []
        self.failed: list[dict[str, Any]] = []

    def add_success(self, item: dict[str, Any]) -> None:
        """Record a successful operation.

        Args:
            item: Dictionary with operation details (e.g., file, resource_id).
        """
        self.succeeded.append(item)

    def add_failure(self, item_id: Any, error: str, **extra: Any) -> None:
        """Record a failed operation.

        Args:
            item_id: Identifier for the failed item (file path, resource ID, etc.).
            error: Error message describing the failure.
            **extra: Additional context to include in the failure record.
        """
        self.failed.append({"id": str(item_id), "error": error, **extra})

    @property
    def has_failures(self) -> bool:
        """Check if any operations failed."""
        return len(self.failed) > 0

    @property
    def all_failed(self) -> bool:
        """Check if all operations failed."""
        return len(self.succeeded) == 0 and len(self.failed) > 0

    @property
    def total(self) -> int:
        """Get total number of operations."""
        return len(self.succeeded) + len(self.failed)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output.

        Returns:
            Dictionary with status, counts, and detailed results.
        """
        status = "error" if self.all_failed else "success"
        return {
            "status": status,
            "succeeded": len(self.succeeded),
            "failed": len(self.failed),
            "items": self.succeeded,
            "errors": self.failed,
        }

    def print_summary(
        self,
        ctx: click.Context,
        item_type: str = "item",
        show_details: bool = True,
    ) -> None:
        """Print human-readable summary of results.

        Args:
            ctx: Click context.
            item_type: Type of item for display (e.g., "file", "resource").
            show_details: Whether to show details of failed items.
        """
        console = get_console(ctx)
        plural = "s" if self.total != 1 else ""

        console.print()
        if self.succeeded:
            console.print(f"[green]Succeeded:[/green] {len(self.succeeded)} {item_type}{plural}")
        if self.failed:
            console.print(f"[red]Failed:[/red] {len(self.failed)} {item_type}{plural}")
            if show_details:
                for failure in self.failed:
                    console.print(f"  [dim]{failure['id']}: {failure['error']}[/dim]")

    def get_exit_code(self) -> int:
        """Get appropriate exit code based on results.

        Returns:
            0 if at least one succeeded, 1 if all failed.
        """
        return 1 if self.all_failed else 0

    def output_json(self) -> None:
        """Output results as JSON."""
        click.echo(json.dumps(self.to_dict(), indent=2))

    def output(self, ctx: click.Context, item_type: str = "item") -> None:
        """Output results in appropriate format based on context.

        Args:
            ctx: Click context.
            item_type: Type of item for display.
        """
        json_output = ctx.obj.get("json_output", False)
        if json_output:
            self.output_json()
        else:
            self.print_summary(ctx, item_type)
