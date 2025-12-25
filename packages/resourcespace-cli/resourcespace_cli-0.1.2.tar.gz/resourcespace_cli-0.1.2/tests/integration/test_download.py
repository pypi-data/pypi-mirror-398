"""Integration tests for the download command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestDownloadSingle:
    """Integration tests for single resource download."""

    def test_download_single_resource(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_resource_data: dict[str, Any],
        sample_download_url: str,
        sample_file_content: bytes,
    ) -> None:
        """Test downloading a single resource by ID."""
        # Mock get_resource_data
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*resource=101.*"),
            json=sample_resource_data,
        )

        # Mock get_resource_path
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*resource=101.*"),
            json=sample_download_url,
        )

        # Mock file download
        httpx_mock.add_response(
            url=sample_download_url,
            content=sample_file_content,
            headers={"content-length": str(len(sample_file_content))},
        )

        result = cli_runner.invoke(main, ["download", "101", "--output", str(tmp_path)])

        assert result.exit_code == 0
        assert "Downloaded" in result.output
        # Verify file was created (exclude .env file from integration_env fixture)
        downloaded_files = [f for f in tmp_path.glob("*") if f.name != ".env"]
        assert len(downloaded_files) == 1

    def test_download_single_resource_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_resource_data: dict[str, Any],
        sample_download_url: str,
        sample_file_content: bytes,
    ) -> None:
        """Test download with JSON output."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json=sample_download_url,
        )
        httpx_mock.add_response(
            url=sample_download_url,
            content=sample_file_content,
        )

        result = cli_runner.invoke(
            main, ["--json", "download", "101", "--output", str(tmp_path)]
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["resource_id"] == 101

    def test_download_to_stdout(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
        sample_download_url: str,
        sample_file_content: bytes,
    ) -> None:
        """Test streaming download to stdout."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json=sample_download_url,
        )
        httpx_mock.add_response(
            url=sample_download_url,
            content=sample_file_content,
        )

        result = cli_runner.invoke(main, ["download", "101", "--stdout"])

        assert result.exit_code == 0

    def test_download_creates_output_directory(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_resource_data: dict[str, Any],
        sample_download_url: str,
        sample_file_content: bytes,
    ) -> None:
        """Test that download creates output directory if it doesn't exist."""
        new_dir = tmp_path / "new_downloads"
        assert not new_dir.exists()

        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json=sample_download_url,
        )
        httpx_mock.add_response(
            url=sample_download_url,
            content=sample_file_content,
        )

        result = cli_runner.invoke(main, ["download", "101", "--output", str(new_dir)])

        assert result.exit_code == 0
        assert new_dir.exists()


class TestDownloadBatch:
    """Integration tests for batch download via search."""

    def test_download_batch_via_search(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_search_results: list[dict[str, Any]],
        sample_file_content: bytes,
    ) -> None:
        """Test batch download using search query."""
        # Mock search
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=sample_search_results,
        )

        # Mock get_resource_path for each result
        for res in sample_search_results:
            ref = res["ref"]
            url = f"https://resourcespace.example.com/filestore/{ref}/file.jpg"
            httpx_mock.add_response(
                url=re.compile(rf".*function=get_resource_path.*resource={ref}.*"),
                json=url,
            )
            httpx_mock.add_response(
                url=url,
                content=sample_file_content,
            )

        result = cli_runner.invoke(
            main, ["download", "--search", "landscape", "--output", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Succeeded" in result.output

    def test_download_batch_empty_search(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test batch download when search returns no results."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=[],
        )

        result = cli_runner.invoke(
            main, ["download", "--search", "nonexistent", "--output", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "No resources found" in result.output

    def test_download_batch_partial_failure(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_search_results: list[dict[str, Any]],
        sample_file_content: bytes,
    ) -> None:
        """Test batch download with some failures."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=sample_search_results,
        )

        # First resource succeeds
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*resource=101.*"),
            json="https://resourcespace.example.com/filestore/101/file.jpg",
        )
        httpx_mock.add_response(
            url="https://resourcespace.example.com/filestore/101/file.jpg",
            content=sample_file_content,
        )

        # Second resource fails (404)
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*resource=102.*"),
            status_code=404,
            json={"error": "Resource not found"},
        )

        # Third resource succeeds
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*resource=103.*"),
            json="https://resourcespace.example.com/filestore/103/file.jpg",
        )
        httpx_mock.add_response(
            url="https://resourcespace.example.com/filestore/103/file.jpg",
            content=sample_file_content,
        )

        result = cli_runner.invoke(
            main, ["download", "--search", "landscape", "--output", str(tmp_path)]
        )

        # Should complete (not exit 1) because some succeeded
        assert "Succeeded" in result.output
        assert "Failed" in result.output

    def test_download_batch_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
        sample_search_results: list[dict[str, Any]],
        sample_file_content: bytes,
    ) -> None:
        """Test batch download with JSON output."""
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=sample_search_results[:1],  # Just one result
        )

        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*resource=101.*"),
            json="https://resourcespace.example.com/filestore/101/file.jpg",
        )
        httpx_mock.add_response(
            url="https://resourcespace.example.com/filestore/101/file.jpg",
            content=sample_file_content,
        )

        result = cli_runner.invoke(
            main,
            ["--json", "download", "--search", "landscape", "--output", str(tmp_path)],
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        # Check for succeeded items in the batch result
        assert "succeeded" in output or "success_count" in output or output.get("query") == "landscape"


class TestDownloadValidation:
    """Integration tests for download input validation."""

    def test_download_missing_resource_id_and_search(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test error when neither resource ID nor --search provided."""
        result = cli_runner.invoke(main, ["download"])

        assert result.exit_code == 1

    def test_download_stdout_with_batch(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test error when --stdout used with batch download."""
        result = cli_runner.invoke(main, ["download", "--search", "photos", "--stdout"])

        assert result.exit_code == 1

    def test_download_invalid_resource_id(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error for invalid resource ID."""
        result = cli_runner.invoke(main, ["download", "-1", "--output", str(tmp_path)])

        # Exit code 2 is Click's error for bad arguments, 1 is application error
        assert result.exit_code != 0
