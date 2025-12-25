"""Tests for validation utilities."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from resourcespace_cli.exceptions import ValidationError
from resourcespace_cli.utils.validation import (
    ConfigKeyInput,
    DownloadInput,
    FieldInput,
    ResourceIdInput,
    SearchQueryInput,
    UploadInput,
    _extract_error_message,
    validate_config_key,
    validate_download_input,
    validate_field_string,
    validate_resource_id,
    validate_search_query,
    validate_upload_input,
)


class TestResourceIdInput:
    """Tests for ResourceIdInput model."""

    def test_valid_resource_id(self) -> None:
        """Test valid positive resource IDs."""
        result = ResourceIdInput(resource_id=1)
        assert result.resource_id == 1

        result = ResourceIdInput(resource_id=12345)
        assert result.resource_id == 12345

    def test_zero_resource_id_invalid(self) -> None:
        """Test that zero resource ID is invalid."""
        with pytest.raises(PydanticValidationError):
            ResourceIdInput(resource_id=0)

    def test_negative_resource_id_invalid(self) -> None:
        """Test that negative resource IDs are invalid."""
        with pytest.raises(PydanticValidationError):
            ResourceIdInput(resource_id=-1)


class TestSearchQueryInput:
    """Tests for SearchQueryInput model."""

    def test_valid_search_query(self) -> None:
        """Test valid search query with defaults."""
        result = SearchQueryInput(query="test")
        assert result.query == "test"
        assert result.page == 1
        assert result.limit == 20
        assert result.resource_type is None
        assert result.collection_id is None

    def test_valid_search_query_with_all_params(self) -> None:
        """Test valid search query with all parameters."""
        result = SearchQueryInput(
            query="photo",
            page=2,
            limit=50,
            resource_type=1,
            collection_id=10,
        )
        assert result.query == "photo"
        assert result.page == 2
        assert result.limit == 50
        assert result.resource_type == 1
        assert result.collection_id == 10

    def test_empty_query_invalid(self) -> None:
        """Test that empty query string is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="")

    def test_query_too_long_invalid(self) -> None:
        """Test that query exceeding max length is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="x" * 1001)

    def test_page_zero_invalid(self) -> None:
        """Test that page 0 is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="test", page=0)

    def test_limit_too_high_invalid(self) -> None:
        """Test that limit over 1000 is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="test", limit=1001)

    def test_negative_resource_type_invalid(self) -> None:
        """Test that negative resource type is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="test", resource_type=-1)

    def test_zero_collection_id_invalid(self) -> None:
        """Test that zero collection ID is invalid."""
        with pytest.raises(PydanticValidationError):
            SearchQueryInput(query="test", collection_id=0)


class TestDownloadInput:
    """Tests for DownloadInput model."""

    def test_valid_download_with_resource_id(self) -> None:
        """Test valid download with resource ID."""
        result = DownloadInput(resource_id=123)
        assert result.resource_id == 123
        assert result.search_query is None
        assert result.stdout is False

    def test_valid_download_with_search_query(self) -> None:
        """Test valid download with search query."""
        result = DownloadInput(search_query="photos")
        assert result.resource_id is None
        assert result.search_query == "photos"

    def test_valid_download_with_stdout(self) -> None:
        """Test valid download with stdout option."""
        result = DownloadInput(resource_id=123, stdout=True)
        assert result.resource_id == 123
        assert result.stdout is True

    def test_no_mode_specified_invalid(self) -> None:
        """Test that neither resource_id nor search_query is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            DownloadInput()
        assert "Either resource_id or search_query is required" in str(exc_info.value)

    def test_both_modes_specified_invalid(self) -> None:
        """Test that both resource_id and search_query is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            DownloadInput(resource_id=123, search_query="photos")
        assert "Cannot specify both resource_id and search_query" in str(exc_info.value)

    def test_stdout_with_search_query_invalid(self) -> None:
        """Test that stdout with search_query is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            DownloadInput(search_query="photos", stdout=True)
        assert "--stdout can only be used with single resource" in str(exc_info.value)

    def test_negative_resource_id_invalid(self) -> None:
        """Test that negative resource ID is invalid."""
        with pytest.raises(PydanticValidationError):
            DownloadInput(resource_id=-1)

    def test_output_dir_resolved(self) -> None:
        """Test that output_dir is resolved to absolute path."""
        result = DownloadInput(resource_id=123, output_dir=Path("."))
        assert result.output_dir.is_absolute()


class TestUploadInput:
    """Tests for UploadInput model."""

    def test_valid_upload_single_file(self, tmp_path: Path) -> None:
        """Test valid upload with single file."""
        test_file = tmp_path / "test.jpg"
        test_file.touch()

        result = UploadInput(files=[test_file])
        assert len(result.files) == 1
        assert result.resource_type == 1
        assert result.collection_id is None
        assert result.fields == []

    def test_valid_upload_with_all_options(self, tmp_path: Path) -> None:
        """Test valid upload with all options."""
        test_file = tmp_path / "test.jpg"
        test_file.touch()

        result = UploadInput(
            files=[test_file],
            resource_type=2,
            collection_id=5,
            fields=[("title", "My Photo")],
        )
        assert result.resource_type == 2
        assert result.collection_id == 5
        assert result.fields == [("title", "My Photo")]

    def test_empty_files_list_invalid(self) -> None:
        """Test that empty files list is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UploadInput(files=[])
        assert "No files specified" in str(exc_info.value)

    def test_invalid_resource_type_invalid(self) -> None:
        """Test that resource type 0 is invalid."""
        with pytest.raises(PydanticValidationError):
            UploadInput(files=[Path("test.jpg")], resource_type=0)

    def test_negative_collection_id_invalid(self) -> None:
        """Test that negative collection ID is invalid."""
        with pytest.raises(PydanticValidationError):
            UploadInput(files=[Path("test.jpg")], collection_id=-1)


