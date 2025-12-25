"""Tests for custom exception classes."""

from __future__ import annotations

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


class TestResourceSpaceError:
    """Tests for base ResourceSpaceError."""

    def test_can_raise(self) -> None:
        """Test that ResourceSpaceError can be raised."""
        with pytest.raises(ResourceSpaceError):
            raise ResourceSpaceError("Test error")

    def test_message(self) -> None:
        """Test that error message is preserved."""
        error = ResourceSpaceError("Test message")
        assert str(error) == "Test message"

    def test_inherits_from_exception(self) -> None:
        """Test that it inherits from Exception."""
        assert issubclass(ResourceSpaceError, Exception)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_can_raise(self) -> None:
        """Test that ConfigurationError can be raised."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Missing config")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(ConfigurationError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise ConfigurationError("Test")


class TestValidationError:
    """Tests for ValidationError."""

    def test_can_raise(self) -> None:
        """Test that ValidationError can be raised."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(ValidationError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise ValidationError("Test")


class TestConnectionError:
    """Tests for ConnectionError."""

    def test_can_raise(self) -> None:
        """Test that ConnectionError can be raised."""
        with pytest.raises(ConnectionError):
            raise ConnectionError("Network error")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(ConnectionError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise ConnectionError("Test")


class TestAPIError:
    """Tests for APIError."""

    def test_can_raise(self) -> None:
        """Test that APIError can be raised."""
        with pytest.raises(APIError):
            raise APIError("API failed")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(APIError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise APIError("Test")

    def test_message_only(self) -> None:
        """Test APIError with message only."""
        error = APIError("API failed")
        assert str(error) == "API failed"
        assert error.status_code is None
        assert error.response_body is None

    def test_with_status_code(self) -> None:
        """Test APIError with status code."""
        error = APIError("Not found", status_code=404)
        assert str(error) == "Not found"
        assert error.status_code == 404
        assert error.response_body is None

    def test_with_response_body(self) -> None:
        """Test APIError with response body."""
        error = APIError("Server error", status_code=500, response_body='{"error": "details"}')
        assert str(error) == "Server error"
        assert error.status_code == 500
        assert error.response_body == '{"error": "details"}'

    def test_all_attributes(self) -> None:
        """Test APIError with all attributes."""
        error = APIError(
            message="Request failed",
            status_code=400,
            response_body="Bad request",
        )
        assert str(error) == "Request failed"
        assert error.status_code == 400
        assert error.response_body == "Bad request"


class TestDownloadError:
    """Tests for DownloadError."""

    def test_can_raise(self) -> None:
        """Test that DownloadError can be raised."""
        with pytest.raises(DownloadError):
            raise DownloadError("Download failed")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(DownloadError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise DownloadError("Test")


class TestUploadError:
    """Tests for UploadError."""

    def test_can_raise(self) -> None:
        """Test that UploadError can be raised."""
        with pytest.raises(UploadError):
            raise UploadError("Upload failed")

    def test_inherits_from_base(self) -> None:
        """Test that it inherits from ResourceSpaceError."""
        assert issubclass(UploadError, ResourceSpaceError)

    def test_catchable_as_base(self) -> None:
        """Test that it can be caught as ResourceSpaceError."""
        with pytest.raises(ResourceSpaceError):
            raise UploadError("Test")


class TestExceptionHierarchy:
    """Tests for the exception hierarchy as a whole."""

    def test_all_exceptions_catchable_as_base(self) -> None:
        """Test all custom exceptions can be caught as ResourceSpaceError."""
        exceptions = [
            ConfigurationError("test"),
            ValidationError("test"),
            ConnectionError("test"),
            APIError("test"),
            DownloadError("test"),
            UploadError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, ResourceSpaceError)

    def test_exceptions_are_distinct(self) -> None:
        """Test that different exception types are distinguishable."""
        config_error = ConfigurationError("config")
        api_error = APIError("api")

        assert type(config_error) != type(api_error)
        assert isinstance(config_error, ConfigurationError)
        assert not isinstance(config_error, APIError)
        assert isinstance(api_error, APIError)
        assert not isinstance(api_error, ConfigurationError)
