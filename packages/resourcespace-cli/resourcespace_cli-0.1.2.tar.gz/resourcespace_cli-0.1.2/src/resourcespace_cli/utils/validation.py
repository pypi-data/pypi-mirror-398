"""Input validation utilities using Pydantic for ResourceSpace CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class ResourceIdInput(BaseModel):
    """Validates resource ID input."""

    resource_id: Annotated[int, Field(gt=0, description="Resource ID must be positive")]


class SearchQueryInput(BaseModel):
    """Validates search query input."""

    query: Annotated[str, Field(min_length=1, max_length=1000)]
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=1000)] = 20
    resource_type: int | None = None
    collection_id: int | None = None

    @field_validator("resource_type", "collection_id")
    @classmethod
    def validate_positive_id(cls, v: int | None) -> int | None:
        """Validate that optional IDs are positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("ID must be a positive integer")
        return v


class DownloadInput(BaseModel):
    """Validates download command input."""

    resource_id: int | None = None
    search_query: str | None = None
    output_dir: Path = Field(default_factory=Path.cwd)
    stdout: bool = False

    @model_validator(mode="after")
    def validate_download_mode(self) -> DownloadInput:
        """Validate that exactly one download mode is specified."""
        if self.resource_id is None and self.search_query is None:
            raise ValueError("Either resource_id or search_query is required")
        if self.resource_id is not None and self.search_query is not None:
            raise ValueError("Cannot specify both resource_id and search_query")
        if self.stdout and self.search_query is not None:
            raise ValueError("--stdout can only be used with single resource download")
        return self

    @field_validator("resource_id")
    @classmethod
    def validate_resource_id(cls, v: int | None) -> int | None:
        """Validate that resource ID is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Resource ID must be a positive integer")
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Resolve the output directory path."""
        return v.resolve()


class UploadInput(BaseModel):
    """Validates upload command input."""

    files: list[Path]
    resource_type: Annotated[int, Field(ge=1)] = 1
    collection_id: int | None = None
    fields: list[tuple[str, str]] = Field(default_factory=list)

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[Path]) -> list[Path]:
        """Validate that at least one file is specified."""
        if not v:
            raise ValueError(
                "No files specified. Provide file paths, glob patterns, or use --stdin."
            )
        return v

    @field_validator("collection_id")
    @classmethod
    def validate_collection_id(cls, v: int | None) -> int | None:
        """Validate that collection ID is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Collection ID must be a positive integer")
        return v


class FieldInput(BaseModel):
    """Validates metadata field input in 'name=value' format."""

    raw: str

    @field_validator("raw")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate that field string contains '=' separator."""
        if "=" not in v:
            raise ValueError(f"Invalid field format '{v}'. Use 'name=value' format.")
        return v

    @property
    def name(self) -> str:
        """Get the field name."""
        name, _, _ = self.raw.partition("=")
        return name.strip()

    @property
    def value(self) -> str:
        """Get the field value."""
        _, _, value = self.raw.partition("=")
        return value.strip()


class ConfigKeyInput(BaseModel):
    """Validates configuration key input."""

    key: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate that key is a recognized configuration key or alias."""
        valid_aliases = {
            "url",
            "api-url",
            "api_url",
            "key",
            "api-key",
            "api_key",
            "user",
            "username",
            "resourcespace_api_url",
            "resourcespace_api_key",
            "resourcespace_user",
        }
        if v.lower() not in valid_aliases:
            raise ValueError(f"Invalid config key '{v}'. Valid keys: url, key, user")
        return v


# === Validation Helper Functions ===


def validate_resource_id(resource_id: int) -> int:
    """Validate a resource ID.

    Args:
        resource_id: The resource ID to validate.

    Returns:
        The validated resource ID.

    Raises:
        ValidationError: If resource ID is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        validated = ResourceIdInput(resource_id=resource_id)
        return validated.resource_id
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def validate_search_query(
    query: str,
    page: int = 1,
    limit: int = 20,
    resource_type: int | None = None,
    collection_id: int | None = None,
) -> SearchQueryInput:
    """Validate search query parameters.

    Args:
        query: The search query string.
        page: Page number (1-indexed).
        limit: Results per page.
        resource_type: Optional resource type filter.
        collection_id: Optional collection filter.

    Returns:
        Validated SearchQueryInput.

    Raises:
        ValidationError: If any parameter is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        return SearchQueryInput(
            query=query,
            page=page,
            limit=limit,
            resource_type=resource_type,
            collection_id=collection_id,
        )
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def validate_download_input(
    resource_id: int | None = None,
    search_query: str | None = None,
    output_dir: Path | None = None,
    stdout: bool = False,
) -> DownloadInput:
    """Validate download command input.

    Args:
        resource_id: Resource ID to download.
        search_query: Search query for batch download.
        output_dir: Output directory path.
        stdout: Whether to output to stdout.

    Returns:
        Validated DownloadInput.

    Raises:
        ValidationError: If input combination is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        return DownloadInput(
            resource_id=resource_id,
            search_query=search_query,
            output_dir=output_dir or Path.cwd(),
            stdout=stdout,
        )
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def validate_upload_input(
    files: list[Path],
    resource_type: int = 1,
    collection_id: int | None = None,
    fields: list[tuple[str, str]] | None = None,
) -> UploadInput:
    """Validate upload command input.

    Args:
        files: List of file paths to upload.
        resource_type: Resource type ID.
        collection_id: Optional collection ID.
        fields: Optional list of (field_name, value) tuples.

    Returns:
        Validated UploadInput.

    Raises:
        ValidationError: If input is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        return UploadInput(
            files=files,
            resource_type=resource_type,
            collection_id=collection_id,
            fields=fields or [],
        )
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def validate_field_string(field_str: str) -> tuple[str, str]:
    """Validate and parse a field string in 'name=value' format.

    Args:
        field_str: Field string like 'title=My Photo'.

    Returns:
        Tuple of (field_name, field_value).

    Raises:
        ValidationError: If format is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        field = FieldInput(raw=field_str)
        return field.name, field.value
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def validate_config_key(key: str) -> str:
    """Validate a configuration key.

    Args:
        key: The configuration key to validate.

    Returns:
        The validated key.

    Raises:
        ValidationError: If key is invalid.
    """
    from resourcespace_cli.exceptions import ValidationError

    try:
        validated = ConfigKeyInput(key=key)
        return validated.key
    except Exception as e:
        raise ValidationError(_extract_error_message(e)) from e


def _extract_error_message(error: Exception) -> str:
    """Extract a user-friendly error message from Pydantic validation errors.

    Args:
        error: The exception to extract message from.

    Returns:
        User-friendly error message.
    """
    from pydantic import ValidationError as PydanticValidationError

    if isinstance(error, PydanticValidationError):
        # Get the first error message
        errors = error.errors()
        if errors:
            first_error = errors[0]
            msg = first_error.get("msg", str(error))
            # Clean up Pydantic message format
            if msg.startswith("Value error, "):
                msg = msg[13:]
            return msg
    return str(error)
