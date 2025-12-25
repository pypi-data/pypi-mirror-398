"""Tests for ResourceSpace API client."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import httpx
import pytest

from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import Config
from resourcespace_cli.exceptions import (
    APIError,
    ConfigurationError,
    ConnectionError,
    DownloadError,
    UploadError,
)


class TestResourceSpaceClientInit:
    """Tests for ResourceSpaceClient initialization."""

    def test_init_with_complete_config(self, mock_config: Config) -> None:
        """Test client initializes with complete config."""
        client = ResourceSpaceClient(mock_config)

        assert client.api_url == mock_config.api_url
        assert client.api_key == mock_config.api_key
        assert client.user == mock_config.user
        client.close()

    def test_init_with_incomplete_config_raises_error(
        self, incomplete_config: Config
    ) -> None:
        """Test client raises ConfigurationError with incomplete config."""
        with pytest.raises(ConfigurationError) as exc_info:
            ResourceSpaceClient(incomplete_config)

        assert "Configuration is incomplete" in str(exc_info.value)

    def test_context_manager(self, mock_config: Config) -> None:
        """Test client works as context manager."""
        with ResourceSpaceClient(mock_config) as client:
            assert client.api_url == mock_config.api_url

        # Client should be closed after context


class TestSignQuery:
    """Tests for _sign_query method."""

    def test_sign_query_produces_sha256(self, mock_config: Config) -> None:
        """Test that _sign_query produces valid SHA256 hash."""
        with ResourceSpaceClient(mock_config) as client:
            query = "user=testuser&function=get_resource"
            signature = client._sign_query(query)

            # Verify it's a valid hex string of correct length
            assert len(signature) == 64
            assert all(c in "0123456789abcdef" for c in signature)

    def test_sign_query_correct_algorithm(self, mock_config: Config) -> None:
        """Test that signature matches expected SHA256 output."""
        with ResourceSpaceClient(mock_config) as client:
            query = "user=testuser&function=test"
            signature = client._sign_query(query)

            # Manually calculate expected signature
            expected = hashlib.sha256(
                f"{mock_config.api_key}{query}".encode()
            ).hexdigest()

            assert signature == expected


class TestBuildQuery:
    """Tests for _build_query method."""

    def test_build_query_basic(self, mock_config: Config) -> None:
        """Test building a basic query string."""
        with ResourceSpaceClient(mock_config) as client:
            query = client._build_query("get_resource", resource=123)

            assert "user=testuser" in query
            assert "function=get_resource" in query
            assert "resource=123" in query

    def test_build_query_multiple_params(self, mock_config: Config) -> None:
        """Test building query with multiple parameters."""
        with ResourceSpaceClient(mock_config) as client:
            query = client._build_query(
                "search",
                search="photos",
                restypes="1,2",
            )

            assert "function=search" in query
            assert "search=photos" in query
            assert "restypes=1" in query or "restypes=1%2C2" in query


class TestCall:
    """Tests for call method."""

    def test_call_successful(self, mock_config: Config) -> None:
        """Test successful API call."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"ref": "123", "field8": "Test"}
            mock_response.raise_for_status = MagicMock()

            with patch.object(client._client, "get", return_value=mock_response):
                result = client.call("get_resource", resource=123)

            assert result == {"ref": "123", "field8": "Test"}

    def test_call_timeout_raises_connection_error(self, mock_config: Config) -> None:
        """Test timeout raises ConnectionError."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "get",
                side_effect=httpx.TimeoutException("Timeout"),
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    client.call("get_resource", resource=123)

                assert "timed out" in str(exc_info.value).lower()

    def test_call_connect_error_raises_connection_error(
        self, mock_config: Config
    ) -> None:
        """Test connection failure raises ConnectionError."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "get",
                side_effect=httpx.ConnectError("Connection refused"),
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    client.call("get_resource", resource=123)

                assert "Could not connect" in str(exc_info.value)

    def test_call_http_error_raises_api_error(self, mock_config: Config) -> None:
        """Test HTTP error raises APIError with status code."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not found"

            with patch.object(
                client._client,
                "get",
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=MagicMock(),
                    response=mock_response,
                ),
            ):
                with pytest.raises(APIError) as exc_info:
                    client.call("get_resource", resource=123)

                assert exc_info.value.status_code == 404

    def test_call_invalid_json_raises_api_error(self, mock_config: Config) -> None:
        """Test invalid JSON response raises APIError."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")

            with patch.object(client._client, "get", return_value=mock_response):
                with pytest.raises(APIError) as exc_info:
                    client.call("get_resource", resource=123)

                assert "Invalid JSON" in str(exc_info.value)

    def test_call_request_error_raises_connection_error(
        self, mock_config: Config
    ) -> None:
        """Test generic request error raises ConnectionError."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "get",
                side_effect=httpx.RequestError("Request failed"),
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    client.call("get_resource", resource=123)

                assert "Request failed" in str(exc_info.value)


class TestGetUserCollections:
    """Tests for get_user_collections method."""

    def test_get_user_collections_success(
        self, mock_config: Config, sample_collection_response: list[dict[str, Any]]
    ) -> None:
        """Test successful collection retrieval."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client, "call", return_value=sample_collection_response
            ):
                result = client.get_user_collections()

            assert len(result) == 2
            assert result[0]["name"] == "Collection A"


