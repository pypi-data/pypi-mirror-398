"""Tests for configuration management."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from resourcespace_cli.config import (
    CONFIG_KEYS,
    Config,
    clear_config,
    get_config_key_aliases,
    get_config_value,
    get_env_path,
    load_config,
    resolve_key_alias,
    set_config_value,
)
from resourcespace_cli.exceptions import ConfigurationError


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self) -> None:
        """Test Config has None defaults."""
        config = Config()
        assert config.api_url is None
        assert config.api_key is None
        assert config.user is None

    def test_with_values(self) -> None:
        """Test Config with provided values."""
        config = Config(
            api_url="https://example.com/api",
            api_key="secret_key",
            user="testuser",
        )
        assert config.api_url == "https://example.com/api"
        assert config.api_key == "secret_key"
        assert config.user == "testuser"

    def test_is_complete_true(self) -> None:
        """Test is_complete returns True when all values set."""
        config = Config(
            api_url="https://example.com/api",
            api_key="secret_key",
            user="testuser",
        )
        assert config.is_complete() is True

    def test_is_complete_false_missing_url(self) -> None:
        """Test is_complete returns False when api_url missing."""
        config = Config(api_key="secret_key", user="testuser")
        assert config.is_complete() is False

    def test_is_complete_false_missing_key(self) -> None:
        """Test is_complete returns False when api_key missing."""
        config = Config(api_url="https://example.com/api", user="testuser")
        assert config.is_complete() is False

    def test_is_complete_false_missing_user(self) -> None:
        """Test is_complete returns False when user missing."""
        config = Config(api_url="https://example.com/api", api_key="secret_key")
        assert config.is_complete() is False

    def test_to_dict(self) -> None:
        """Test to_dict returns proper dictionary."""
        config = Config(
            api_url="https://example.com/api",
            api_key="secret_key",
            user="testuser",
        )
        result = config.to_dict()

        assert result == {
            "RESOURCESPACE_API_URL": "https://example.com/api",
            "RESOURCESPACE_API_KEY": "secret_key",
            "RESOURCESPACE_USER": "testuser",
        }

    def test_frozen_immutable(self) -> None:
        """Test Config is immutable (frozen dataclass)."""
        config = Config(api_url="https://example.com/api")

        with pytest.raises(AttributeError):
            config.api_url = "new_url"  # type: ignore[misc]


class TestGetEnvPath:
    """Tests for get_env_path function."""

    def test_default_path(self, clean_env: None) -> None:
        """Test default .env path is returned."""
        path = get_env_path()
        assert path.name == ".env"

    def test_env_override(self, tmp_path: Path) -> None:
        """Test RESOURCESPACE_ENV_PATH override."""
        custom_path = tmp_path / "custom.env"
        os.environ["RESOURCESPACE_ENV_PATH"] = str(custom_path)

        try:
            path = get_env_path()
            assert path == custom_path
        finally:
            del os.environ["RESOURCESPACE_ENV_PATH"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_env_file(
        self, temp_env_file: Path
    ) -> None:
        """Test loading config from .env file."""
        # Clear any existing env vars first
        import os
        for key in ["RESOURCESPACE_API_URL", "RESOURCESPACE_API_KEY", "RESOURCESPACE_USER"]:
            os.environ.pop(key, None)

        temp_env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com/api\n"
            "RESOURCESPACE_API_KEY=file_key\n"
            "RESOURCESPACE_USER=fileuser\n"
        )

        config = load_config()

        assert config.api_url == "https://example.com/api"
        assert config.api_key == "file_key"
        assert config.user == "fileuser"

    def test_env_vars_take_precedence(
        self, temp_env_file: Path
    ) -> None:
        """Test environment variables override .env file."""
        temp_env_file.write_text(
            "RESOURCESPACE_API_URL=https://file.com/api\n"
            "RESOURCESPACE_API_KEY=file_key\n"
            "RESOURCESPACE_USER=fileuser\n"
        )

        os.environ["RESOURCESPACE_API_URL"] = "https://env.com/api"

        try:
            config = load_config()
            assert config.api_url == "https://env.com/api"
            assert config.api_key == "file_key"  # Still from file
        finally:
            del os.environ["RESOURCESPACE_API_URL"]

    def test_missing_env_file(self, tmp_path: Path) -> None:
        """Test loading when .env file doesn't exist."""
        os.environ["RESOURCESPACE_ENV_PATH"] = str(tmp_path / "nonexistent.env")
        os.environ.pop("RESOURCESPACE_API_URL", None)
        os.environ.pop("RESOURCESPACE_API_KEY", None)
        os.environ.pop("RESOURCESPACE_USER", None)

        try:
            config = load_config()
            assert config.api_url is None
            assert config.api_key is None
            assert config.user is None
        finally:
            del os.environ["RESOURCESPACE_ENV_PATH"]


