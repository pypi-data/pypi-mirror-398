"""File handling utilities for ResourceSpace CLI."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing/replacing problematic characters.

    Args:
        filename: The original filename.

    Returns:
        Sanitized filename safe for the filesystem.
    """
    # Characters that are problematic on Windows/Unix
    invalid_chars = '<>:"/\\|?*'
    result = filename
    for char in invalid_chars:
        result = result.replace(char, "_")
    return result.strip()


def resolve_filename_conflict(
    output_dir: Path,
    filename: str,
    resource_id: int,
) -> Path:
    """Resolve filename conflicts by adding resource ID suffix.

    If filename.ext already exists, returns filename_<resource_id>.ext

    Args:
        output_dir: The output directory.
        filename: The original filename.
        resource_id: The resource ID to use as suffix.

    Returns:
        Path object with conflict-resolved filename.
    """
    filepath = output_dir / filename

    if not filepath.exists():
        return filepath

    # Add resource ID before the extension
    stem = filepath.stem
    suffix = filepath.suffix
    new_filename = f"{stem}_{resource_id}{suffix}"

    return output_dir / new_filename


def extract_filename_from_url(url: str) -> str:
    """Extract filename from a download URL.

    Args:
        url: The download URL.

    Returns:
        Extracted filename or a default.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = Path(path).name

    return filename if filename else "download"


def ensure_output_directory(output_dir: Path) -> None:
    """Ensure the output directory exists.

    Args:
        output_dir: The directory path.

    Raises:
        DownloadError: If directory cannot be created.
    """
    from resourcespace_cli.exceptions import DownloadError

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise DownloadError(f"Cannot create output directory '{output_dir}': {e}") from e
