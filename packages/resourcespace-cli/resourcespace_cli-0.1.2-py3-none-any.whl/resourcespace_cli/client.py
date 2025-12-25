"""ResourceSpace API client."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from resourcespace_cli.config import Config
from resourcespace_cli.exceptions import (
    APIError,
    ConfigurationError,
    ConnectionError,
    DownloadError,
    UploadError,
)


class ResourceSpaceClient:
    """Client for interacting with the ResourceSpace API."""

    def __init__(self, config: Config) -> None:
        """Initialize the client with configuration.

        Args:
            config: Configuration object with API credentials.

        Raises:
            ConfigurationError: If configuration is incomplete.
        """
        if not config.is_complete():
            raise ConfigurationError(
                "Configuration is incomplete. Run 'rs config get' to see missing values."
            )

        self.api_url = config.api_url
        self.api_key = config.api_key
        self.user = config.user
        self._client = httpx.Client(timeout=30.0)

    def _sign_query(self, query: str) -> str:
        """Generate SHA256 signature for API request.

        Args:
            query: The query string to sign (without the sign parameter).

        Returns:
            SHA256 hexadecimal hash of api_key + query.
        """
        return hashlib.sha256(f"{self.api_key}{query}".encode()).hexdigest()

    def _build_query(self, function: str, **params: Any) -> str:
        """Build the query string for an API request.

        Args:
            function: The API function name.
            **params: Additional parameters for the function.

        Returns:
            URL-encoded query string.
        """
        query_params = {"user": self.user, "function": function, **params}
        return urlencode(query_params)

    def call(self, function: str, **params: Any) -> Any:
        """Make an API call to ResourceSpace.

        Args:
            function: The API function name.
            **params: Additional parameters for the function.

        Returns:
            Parsed JSON response from the API.

        Raises:
            APIError: If the API returns an error or request fails.
        """
        query = self._build_query(function, **params)
        sign = self._sign_query(query)

        url = f"{self.api_url}?{query}&sign={sign}"

        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            raise ConnectionError(
                "Request timed out. The server may be slow or unreachable."
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Could not connect to {self.api_url}. "
                "Please check your network connection and server URL."
            ) from e
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"API request failed: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500] if e.response.text else None,
            ) from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}") from e

    def get_user_collections(self) -> list[dict[str, Any]]:
        """Get all collections for the authenticated user.

        Returns:
            List of collection dictionaries with ref, name, and count fields.
        """
        result: list[dict[str, Any]] = self.call("get_user_collections")
        return result

    def download_stream(self, url: str) -> Iterator[tuple[bytes, int | None]]:
        """Stream download content from a URL.

        Args:
            url: The URL to download from.

        Yields:
            Tuple of (chunk_bytes, total_size_or_none).

        Raises:
            DownloadError: If the download fails.
        """
        try:
            with self._client.stream("GET", url) as response:
                response.raise_for_status()
                total = response.headers.get("content-length")
                total_size = int(total) if total else None

                for chunk in response.iter_bytes(chunk_size=8192):
                    yield chunk, total_size

        except httpx.TimeoutException as e:
            raise ConnectionError(
                "Download timed out. The server may be slow or unreachable."
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionError(
                "Could not connect for download. "
                "Please check your network connection."
            ) from e
        except httpx.HTTPStatusError as e:
            raise DownloadError(
                f"Download failed: HTTP {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Download failed: {e}") from e

    def upload_file(
        self,
        resource_id: int,
        filepath: Path,
        *,
        no_exif: bool = False,
        revert: bool = False,
    ) -> bool:
        """Upload a file to an existing resource.

        Args:
            resource_id: The resource ID to upload to.
            filepath: Path to the file to upload.
            no_exif: If True, do not extract EXIF data.
            revert: If True, revert to the original file.

        Returns:
            True if upload succeeded.

        Raises:
            UploadError: If the upload fails.
        """
        query = self._build_query(
            "upload_file",
            resource=resource_id,
            no_exif="true" if no_exif else "false",
            revert="true" if revert else "false",
        )
        sign = self._sign_query(query)
        url = f"{self.api_url}?{query}&sign={sign}"

        try:
            with open(filepath, "rb") as f:
                files = {"userfile": (filepath.name, f)}
                response = self._client.post(url, files=files)
                response.raise_for_status()

                result = response.json()
                if result is True or result == "true":
                    return True
                # API may return error message
                raise UploadError(f"Upload failed: {result}")

        except httpx.TimeoutException as e:
            raise ConnectionError(
                "Upload timed out. The server may be slow or unreachable."
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionError(
                "Could not connect for upload. "
                "Please check your network connection."
            ) from e
        except httpx.HTTPStatusError as e:
            raise UploadError(f"Upload failed: HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Upload failed: {e}") from e
        except OSError as e:
            raise UploadError(f"Cannot read file '{filepath}': {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> ResourceSpaceClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