class TestDownloadStream:
    """Tests for download_stream method."""

    def test_download_stream_success(self, mock_config: Config) -> None:
        """Test successful streaming download."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.headers = {"content-length": "1024"}
            mock_response.raise_for_status = MagicMock()
            mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2"]

            with patch.object(
                client._client,
                "stream",
                return_value=MagicMock(__enter__=lambda s: mock_response, __exit__=lambda *a: None),
            ):
                chunks = list(client.download_stream("https://example.com/file.jpg"))

            assert len(chunks) == 2
            assert chunks[0] == (b"chunk1", 1024)
            assert chunks[1] == (b"chunk2", 1024)

    def test_download_stream_no_content_length(self, mock_config: Config) -> None:
        """Test download without content-length header."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.headers = {}
            mock_response.raise_for_status = MagicMock()
            mock_response.iter_bytes.return_value = [b"chunk"]

            with patch.object(
                client._client,
                "stream",
                return_value=MagicMock(__enter__=lambda s: mock_response, __exit__=lambda *a: None),
            ):
                chunks = list(client.download_stream("https://example.com/file.jpg"))

            assert chunks[0] == (b"chunk", None)

    def test_download_stream_timeout_raises_connection_error(
        self, mock_config: Config
    ) -> None:
        """Test download timeout raises ConnectionError."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "stream",
                side_effect=httpx.TimeoutException("Timeout"),
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    list(client.download_stream("https://example.com/file.jpg"))

                assert "timed out" in str(exc_info.value).lower()

    def test_download_stream_connect_error_raises_connection_error(
        self, mock_config: Config
    ) -> None:
        """Test download connection failure raises ConnectionError."""
        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "stream",
                side_effect=httpx.ConnectError("Connection failed"),
            ):
                with pytest.raises(ConnectionError):
                    list(client.download_stream("https://example.com/file.jpg"))

    def test_download_stream_http_error_raises_download_error(
        self, mock_config: Config
    ) -> None:
        """Test download HTTP error raises DownloadError."""
        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 404

            with patch.object(
                client._client,
                "stream",
                side_effect=httpx.HTTPStatusError(
                    "Not found", request=MagicMock(), response=mock_response
                ),
            ):
                with pytest.raises(DownloadError) as exc_info:
                    list(client.download_stream("https://example.com/file.jpg"))

                assert "HTTP 404" in str(exc_info.value)


class TestUploadFile:
    """Tests for upload_file method."""

    def test_upload_file_success_true_response(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test successful upload with True response."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = True

            with patch.object(client._client, "post", return_value=mock_response):
                result = client.upload_file(123, test_file)

            assert result is True

    def test_upload_file_success_string_response(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test successful upload with 'true' string response."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = "true"

            with patch.object(client._client, "post", return_value=mock_response):
                result = client.upload_file(123, test_file)

            assert result is True

    def test_upload_file_api_error(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload with API error response."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = "Error: Invalid resource"

            with patch.object(client._client, "post", return_value=mock_response):
                with pytest.raises(UploadError) as exc_info:
                    client.upload_file(123, test_file)

                assert "Invalid resource" in str(exc_info.value)

    def test_upload_file_timeout_raises_connection_error(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload timeout raises ConnectionError."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "post",
                side_effect=httpx.TimeoutException("Timeout"),
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    client.upload_file(123, test_file)

                assert "timed out" in str(exc_info.value).lower()

    def test_upload_file_connect_error_raises_connection_error(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload connection failure raises ConnectionError."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            with patch.object(
                client._client,
                "post",
                side_effect=httpx.ConnectError("Connection failed"),
            ):
                with pytest.raises(ConnectionError):
                    client.upload_file(123, test_file)

    def test_upload_file_http_error_raises_upload_error(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload HTTP error raises UploadError."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 500

            with patch.object(
                client._client,
                "post",
                side_effect=httpx.HTTPStatusError(
                    "Server error", request=MagicMock(), response=mock_response
                ),
            ):
                with pytest.raises(UploadError) as exc_info:
                    client.upload_file(123, test_file)

                assert "HTTP 500" in str(exc_info.value)

    def test_upload_file_os_error_raises_upload_error(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload with missing file raises UploadError."""
        missing_file = tmp_path / "nonexistent.jpg"

        with ResourceSpaceClient(mock_config) as client:
            with pytest.raises(UploadError) as exc_info:
                client.upload_file(123, missing_file)

            assert "Cannot read file" in str(exc_info.value)

    def test_upload_file_with_options(
        self, mock_config: Config, tmp_path: Path
    ) -> None:
        """Test upload with no_exif and revert options."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        with ResourceSpaceClient(mock_config) as client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = True

            with patch.object(client._client, "post", return_value=mock_response) as mock_post:
                client.upload_file(123, test_file, no_exif=True, revert=True)

                # Check the URL contains the options
                call_url = mock_post.call_args[0][0]
                assert "no_exif=true" in call_url
                assert "revert=true" in call_url
