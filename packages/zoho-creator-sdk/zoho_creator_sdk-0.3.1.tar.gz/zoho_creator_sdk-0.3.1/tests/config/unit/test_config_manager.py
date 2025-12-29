"""Unit tests for :class:`zoho_creator_sdk.ConfigManager`."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from zoho_creator_sdk.config import ConfigManager
from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.models import APIConfig, AuthConfig


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_initialization_with_default_path(self) -> None:
        """ConfigManager initializes with default config path."""
        with patch.object(ConfigManager, "_find_config_file") as mock_find:
            mock_find.return_value = "/path/to/config"

            config_manager = ConfigManager()

            assert config_manager.config_file_path == "/path/to/config"
            mock_find.assert_called_once_with(None)

    def test_initialization_with_custom_path(self) -> None:
        """ConfigManager initializes with custom config path."""
        custom_path = "/custom/config.json"

        with patch("os.path.exists", return_value=True):
            config_manager = ConfigManager(custom_path)

            assert config_manager.config_file_path == custom_path

    @pytest.fixture
    def temp_config_file(self) -> Path:
        """Create a temporary config file for testing."""
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "api": {"datacenter": "US", "timeout": 30, "max_retries": 3},
                "auth": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uri": "https://test.com/callback",
                    "refresh_token": "test_refresh_token",
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            }
            json.dump(config_data, f)
            temp_path = Path(f.name)

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    def test_config_data_property_with_valid_file(self, temp_config_file: Path) -> None:
        """config_data property returns correct data from valid file."""
        config_manager = ConfigManager(str(temp_config_file))

        config_data = config_manager.config_data

        assert config_data["api"]["datacenter"] == "US"
        assert config_data["auth"]["client_id"] == "test_client_id"
        assert config_data["logging"]["level"] == "INFO"

    def test_config_data_property_with_missing_file(self) -> None:
        """config_data property handles missing file gracefully."""
        config_manager = ConfigManager("nonexistent_file.json")

        config_data = config_manager.config_data
        assert config_data == {}

    def test_get_api_config_success(self, temp_config_file: Path) -> None:
        """get_api_config returns valid APIConfig from file."""
        config_manager = ConfigManager(str(temp_config_file))

        api_config = config_manager.get_api_config()

        assert isinstance(api_config, APIConfig)
        assert api_config.datacenter == Datacenter.US

    def test_get_auth_config_success(self, temp_config_file: Path) -> None:
        """get_auth_config returns valid AuthConfig from file."""
        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigManager(str(temp_config_file))

            auth_config = config_manager.get_auth_config()

            assert isinstance(auth_config, AuthConfig)
            assert auth_config.client_id == "test_client_id"
            assert auth_config.client_secret == "test_client_secret"

    def test_get_logging_config_success(self, temp_config_file: Path) -> None:
        """get_logging_config returns logging configuration."""
        from zoho_creator_sdk.config import LoggingConfig

        config_manager = ConfigManager(str(temp_config_file))

        logging_config = config_manager.get_logging_config()

        assert isinstance(logging_config, LoggingConfig)
        assert logging_config.level == "INFO"

    def test_convert_datacenter_valid_values(self) -> None:
        """_convert_datacenter returns correct Datacenter for valid values."""
        config_manager = ConfigManager()

        assert config_manager._convert_datacenter("US") == Datacenter.US
        assert config_manager._convert_datacenter("EU") == Datacenter.EU
        assert config_manager._convert_datacenter("IN") == Datacenter.IN
        assert config_manager._convert_datacenter("AU") == Datacenter.AU
        assert config_manager._convert_datacenter("CA") == Datacenter.CA

    def test_convert_datacenter_invalid_value(self) -> None:
        """_convert_datacenter raises error for invalid value."""
        from zoho_creator_sdk.exceptions import ConfigurationError

        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError):
            config_manager._convert_datacenter("INVALID")

    def test_get_env_config(self) -> None:
        """_get_env_config returns config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ZOHO_CREATOR_DATACENTER": "EU",
                "ZOHO_CREATOR_TIMEOUT": "60",
                "ZOHO_CREATOR_CLIENT_ID": "env_client_id",
            },
        ):
            config_manager = ConfigManager()

            api_env_config = config_manager._get_env_config("api")

            assert api_env_config["datacenter"] == "EU"
            assert api_env_config["timeout"] == 60

    def test_get_env_config_no_env_vars(self) -> None:
        """_get_env_config returns empty dict when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigManager()

            env_config = config_manager._get_env_config("api")
            assert env_config == {}

    def test_is_float_valid_values(self) -> None:
        """_is_float returns True for valid float values."""
        assert ConfigManager._is_float("123.45") is True
        assert ConfigManager._is_float("100") is True
        assert ConfigManager._is_float("0.0") is True

    def test_is_float_invalid_values(self) -> None:
        """_is_float returns False for invalid float values."""
        assert ConfigManager._is_float("abc") is False
        assert ConfigManager._is_float("") is False
