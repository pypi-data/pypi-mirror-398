"""Tests for file handling utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from resourcespace_cli.exceptions import DownloadError
from resourcespace_cli.utils.files import (
    ensure_output_directory,
    extract_filename_from_url,
    resolve_filename_conflict,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_clean_filename_unchanged(self) -> None:
        """Test that clean filenames are unchanged."""
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("my_photo.jpg") == "my_photo.jpg"
        assert sanitize_filename("file-name.txt") == "file-name.txt"

    def test_replace_less_than(self) -> None:
        """Test replacement of < character."""
        assert sanitize_filename("file<name.txt") == "file_name.txt"

    def test_replace_greater_than(self) -> None:
        """Test replacement of > character."""
        assert sanitize_filename("file>name.txt") == "file_name.txt"

    def test_replace_colon(self) -> None:
        """Test replacement of : character."""
        assert sanitize_filename("file:name.txt") == "file_name.txt"

    def test_replace_double_quote(self) -> None:
        """Test replacement of " character."""
        assert sanitize_filename('file"name.txt') == "file_name.txt"

    def test_replace_forward_slash(self) -> None:
        """Test replacement of / character."""
        assert sanitize_filename("file/name.txt") == "file_name.txt"

    def test_replace_backslash(self) -> None:
        """Test replacement of \\ character."""
        assert sanitize_filename("file\\name.txt") == "file_name.txt"

    def test_replace_pipe(self) -> None:
        """Test replacement of | character."""
        assert sanitize_filename("file|name.txt") == "file_name.txt"

    def test_replace_question_mark(self) -> None:
        """Test replacement of ? character."""
        assert sanitize_filename("file?name.txt") == "file_name.txt"

    def test_replace_asterisk(self) -> None:
        """Test replacement of * character."""
        assert sanitize_filename("file*name.txt") == "file_name.txt"

    def test_multiple_invalid_chars(self) -> None:
        """Test replacement of multiple invalid characters."""
        assert sanitize_filename("a<b>c:d/e\\f|g?h*i.txt") == "a_b_c_d_e_f_g_h_i.txt"

    def test_strip_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        assert sanitize_filename("  filename.txt  ") == "filename.txt"

    def test_empty_string(self) -> None:
        """Test sanitizing empty string."""
        assert sanitize_filename("") == ""


class TestResolveFilenameConflict:
    """Tests for resolve_filename_conflict function."""

    def test_no_conflict(self, tmp_path: Path) -> None:
        """Test when file doesn't exist, returns original path."""
        result = resolve_filename_conflict(tmp_path, "test.jpg", 123)
        assert result == tmp_path / "test.jpg"

    def test_conflict_adds_resource_id(self, tmp_path: Path) -> None:
        """Test when file exists, adds resource ID suffix."""
        # Create existing file
        (tmp_path / "test.jpg").touch()

        result = resolve_filename_conflict(tmp_path, "test.jpg", 123)
        assert result == tmp_path / "test_123.jpg"

    def test_preserves_extension(self, tmp_path: Path) -> None:
        """Test that file extension is preserved after conflict resolution."""
        (tmp_path / "document.pdf").touch()

        result = resolve_filename_conflict(tmp_path, "document.pdf", 456)
        assert result.suffix == ".pdf"
        assert result.stem == "document_456"

    def test_handles_multiple_dots(self, tmp_path: Path) -> None:
        """Test handling filenames with multiple dots."""
        (tmp_path / "file.name.with.dots.txt").touch()

        result = resolve_filename_conflict(tmp_path, "file.name.with.dots.txt", 789)
        assert result == tmp_path / "file.name.with.dots_789.txt"

    def test_handles_no_extension(self, tmp_path: Path) -> None:
        """Test handling filenames without extension."""
        (tmp_path / "README").touch()

        result = resolve_filename_conflict(tmp_path, "README", 100)
        assert result == tmp_path / "README_100"


class TestExtractFilenameFromUrl:
    """Tests for extract_filename_from_url function."""

    def test_simple_url(self) -> None:
        """Test extracting filename from simple URL."""
        url = "https://example.com/files/document.pdf"
        assert extract_filename_from_url(url) == "document.pdf"

    def test_url_with_query_params(self) -> None:
        """Test extracting filename ignoring query parameters."""
        url = "https://example.com/files/image.jpg?width=800&height=600"
        assert extract_filename_from_url(url) == "image.jpg"

    def test_url_encoded_filename(self) -> None:
        """Test extracting URL-encoded filename."""
        url = "https://example.com/files/my%20photo.jpg"
        assert extract_filename_from_url(url) == "my photo.jpg"

    def test_url_with_fragment(self) -> None:
        """Test extracting filename ignoring fragment."""
        url = "https://example.com/files/doc.html#section1"
        assert extract_filename_from_url(url) == "doc.html"

    def test_url_no_filename(self) -> None:
        """Test URL with no filename returns default."""
        url = "https://example.com/"
        assert extract_filename_from_url(url) == "download"

    def test_url_directory_path(self) -> None:
        """Test URL with trailing slash returns directory name."""
        # Path("/files/").name returns "files" (the last path component)
        url = "https://example.com/files/"
        assert extract_filename_from_url(url) == "files"

    def test_complex_path(self) -> None:
        """Test URL with complex path structure."""
        url = "https://cdn.example.com/assets/2024/01/photos/vacation/sunset.png"
        assert extract_filename_from_url(url) == "sunset.png"


class TestEnsureOutputDirectory:
    """Tests for ensure_output_directory function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        assert not new_dir.exists()

        ensure_output_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory_ok(self, tmp_path: Path) -> None:
        """Test that existing directory doesn't raise error."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # Should not raise
        ensure_output_directory(existing_dir)

        assert existing_dir.exists()

    def test_permission_error_raises_download_error(self, tmp_path: Path) -> None:
        """Test that permission errors raise DownloadError."""
        # Create a file where we want a directory
        # This will cause an error when trying to create a directory with that name
        blocker = tmp_path / "blocker"
        blocker.touch()

        with pytest.raises(DownloadError) as exc_info:
            ensure_output_directory(blocker / "subdir")

        assert "Cannot create output directory" in str(exc_info.value)