class TestFieldInput:
    """Tests for FieldInput model."""

    def test_valid_field_format(self) -> None:
        """Test valid field in name=value format."""
        result = FieldInput(raw="title=My Photo")
        assert result.name == "title"
        assert result.value == "My Photo"

    def test_field_with_empty_value(self) -> None:
        """Test field with empty value."""
        result = FieldInput(raw="description=")
        assert result.name == "description"
        assert result.value == ""

    def test_field_with_multiple_equals(self) -> None:
        """Test field with multiple equals signs."""
        result = FieldInput(raw="formula=a=b+c")
        assert result.name == "formula"
        assert result.value == "a=b+c"

    def test_field_with_whitespace(self) -> None:
        """Test field with whitespace around name/value."""
        result = FieldInput(raw=" title = My Photo ")
        assert result.name == "title"
        assert result.value == "My Photo"

    def test_missing_equals_invalid(self) -> None:
        """Test that missing equals sign is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            FieldInput(raw="invalid_field")
        assert "Invalid field format" in str(exc_info.value)


class TestConfigKeyInput:
    """Tests for ConfigKeyInput model."""

    @pytest.mark.parametrize(
        "key",
        [
            "url",
            "api-url",
            "api_url",
            "key",
            "api-key",
            "api_key",
            "user",
            "username",
            "RESOURCESPACE_API_URL",
            "RESOURCESPACE_API_KEY",
            "RESOURCESPACE_USER",
        ],
    )
    def test_valid_config_keys(self, key: str) -> None:
        """Test all valid configuration key aliases."""
        result = ConfigKeyInput(key=key)
        assert result.key == key

    def test_case_insensitive_keys(self) -> None:
        """Test that keys are case insensitive."""
        result = ConfigKeyInput(key="URL")
        assert result.key == "URL"

        result = ConfigKeyInput(key="Api-Key")
        assert result.key == "Api-Key"

    def test_invalid_key_raises_error(self) -> None:
        """Test that invalid key raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ConfigKeyInput(key="invalid_key")
        assert "Invalid config key" in str(exc_info.value)


class TestValidateResourceId:
    """Tests for validate_resource_id function."""

    def test_valid_resource_id(self) -> None:
        """Test valid resource ID returns the ID."""
        result = validate_resource_id(123)
        assert result == 123

    def test_invalid_resource_id_raises_validation_error(self) -> None:
        """Test invalid resource ID raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_resource_id(0)


class TestValidateSearchQuery:
    """Tests for validate_search_query function."""

    def test_valid_search_query(self) -> None:
        """Test valid search query returns SearchQueryInput."""
        result = validate_search_query("test", page=2, limit=50)
        assert result.query == "test"
        assert result.page == 2
        assert result.limit == 50

    def test_invalid_search_query_raises_validation_error(self) -> None:
        """Test invalid search query raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_search_query("")


class TestValidateDownloadInput:
    """Tests for validate_download_input function."""

    def test_valid_download_input(self) -> None:
        """Test valid download input returns DownloadInput."""
        result = validate_download_input(resource_id=123)
        assert result.resource_id == 123

    def test_invalid_download_input_raises_validation_error(self) -> None:
        """Test invalid download input raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_download_input()  # Neither resource_id nor search_query


class TestValidateUploadInput:
    """Tests for validate_upload_input function."""

    def test_valid_upload_input(self, tmp_path: Path) -> None:
        """Test valid upload input returns UploadInput."""
        test_file = tmp_path / "test.jpg"
        test_file.touch()

        result = validate_upload_input(files=[test_file])
        assert len(result.files) == 1

    def test_invalid_upload_input_raises_validation_error(self) -> None:
        """Test invalid upload input raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_upload_input(files=[])


class TestValidateFieldString:
    """Tests for validate_field_string function."""

    def test_valid_field_string(self) -> None:
        """Test valid field string returns tuple."""
        name, value = validate_field_string("title=My Photo")
        assert name == "title"
        assert value == "My Photo"

    def test_invalid_field_string_raises_validation_error(self) -> None:
        """Test invalid field string raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_field_string("no_equals")


class TestValidateConfigKey:
    """Tests for validate_config_key function."""

    def test_valid_config_key(self) -> None:
        """Test valid config key returns the key."""
        result = validate_config_key("url")
        assert result == "url"

    def test_invalid_config_key_raises_validation_error(self) -> None:
        """Test invalid config key raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_config_key("invalid")


class TestExtractErrorMessage:
    """Tests for _extract_error_message function."""

    def test_extract_from_pydantic_error(self) -> None:
        """Test extracting message from Pydantic validation error."""
        try:
            ResourceIdInput(resource_id=0)
        except PydanticValidationError as e:
            msg = _extract_error_message(e)
            assert msg  # Should have some message
            assert "greater than 0" in msg.lower() or "gt" in msg.lower()

    def test_extract_from_regular_exception(self) -> None:
        """Test extracting message from regular exception."""
        error = ValueError("Something went wrong")
        msg = _extract_error_message(error)
        assert msg == "Something went wrong"

    def test_strip_value_error_prefix(self) -> None:
        """Test that 'Value error, ' prefix is stripped."""
        # Create a custom Pydantic error with Value error prefix
        try:
            DownloadInput()  # Will raise validation error
        except PydanticValidationError as e:
            msg = _extract_error_message(e)
            # Should not start with "Value error, "
            assert not msg.startswith("Value error, ")
