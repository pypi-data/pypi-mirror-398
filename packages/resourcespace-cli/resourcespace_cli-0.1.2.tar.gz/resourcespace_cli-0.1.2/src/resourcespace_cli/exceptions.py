"""Custom exceptions for ResourceSpace CLI."""

from __future__ import annotations


class ResourceSpaceError(Exception):
    """Base exception for ResourceSpace CLI errors."""

    pass


class ConfigurationError(ResourceSpaceError):
    """Raised when there is a configuration problem."""

    pass


class ValidationError(ResourceSpaceError):
    """Raised when input validation fails.

    Contains user-friendly error messages from Pydantic validation.
    """

    pass


class ConnectionError(ResourceSpaceError):
    """Raised when a connection to the ResourceSpace server fails.

    This includes network errors, DNS failures, timeouts, etc.
    """

    pass


class APIError(ResourceSpaceError):
    """Raised when the ResourceSpace API returns an error.

    Attributes:
        status_code: HTTP status code if applicable.
        response_body: Raw response body if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        """Initialize API error with optional HTTP details.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
            response_body: Raw response body if available.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class DownloadError(ResourceSpaceError):
    """Raised when a download operation fails."""

    pass


class UploadError(ResourceSpaceError):
    """Raised when an upload operation fails."""

    pass
