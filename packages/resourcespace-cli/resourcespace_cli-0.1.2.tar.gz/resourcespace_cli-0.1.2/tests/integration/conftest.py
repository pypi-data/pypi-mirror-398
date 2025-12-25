"""Shared fixtures for integration tests."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Generator

import pytest
from click.testing import CliRunner

from resourcespace_cli.config import Config


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def integration_config() -> Config:
    """Create a complete configuration for integration tests."""
    return Config(
        api_url="https://resourcespace.example.com/api/",
        api_key="integration_test_api_key_12345",
        user="integration_user",
    )


@pytest.fixture
def integration_env(integration_config: Config, tmp_path: Path) -> Generator[Path, None, None]:
    """Set up environment variables for integration tests.

    Creates a temporary .env file and sets environment variables
    to ensure consistent test configuration.
    """
    env_file = tmp_path / ".env"
    env_file.touch()

    original_env = {
        "RESOURCESPACE_API_URL": os.environ.get("RESOURCESPACE_API_URL"),
        "RESOURCESPACE_API_KEY": os.environ.get("RESOURCESPACE_API_KEY"),
        "RESOURCESPACE_USER": os.environ.get("RESOURCESPACE_USER"),
        "RESOURCESPACE_ENV_PATH": os.environ.get("RESOURCESPACE_ENV_PATH"),
    }

    os.environ["RESOURCESPACE_API_URL"] = integration_config.api_url
    os.environ["RESOURCESPACE_API_KEY"] = integration_config.api_key
    os.environ["RESOURCESPACE_USER"] = integration_config.user
    os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

    yield env_file

    # Restore original environment
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


# ============================================================================
# URL Pattern Fixtures
# ============================================================================


@pytest.fixture
def api_url_pattern() -> re.Pattern[str]:
    """Pattern matching any API URL."""
    return re.compile(r"https://resourcespace\.example\.com/api/.*")


@pytest.fixture
def search_url_pattern() -> re.Pattern[str]:
    """Pattern matching search API calls."""
    return re.compile(r".*function=do_search.*")


@pytest.fixture
def get_resource_data_pattern() -> re.Pattern[str]:
    """Pattern matching get_resource_data API calls."""
    return re.compile(r".*function=get_resource_data.*")


@pytest.fixture
def get_resource_path_pattern() -> re.Pattern[str]:
    """Pattern matching get_resource_path API calls."""
    return re.compile(r".*function=get_resource_path.*")


@pytest.fixture
def collections_url_pattern() -> re.Pattern[str]:
    """Pattern matching get_user_collections API calls."""
    return re.compile(r".*function=get_user_collections.*")


@pytest.fixture
def types_url_pattern() -> re.Pattern[str]:
    """Pattern matching get_resource_types API calls."""
    return re.compile(r".*function=get_resource_types.*")


@pytest.fixture
def create_resource_pattern() -> re.Pattern[str]:
    """Pattern matching create_resource API calls."""
    return re.compile(r".*function=create_resource.*")


@pytest.fixture
def upload_file_pattern() -> re.Pattern[str]:
    """Pattern matching upload_file API calls."""
    return re.compile(r".*function=upload_file.*")


# ============================================================================
# Mock Response Data Fixtures
# ============================================================================


@pytest.fixture
def sample_search_results() -> list[dict[str, Any]]:
    """Sample search results."""
    return [
        {
            "ref": "101",
            "field8": "Sunset Landscape",
            "resource_type": "1",
            "file_extension": "jpg",
            "preview": "https://resourcespace.example.com/previews/101_pre.jpg",
        },
        {
            "ref": "102",
            "field8": "Mountain View",
            "resource_type": "1",
            "file_extension": "png",
            "preview": "https://resourcespace.example.com/previews/102_pre.png",
        },
        {
            "ref": "103",
            "field8": "City Skyline",
            "resource_type": "2",
            "file_extension": "jpg",
            "preview": "https://resourcespace.example.com/previews/103_pre.jpg",
        },
    ]


@pytest.fixture
def sample_resource_data() -> dict[str, Any]:
    """Sample resource metadata."""
    return {
        "ref": "101",
        "resource_type": "1",
        "creation_date": "2024-01-15 10:30:00",
        "file_path": "photos/sunset.jpg",
        "file_extension": "jpg",
        "file_size": "2048576",
        "original_filename": "sunset.jpg",
        "field8": "Sunset Landscape",
    }


@pytest.fixture
def sample_field_data() -> list[dict[str, Any]]:
    """Sample resource field data."""
    return [
        {"ref": "8", "title": "Title", "value": "Sunset Landscape"},
        {"ref": "3", "title": "Description", "value": "A beautiful sunset over the ocean"},
        {"ref": "12", "title": "Keywords", "value": "sunset, ocean, landscape"},
    ]


@pytest.fixture
def sample_image_sizes() -> list[dict[str, Any]]:
    """Sample image size data."""
    return [
        {"id": "thm", "name": "Thumbnail", "width": "150", "height": "100"},
        {"id": "pre", "name": "Preview", "width": "800", "height": "600"},
        {"id": "scr", "name": "Screen", "width": "1920", "height": "1080"},
        {"id": "", "name": "Original", "width": "4000", "height": "3000"},
    ]


@pytest.fixture
def sample_collections() -> list[dict[str, Any]]:
    """Sample collections list."""
    return [
        {"ref": "1", "name": "Nature Photos", "count": "25"},
        {"ref": "2", "name": "Architecture", "count": "42"},
        {"ref": "3", "name": "Portraits", "count": "18"},
    ]


@pytest.fixture
def sample_resource_types() -> list[dict[str, Any]]:
    """Sample resource types."""
    return [
        {"ref": "1", "name": "Photo"},
        {"ref": "2", "name": "Document"},
        {"ref": "3", "name": "Video"},
        {"ref": "4", "name": "Audio"},
    ]


@pytest.fixture
def sample_download_url() -> str:
    """Sample download URL."""
    return "https://resourcespace.example.com/filestore/101/sunset.jpg"


@pytest.fixture
def sample_file_content() -> bytes:
    """Sample file content for download tests."""
    return b"FAKE_IMAGE_CONTENT_" + b"x" * 1024
