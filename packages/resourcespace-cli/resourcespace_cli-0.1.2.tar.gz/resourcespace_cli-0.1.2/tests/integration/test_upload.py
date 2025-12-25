"""Integration tests for the upload command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestUploadSingle:
    """Integration tests for single file upload."""

    def test_upload_single_file(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test uploading a single file."""
        # Create test file
        test_file = tmp_path / "test_image.jpg"
        test_file.write_bytes(b"FAKE_JPG_DATA")

        # Mock create_resource
        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=999,  # New resource ID
        )

        # Mock upload_file (POST request)
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )

        result = cli_runner.invoke(main, ["upload", str(test_file)])

        assert result.exit_code == 0
        assert "Uploaded" in result.output
        assert "999" in result.output

    def test_upload_single_file_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test upload with JSON output."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"FAKE_DATA")

        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=888,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )

        result = cli_runner.invoke(main, ["--json", "upload", str(test_file)])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["resource_id"] == 888

    def test_upload_with_resource_type(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test upload with custom resource type."""
        test_file = tmp_path / "document.pdf"
        test_file.write_bytes(b"FAKE_PDF")

        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*resource_type=2.*"),
            json=777,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )

        result = cli_runner.invoke(main, ["upload", str(test_file), "--type", "2"])

        assert result.exit_code == 0

    def test_upload_with_collection(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test upload with collection assignment."""
        test_file = tmp_path / "photo.jpg"
        test_file.write_bytes(b"FAKE_JPG")

        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=666,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=add_resource_to_collection.*resource=666.*collection=5.*"),
            json=True,
        )

        result = cli_runner.invoke(main, ["upload", str(test_file), "--collection", "5"])

        assert result.exit_code == 0

    def test_upload_with_metadata_fields(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test upload with metadata field updates."""
        test_file = tmp_path / "photo.jpg"
        test_file.write_bytes(b"FAKE_JPG")

        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=555,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=update_field.*resource=555.*field=8.*"),
            json=True,
        )

        result = cli_runner.invoke(
            main, ["upload", str(test_file), "--field", "8=My Photo Title"]
        )

        assert result.exit_code == 0


class TestUploadBatch:
    """Integration tests for batch upload."""

    def test_upload_multiple_files(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test uploading multiple files."""
        # Create test files
        files = []
        for i in range(3):
            f = tmp_path / f"image_{i}.jpg"
            f.write_bytes(f"FAKE_JPG_{i}".encode())
            files.append(str(f))

        # Mock responses for each file
        for resource_id in [100, 101, 102]:
            httpx_mock.add_response(
                url=re.compile(r".*function=create_resource.*"),
                json=resource_id,
            )
            httpx_mock.add_response(
                method="POST",
                url=re.compile(r".*function=upload_file.*"),
                json=True,
            )

        result = cli_runner.invoke(main, ["upload"] + files)

        assert result.exit_code == 0
        assert "Succeeded" in result.output
        assert "3" in result.output  # 3 files succeeded

    def test_upload_batch_partial_failure(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test batch upload with some failures."""
        files = []
        for i in range(2):
            f = tmp_path / f"file_{i}.jpg"
            f.write_bytes(f"DATA_{i}".encode())
            files.append(str(f))

        # First file succeeds
        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=100,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )

        # Second file fails at create_resource
        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            status_code=500,
        )

        result = cli_runner.invoke(main, ["upload"] + files)

        # Should still exit 0 if at least one succeeded
        assert "Succeeded" in result.output
        assert "Failed" in result.output

    def test_upload_batch_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test batch upload with JSON output."""
        files = []
        for i in range(2):
            f = tmp_path / f"file_{i}.jpg"
            f.write_bytes(f"DATA_{i}".encode())
            files.append(str(f))

        for resource_id in [100, 101]:
            httpx_mock.add_response(
                url=re.compile(r".*function=create_resource.*"),
                json=resource_id,
            )
            httpx_mock.add_response(
                method="POST",
                url=re.compile(r".*function=upload_file.*"),
                json=True,
            )

        result = cli_runner.invoke(main, ["--json", "upload"] + files)

        assert result.exit_code == 0
        output = json.loads(result.output)
        # Check for succeeded items in the batch result
        assert "succeeded" in output or "success_count" in output


class TestUploadValidation:
    """Integration tests for upload validation."""

    def test_upload_no_files_provided(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test error when no files provided."""
        result = cli_runner.invoke(main, ["upload"])

        assert result.exit_code == 1

    def test_upload_nonexistent_file(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error for non-existent file."""
        result = cli_runner.invoke(main, ["upload", str(tmp_path / "nonexistent.jpg")])

        assert result.exit_code == 1

    def test_upload_invalid_field_format(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test error for invalid field format."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"DATA")

        result = cli_runner.invoke(
            main, ["upload", str(test_file), "--field", "invalid_format"]
        )

        assert result.exit_code == 1

    def test_upload_with_multiple_fields(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test upload with multiple metadata fields."""
        test_file = tmp_path / "photo.jpg"
        test_file.write_bytes(b"FAKE_JPG")

        httpx_mock.add_response(
            url=re.compile(r".*function=create_resource.*"),
            json=444,
        )
        httpx_mock.add_response(
            method="POST",
            url=re.compile(r".*function=upload_file.*"),
            json=True,
        )
        # Mock update_field for each field
        httpx_mock.add_response(
            url=re.compile(r".*function=update_field.*field=8.*"),
            json=True,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=update_field.*field=3.*"),
            json=True,
        )

        result = cli_runner.invoke(
            main,
            [
                "upload",
                str(test_file),
                "--field",
                "8=Title",
                "--field",
                "3=Description",
            ],
        )

        assert result.exit_code == 0
