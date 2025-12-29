"""Comprehensive unit tests for config module."""

from __future__ import annotations

import json
import os
from unittest.mock import mock_open, patch

import pytest

from zoho_creator_sdk.config import (
    ENV_VAR_MAP,
    ConfigManager,
    LoggingConfig,
    setup_logging,
)
from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.exceptions import ConfigurationError
from zoho_creator_sdk.models import APIConfig, AuthConfig


class TestConfigManagerComprehensive:
    """Comprehensive test cases for ConfigManager."""

    def test_find_config_file_custom_path_exists(self) -> None:
        """ConfigManager finds config file when custom path exists."""
        custom_path = "/custom/test_config.json"

        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == custom_path

            config_manager = ConfigManager(custom_path)

            assert config_manager.config_file_path == custom_path

    def test_find_config_file_custom_path_not_exists(self) -> None:
        """ConfigManager returns None when custom path doesn't exist."""
        custom_path = "/nonexistent/config.json"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            config_manager = ConfigManager(custom_path)

            assert config_manager.config_file_path is None

    def test_find_config_file_no_config_found(self) -> None:
        """ConfigManager returns None when no config file found."""
        with patch("os.path.exists", return_value=False):
            config_manager = ConfigManager()

            assert config_manager.config_file_path is None

    # Note: search order testing is covered by other tests

    def test_load_config_file_json_success(self) -> None:
        """_load_config_file successfully loads valid JSON file."""
        config_data = {"api": {"datacenter": "US"}, "auth": {"client_id": "test"}}

        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            result = ConfigManager()._load_config_file("test.json")

            assert result == config_data

    def test_load_config_file_json_invalid_format(self) -> None:
        """_load_config_file handles JSON file that doesn't contain a dict."""
        with patch("builtins.open", mock_open(read_data='["not", "a", "dict"]')):
            with patch("zoho_creator_sdk.config.logger") as mock_logger:
                result = ConfigManager()._load_config_file("test.json")

                assert result == {}
                mock_logger.warning.assert_called_once()

    def test_load_config_file_json_decode_error(self) -> None:
        """_load_config_file handles JSON decode errors."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("zoho_creator_sdk.config.logger") as mock_logger:
                result = ConfigManager()._load_config_file("test.json")

                assert result == {}
                mock_logger.warning.assert_called_once()

    def test_load_config_file_os_error(self) -> None:
        """_load_config_file handles OS errors."""
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch("zoho_creator_sdk.config.logger") as mock_logger:
                result = ConfigManager()._load_config_file("test.json")

                assert result == {}
                mock_logger.warning.assert_called_once()

    def test_config_data_property_caching(self) -> None:
        """config_data property caches the loaded config."""
        config_data = {"test": "data"}

        config_manager = ConfigManager()
        config_manager.config_file_path = "/tmp/test_config.json"  # Ensure path is set
        with patch.object(
            config_manager, "_load_config_file", return_value=config_data
        ) as mock_load:
            # First call should load the file
            result1 = config_manager.config_data
            # Second call should use cached value
            result2 = config_manager.config_data

            assert result1 == config_data
            assert result2 == config_data
            mock_load.assert_called_once()

    def test_config_data_property_no_file(self) -> None:
        """config_data property returns empty dict when no config file."""
        config_manager = ConfigManager()
        config_manager.config_file_path = None

        result = config_manager.config_data
        assert result == {}

    def test_load_config_env_vars_take_precedence(self) -> None:
        """Environment variables take precedence over file config."""
        file_config = {"api": {"datacenter": "US", "timeout": 30}}
        env_config = {"datacenter": "EU", "timeout": 60}

        config_manager = ConfigManager()
        config_manager._config_data = (
            file_config  # Set directly instead of patching property
        )

        with patch.object(config_manager, "_get_env_config", return_value=env_config):
            with patch.object(
                config_manager, "_convert_datacenter", return_value=Datacenter.EU
            ):
                result = config_manager._load_config("api", APIConfig)

                assert result.datacenter == Datacenter.EU
                assert result.timeout == 60

    def test_load_config_with_datacenter_conversion(self) -> None:
        """_load_config properly converts datacenter values."""
        config = {"datacenter": "eu"}

        config_manager = ConfigManager()
        config_manager._config_data = {
            "api": config
        }  # Set directly instead of patching property

        with patch.object(config_manager, "_get_env_config", return_value={}):
            with patch.object(
                config_manager, "_convert_datacenter", return_value=Datacenter.EU
            ):
                result = config_manager._load_config("api", APIConfig)

                assert result.datacenter == Datacenter.EU
                config_manager._convert_datacenter.assert_called_once_with("eu")

    def test_load_config_validation_error(self) -> None:
        """_load_config raises ConfigurationError on validation failure."""
        invalid_config = {"datacenter": "INVALID_DATACENTER"}

        config_manager = ConfigManager()
        config_manager._config_data = {
            "api": invalid_config
        }  # Set directly instead of patching property

        with patch.object(config_manager, "_get_env_config", return_value={}):
            with patch.object(
                config_manager,
                "_convert_datacenter",
                side_effect=ConfigurationError("Invalid datacenter"),
            ):
                with pytest.raises(ConfigurationError) as exc_info:
                    config_manager._load_config("api", APIConfig)

                assert "Invalid datacenter" in str(exc_info.value)

    def test_convert_datacenter_lowercase(self) -> None:
        """_convert_datacenter handles lowercase values."""
        config_manager = ConfigManager()

        assert config_manager._convert_datacenter("us") == Datacenter.US
        assert config_manager._convert_datacenter("eu") == Datacenter.EU
        assert config_manager._convert_datacenter("in") == Datacenter.IN

    def test_convert_datacenter_already_enum(self) -> None:
        """_convert_datacenter returns Datacenter enum as-is."""
        config_manager = ConfigManager()

        result = config_manager._convert_datacenter(Datacenter.EU)
        assert result == Datacenter.EU

    def test_convert_datacenter_invalid_string(self) -> None:
        """_convert_datacenter raises error for invalid string."""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError) as exc_info:
            config_manager._convert_datacenter("INVALID")

        assert "Invalid datacenter: INVALID" in str(exc_info.value)

    def test_convert_datacenter_invalid_type(self) -> None:
        """_convert_datacenter raises error for invalid type."""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError) as exc_info:
            config_manager._convert_datacenter(123)

        assert "Invalid datacenter type" in str(exc_info.value)

    def test_get_env_config_boolean_conversion(self) -> None:
        """_get_env_config properly converts boolean values."""
        test_cases = [
            ("true", True),
            ("yes", True),
            ("on", True),
            ("1", True),
            ("false", False),
            ("no", False),
            ("off", False),
            ("0", False),
            ("TRUE", True),
            ("FALSE", False),
        ]

        config_manager = ConfigManager()
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"ZOHO_CREATOR_DEMO_USER_NAME": env_value}):
                result = config_manager._get_env_config("api")
                assert result.get("demo_user_name") == expected

    def test_get_env_config_numeric_conversion(self) -> None:
        """_get_env_config properly converts numeric values."""
        with patch.dict(
            os.environ,
            {"ZOHO_CREATOR_TIMEOUT": "120", "ZOHO_CREATOR_RETRY_DELAY": "2.5"},
        ):
            config_manager = ConfigManager()
            result = config_manager._get_env_config("api")

            assert result.get("timeout") == 120
            assert result.get("retry_delay") == 2.5

    def test_get_env_config_string_values(self) -> None:
        """_get_env_config handles string values correctly."""
        with patch.dict(
            os.environ,
            {
                "ZOHO_CREATOR_API_KEY": "test_key_123",
                "ZOHO_CREATOR_ENVIRONMENT": "development",
            },
        ):
            config_manager = ConfigManager()

            # Test auth section for api_key
            auth_result = config_manager._get_env_config("auth")
            assert auth_result.get("api_key") == "test_key_123"

            # Test api section for environment
            api_result = config_manager._get_env_config("api")
            assert api_result.get("environment") == "development"

    def test_get_env_config_section_not_found(self) -> None:
        """_get_env_config returns empty dict for unknown section."""
        config_manager = ConfigManager()

        with patch.dict(os.environ, {"SOME_VAR": "value"}):
            result = config_manager._get_env_config("unknown_section")
            assert result == {}

    def test_get_env_config_ignores_none_values(self) -> None:
        """_get_env_config ignores environment variables with None values."""
        config_manager = ConfigManager()

        with patch.dict(os.environ, {"ZOHO_CREATOR_ENVIRONMENT": ""}):
            with patch("os.getenv", return_value=None):
                result = config_manager._get_env_config("api")
                assert "environment" not in result

    def test_get_api_config_caching(self) -> None:
        """get_api_config caches the result."""
        config_manager = ConfigManager()
        test_config = APIConfig(dc="US", api_key="test")

        with patch.object(
            config_manager, "_load_config", return_value=test_config
        ) as mock_load:
            # First call
            result1 = config_manager.get_api_config()
            # Second call should use cache
            result2 = config_manager.get_api_config()

            assert result1 is test_config
            assert result2 is test_config
            mock_load.assert_called_once_with("api", APIConfig)

    def test_get_auth_config_caching(self) -> None:
        """get_auth_config caches the result."""
        config_manager = ConfigManager()
        test_config = AuthConfig(
            client_id="test",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            refresh_token="test_refresh_token",
        )

        with patch.object(
            config_manager, "_load_config", return_value=test_config
        ) as mock_load:
            result1 = config_manager.get_auth_config()
            result2 = config_manager.get_auth_config()

            assert result1 is test_config
            assert result2 is test_config
            mock_load.assert_called_once_with("auth", AuthConfig)

    def test_get_logging_config_caching(self) -> None:
        """get_logging_config caches the result."""
        config_manager = ConfigManager()

        with patch.object(config_manager, "_load_config") as mock_load:
            mock_load.return_value = LoggingConfig(level="DEBUG")

            result1 = config_manager.get_logging_config()
            result2 = config_manager.get_logging_config()

            assert isinstance(result1, LoggingConfig)
            assert result1 is result2
            mock_load.assert_called_once_with("logging", LoggingConfig)

    def test_is_float_edge_cases(self) -> None:
        """_is_float handles edge cases correctly."""
        # Valid floats
        assert ConfigManager._is_float("123.456") is True
        assert ConfigManager._is_float("-123.45") is True
        assert ConfigManager._is_float(".5") is True
        assert ConfigManager._is_float("0.0") is True
        assert ConfigManager._is_float("100") is True  # Integers are valid floats

        # Invalid floats
        assert ConfigManager._is_float("") is False
        assert ConfigManager._is_float("123.45.67") is False
        assert ConfigManager._is_float("abc") is False
        assert ConfigManager._is_float("12a") is False


class TestLoggingConfig:
    """Test cases for LoggingConfig."""

    def test_logging_config_default_values(self) -> None:
        """LoggingConfig has correct default values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        assert config.file_path is None

    def test_logging_config_custom_values(self) -> None:
        """LoggingConfig accepts custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format="%(name)s - %(message)s",
            file_path="/var/log/zoho.log",
        )

        assert config.level == "DEBUG"
        assert config.format == "%(name)s - %(message)s"
        assert config.file_path == "/var/log/zoho.log"


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_basic(self) -> None:
        """setup_logging configures basic logging."""
        config = LoggingConfig(level="DEBUG")

        with patch("logging.basicConfig") as mock_basicConfig:
            setup_logging(config)

            mock_basicConfig.assert_called_once_with(
                level="DEBUG",
                format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                filename=None,
                filemode="w",
            )

    def test_setup_logging_with_file(self) -> None:
        """setup_logging configures logging with file output."""
        config = LoggingConfig(
            level="INFO", format="%(message)s", file_path="/tmp/test.log"
        )

        with patch("logging.basicConfig") as mock_basicConfig:
            setup_logging(config)

            mock_basicConfig.assert_called_once_with(
                level="INFO",
                format="%(message)s",
                filename="/tmp/test.log",
                filemode="a",
            )

    def test_setup_logging_case_insensitive_level(self) -> None:
        """setup_logging handles case-insensitive log levels."""
        config = LoggingConfig(level="warning")

        with patch("logging.basicConfig") as mock_basicConfig:
            setup_logging(config)

            # Check that level was converted to uppercase
            args, kwargs = mock_basicConfig.call_args
            assert kwargs["level"] == "WARNING"


class TestEnvVarMap:
    """Test cases for ENV_VAR_MAP constant."""

    def test_env_var_map_structure(self) -> None:
        """ENV_VAR_MAP has correct structure."""
        assert "api" in ENV_VAR_MAP
        assert "auth" in ENV_VAR_MAP

        api_vars = ENV_VAR_MAP["api"]
        assert "datacenter" in api_vars
        assert "timeout" in api_vars
        assert "max_retries" in api_vars
        assert "retry_delay" in api_vars
        assert "environment" in api_vars
        assert "demo_user_name" in api_vars

        auth_vars = ENV_VAR_MAP["auth"]
        assert "api_key" in auth_vars
        assert "client_id" in auth_vars
        assert "client_secret" in auth_vars
        assert "redirect_uri" in auth_vars
        assert "refresh_token" in auth_vars

    def test_env_var_map_values(self) -> None:
        """ENV_VAR_MAP contains correct environment variable names."""
        api_vars = ENV_VAR_MAP["api"]
        assert api_vars["datacenter"][0] == "ZOHO_CREATOR_DATACENTER"
        assert api_vars["timeout"][0] == "ZOHO_CREATOR_TIMEOUT"

        auth_vars = ENV_VAR_MAP["auth"]
        assert auth_vars["client_id"][0] == "ZOHO_CREATOR_CLIENT_ID"
        assert auth_vars["api_key"][0] == "ZOHO_CREATOR_API_KEY"

    def test_env_var_map_defaults(self) -> None:
        """ENV_VAR_MAP contains correct default values."""
        api_vars = ENV_VAR_MAP["api"]
        assert api_vars["datacenter"][1] == "US"
        assert api_vars["timeout"][1] == 30
        assert api_vars["max_retries"][1] == 3
        assert api_vars["retry_delay"][1] == 1.0