class TestSetConfigValue:
    """Tests for set_config_value function."""

    def test_set_valid_key(self, temp_env_file: Path) -> None:
        """Test setting a valid configuration key."""
        set_config_value("RESOURCESPACE_API_URL", "https://new.com/api")

        content = temp_env_file.read_text()
        assert "RESOURCESPACE_API_URL" in content
        assert "https://new.com/api" in content

    def test_set_all_valid_keys(self, temp_env_file: Path) -> None:
        """Test setting all valid configuration keys."""
        for key in CONFIG_KEYS:
            set_config_value(key, f"value_for_{key}")

        content = temp_env_file.read_text()
        for key in CONFIG_KEYS:
            assert key in content

    def test_invalid_key_raises_error(self, temp_env_file: Path) -> None:
        """Test setting invalid key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            set_config_value("INVALID_KEY", "value")

        assert "Invalid config key" in str(exc_info.value)

    def test_creates_env_file_if_missing(self, tmp_path: Path) -> None:
        """Test .env file is created if it doesn't exist."""
        env_file = tmp_path / "new.env"
        os.environ["RESOURCESPACE_ENV_PATH"] = str(env_file)

        try:
            assert not env_file.exists()
            set_config_value("RESOURCESPACE_API_URL", "https://example.com")
            assert env_file.exists()
        finally:
            del os.environ["RESOURCESPACE_ENV_PATH"]


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_existing_value(self, temp_env_file: Path) -> None:
        """Test getting an existing configuration value."""
        temp_env_file.write_text("RESOURCESPACE_API_URL=https://example.com/api\n")

        # Clear any env vars that might interfere
        os.environ.pop("RESOURCESPACE_API_URL", None)

        value = get_config_value("RESOURCESPACE_API_URL")
        assert value == "https://example.com/api"

    def test_get_missing_value(self, temp_env_file: Path, clean_env: None) -> None:
        """Test getting a missing configuration value returns None."""
        value = get_config_value("RESOURCESPACE_API_KEY")
        assert value is None

    def test_invalid_key_raises_error(self, temp_env_file: Path) -> None:
        """Test getting invalid key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            get_config_value("INVALID_KEY")

        assert "Invalid config key" in str(exc_info.value)


class TestClearConfig:
    """Tests for clear_config function."""

    def test_clear_specific_key(self, temp_env_file: Path) -> None:
        """Test clearing a specific configuration key."""
        temp_env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com\n"
            "RESOURCESPACE_API_KEY=secret\n"
        )

        cleared = clear_config("RESOURCESPACE_API_URL")

        assert "RESOURCESPACE_API_URL" in cleared
        content = temp_env_file.read_text()
        assert "RESOURCESPACE_API_URL" not in content
        assert "RESOURCESPACE_API_KEY" in content

    def test_clear_all_keys(self, temp_env_file: Path) -> None:
        """Test clearing all configuration keys."""
        temp_env_file.write_text(
            "RESOURCESPACE_API_URL=https://example.com\n"
            "RESOURCESPACE_API_KEY=secret\n"
            "RESOURCESPACE_USER=testuser\n"
        )

        cleared = clear_config()

        assert len(cleared) == 3
        content = temp_env_file.read_text()
        for key in CONFIG_KEYS:
            assert key not in content

    def test_clear_nonexistent_key(self, temp_env_file: Path) -> None:
        """Test clearing key that doesn't exist returns empty list."""
        temp_env_file.write_text("")

        cleared = clear_config("RESOURCESPACE_API_URL")

        assert cleared == []

    def test_clear_missing_env_file(self, tmp_path: Path) -> None:
        """Test clearing when .env file doesn't exist."""
        os.environ["RESOURCESPACE_ENV_PATH"] = str(tmp_path / "nonexistent.env")

        try:
            cleared = clear_config()
            assert cleared == []
        finally:
            del os.environ["RESOURCESPACE_ENV_PATH"]

    def test_invalid_key_raises_error(self, temp_env_file: Path) -> None:
        """Test clearing invalid key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            clear_config("INVALID_KEY")

        assert "Invalid config key" in str(exc_info.value)


class TestGetConfigKeyAliases:
    """Tests for get_config_key_aliases function."""

    def test_returns_dict(self) -> None:
        """Test that function returns a dictionary."""
        aliases = get_config_key_aliases()
        assert isinstance(aliases, dict)

    def test_all_aliases_map_to_valid_keys(self) -> None:
        """Test all aliases map to valid CONFIG_KEYS."""
        aliases = get_config_key_aliases()
        for alias, key in aliases.items():
            assert key in CONFIG_KEYS

    def test_common_aliases_exist(self) -> None:
        """Test common user-friendly aliases exist."""
        aliases = get_config_key_aliases()
        assert "url" in aliases
        assert "key" in aliases
        assert "user" in aliases


class TestResolveKeyAlias:
    """Tests for resolve_key_alias function."""

    def test_resolve_url_alias(self) -> None:
        """Test resolving 'url' alias."""
        assert resolve_key_alias("url") == "RESOURCESPACE_API_URL"

    def test_resolve_key_alias(self) -> None:
        """Test resolving 'key' alias."""
        assert resolve_key_alias("key") == "RESOURCESPACE_API_KEY"

    def test_resolve_user_alias(self) -> None:
        """Test resolving 'user' alias."""
        assert resolve_key_alias("user") == "RESOURCESPACE_USER"

    def test_case_insensitive(self) -> None:
        """Test alias resolution is case insensitive."""
        assert resolve_key_alias("URL") == "RESOURCESPACE_API_URL"
        assert resolve_key_alias("Key") == "RESOURCESPACE_API_KEY"

    def test_full_key_name(self) -> None:
        """Test that full key names work (converted to uppercase)."""
        assert resolve_key_alias("resourcespace_api_url") == "RESOURCESPACE_API_URL"

    def test_unknown_alias_uppercased(self) -> None:
        """Test unknown alias is uppercased and returned as-is."""
        assert resolve_key_alias("unknown_key") == "UNKNOWN_KEY"
