"""Integration tests for the info command."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from resourcespace_cli.main import main


class TestInfoCommand:
    """Integration tests for rs info command."""

    def test_info_basic_resource(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
        sample_field_data: list[dict[str, Any]],
        sample_image_sizes: list[dict[str, Any]],
    ) -> None:
        """Test displaying info for a resource."""
        # Mock get_resource_data
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*resource=101.*"),
            json=sample_resource_data,
        )
        # Mock get_resource_field_data
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_field_data.*"),
            json=sample_field_data,
        )
        # Mock get_resource_all_image_sizes
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_all_image_sizes.*"),
            json=sample_image_sizes,
        )
        # Mock get_alternative_files
        httpx_mock.add_response(
            url=re.compile(r".*function=get_alternative_files.*"),
            json=[],
        )
        # Mock get_user_collections (for get_resource_collections)
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            json=[],
        )
        # Mock get_resource_path for preview URL
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*size=pre.*"),
            json="https://resourcespace.example.com/preview/101_pre.jpg",
        )

        result = cli_runner.invoke(main, ["info", "101"])

        assert result.exit_code == 0
        assert "Resource #101" in result.output
        assert "jpg" in result.output.lower()

    def test_info_json_output(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
        sample_field_data: list[dict[str, Any]],
        sample_image_sizes: list[dict[str, Any]],
    ) -> None:
        """Test info command with JSON output."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_field_data.*"),
            json=sample_field_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_all_image_sizes.*"),
            json=sample_image_sizes,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_alternative_files.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json="https://example.com/preview.jpg",
        )

        result = cli_runner.invoke(main, ["--json", "info", "101"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["resource"]["id"] == 101
        assert "data" in output["resource"]
        assert "metadata" in output["resource"]
        assert "sizes" in output["resource"]

    def test_info_resource_not_found(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test info for non-existent resource."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json={},  # Empty response for non-existent resource
        )

        result = cli_runner.invoke(main, ["info", "99999"])

        assert "not found" in result.output.lower()

    def test_info_handles_api_errors_gracefully(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
    ) -> None:
        """Test that info command handles partial API failures gracefully."""
        # Main resource data succeeds
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        # Field data fails (404)
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_field_data.*"),
            status_code=404,
        )
        # Sizes fail
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_all_image_sizes.*"),
            status_code=500,
        )
        # Alternatives fail
        httpx_mock.add_response(
            url=re.compile(r".*function=get_alternative_files.*"),
            status_code=500,
        )
        # Collections
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            json=[],
        )
        # Preview URL fails
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            status_code=404,
        )

        result = cli_runner.invoke(main, ["info", "101"])

        # Should still display basic info, not crash
        assert result.exit_code == 0
        assert "101" in result.output

    def test_info_with_collections(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
        sample_collections: list[dict[str, Any]],
    ) -> None:
        """Test info showing collections containing the resource."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_field_data.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_all_image_sizes.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_alternative_files.*"),
            json=[],
        )
        # get_resource_collections calls get_user_collections and then searches
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            json=sample_collections,
        )
        # Mock the search calls for each collection to find resources
        # Resource 101 is found in collection 1 (Nature Photos)
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=[{"ref": "101"}],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=do_search.*"),
            json=[],
        )
        # Mock get_collection call
        httpx_mock.add_response(
            url=re.compile(r".*function=get_collection.*"),
            json={"ref": "1", "name": "Nature Photos", "count": "25"},
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json="",
        )

        result = cli_runner.invoke(main, ["info", "101"])

        assert result.exit_code == 0
        assert "Collections" in result.output
        assert "Nature Photos" in result.output

    def test_info_invalid_resource_id(
        self,
        integration_env: Path,
        cli_runner: CliRunner,
    ) -> None:
        """Test info with invalid resource ID."""
        result = cli_runner.invoke(main, ["info", "-1"])

        # Exit code 2 is Click's error for bad arguments, 1 is application error
        assert result.exit_code != 0

    def test_info_shows_file_size(
        self,
        httpx_mock: HTTPXMock,
        integration_env: Path,
        cli_runner: CliRunner,
        sample_resource_data: dict[str, Any],
    ) -> None:
        """Test that info displays file size in human-readable format."""
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_data.*"),
            json=sample_resource_data,
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_field_data.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_all_image_sizes.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_alternative_files.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_user_collections.*"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(r".*function=get_resource_path.*"),
            json="",
        )

        result = cli_runner.invoke(main, ["info", "101"])

        assert result.exit_code == 0
        # 2048576 bytes should be ~2.0 MB
        assert "2.0 MB" in result.output or "MB" in result.output
