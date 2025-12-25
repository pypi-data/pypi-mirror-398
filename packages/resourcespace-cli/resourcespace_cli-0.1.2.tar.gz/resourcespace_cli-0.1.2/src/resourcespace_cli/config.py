"""Configuration management for ResourceSpace CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, set_key, unset_key

from resourcespace_cli.exceptions import ConfigurationError

# Configuration key constants
CONFIG_KEYS: tuple[str, ...] = (
    "RESOURCESPACE_API_URL",
    "RESOURCESPACE_API_KEY",
    "RESOURCESPACE_USER",
)

# Default .env file location (project directory)
DEFAULT_ENV_PATH: Path = Path(__file__).parent.parent.parent / ".env"


@dataclass(frozen=True)
class Config:
    """ResourceSpace configuration settings."""

    api_url: str | None = None
    api_key: str | None = None
    user: str | None = None

    def is_complete(self) -> bool:
        """Check if all required configuration values are set."""
        return all([self.api_url, self.api_key, self.user])

    def to_dict(self) -> dict[str, str | None]:
        """Convert configuration to dictionary."""
        return {
            "RESOURCESPACE_API_URL": self.api_url,
            "RESOURCESPACE_API_KEY": self.api_key,
            "RESOURCESPACE_USER": self.user,
        }


def get_env_path() -> Path:
    """Get the path to the .env file.

    Returns the project directory .env file path.
    Can be overridden by RESOURCESPACE_ENV_PATH environment variable.
    """
    env_override = os.environ.get("RESOURCESPACE_ENV_PATH")
    if env_override:
        return Path(env_override)
    return DEFAULT_ENV_PATH


def load_config() -> Config:
    """Load configuration from .env file and environment variables.

    Environment variables take precedence over .env file values.

    Returns:
        Config object with loaded values.
    """
    env_path = get_env_path()

    # Load from .env file (returns empty dict if file doesn't exist)
    env_values: dict[str, str | None] = {}
    if env_path.exists():
        env_values = dotenv_values(env_path)

    # Environment variables take precedence
    api_url = os.environ.get("RESOURCESPACE_API_URL") or env_values.get(
        "RESOURCESPACE_API_URL"
    )
    api_key = os.environ.get("RESOURCESPACE_API_KEY") or env_values.get(
        "RESOURCESPACE_API_KEY"
    )
    user = os.environ.get("RESOURCESPACE_USER") or env_values.get("RESOURCESPACE_USER")

    return Config(
        api_url=api_url,
        api_key=api_key,
        user=user,
    )


def set_config_value(key: str, value: str) -> None:
    """Set a configuration value in the .env file.

    Args:
        key: Configuration key (must be one of CONFIG_KEYS).
        value: Value to set.

    Raises:
        ConfigurationError: If key is not valid.
    """
    if key not in CONFIG_KEYS:
        valid_keys = ", ".join(CONFIG_KEYS)
        msg = f"Invalid config key '{key}'. Valid keys: {valid_keys}"
        raise ConfigurationError(msg)

    env_path = get_env_path()

    # Create .env file if it doesn't exist
    if not env_path.exists():
        env_path.touch()

    set_key(str(env_path), key, value)


def get_config_value(key: str) -> str | None:
    """Get a single configuration value.

    Args:
        key: Configuration key to retrieve.

    Returns:
        The configuration value, or None if not set.

    Raises:
        ConfigurationError: If key is not valid.
    """
    if key not in CONFIG_KEYS:
        valid_keys = ", ".join(CONFIG_KEYS)
        msg = f"Invalid config key '{key}'. Valid keys: {valid_keys}"
        raise ConfigurationError(msg)

    config = load_config()
    return config.to_dict().get(key)


def clear_config(key: str | None = None) -> list[str]:
    """Clear configuration values from the .env file.

    Args:
        key: Specific key to clear, or None to clear all.

    Returns:
        List of keys that were cleared.

    Raises:
        ConfigurationError: If specified key is not valid.
    """
    env_path = get_env_path()

    if not env_path.exists():
        return []

    keys_to_clear: list[str]
    if key:
        if key not in CONFIG_KEYS:
            valid_keys = ", ".join(CONFIG_KEYS)
            msg = f"Invalid config key '{key}'. Valid keys: {valid_keys}"
            raise ConfigurationError(msg)
        keys_to_clear = [key]
    else:
        keys_to_clear = list(CONFIG_KEYS)

    cleared: list[str] = []
    for k in keys_to_clear:
        result = unset_key(str(env_path), k)
        # unset_key returns (success, key_name) tuple
        if result[0]:
            cleared.append(k)

    return cleared


def get_config_key_aliases() -> dict[str, str]:
    """Get user-friendly aliases for configuration keys.

    Returns:
        Mapping from alias to full key name.
    """
    return {
        "url": "RESOURCESPACE_API_URL",
        "api-url": "RESOURCESPACE_API_URL",
        "api_url": "RESOURCESPACE_API_URL",
        "key": "RESOURCESPACE_API_KEY",
        "api-key": "RESOURCESPACE_API_KEY",
        "api_key": "RESOURCESPACE_API_KEY",
        "user": "RESOURCESPACE_USER",
        "username": "RESOURCESPACE_USER",
    }


def resolve_key_alias(key: str) -> str:
    """Resolve a key alias to the full configuration key.

    Args:
        key: Key name or alias.

    Returns:
        Full configuration key name.
    """
    aliases = get_config_key_aliases()
    return aliases.get(key.lower(), key.upper())
