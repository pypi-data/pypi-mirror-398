"""
Configuration management for the Zoho Creator SDK.
"""

import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, cast

from pydantic import BaseModel, ValidationError

from .constants import Datacenter
from .exceptions import ConfigurationError
from .models import APIConfig, AuthConfig

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

ENV_VAR_MAP: Mapping[str, Mapping[str, Tuple[str, Any]]] = {
    "api": {
        "datacenter": ("ZOHO_CREATOR_DATACENTER", "US"),
        "timeout": ("ZOHO_CREATOR_TIMEOUT", 30),
        "max_retries": ("ZOHO_CREATOR_MAX_RETRIES", 3),
        "retry_delay": ("ZOHO_CREATOR_RETRY_DELAY", 1.0),
        "environment": ("ZOHO_CREATOR_ENVIRONMENT", None),
        "demo_user_name": ("ZOHO_CREATOR_DEMO_USER_NAME", None),
    },
    "auth": {
        "api_key": ("ZOHO_CREATOR_API_KEY", None),
        "client_id": ("ZOHO_CREATOR_CLIENT_ID", None),
        "client_secret": ("ZOHO_CREATOR_CLIENT_SECRET", None),
        "redirect_uri": ("ZOHO_CREATOR_REDIRECT_URI", None),
        "refresh_token": ("ZOHO_CREATOR_REFRESH_TOKEN", None),
    },
}


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = "INFO"
    format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    file_path: Optional[str] = None


class ConfigManager:
    """Manages the configuration for the Zoho Creator SDK."""

    def __init__(self, config_file_path: Optional[str] = None) -> None:
        self.config_file_path = self._find_config_file(config_file_path)
        self._config_data: Optional[Mapping[str, Any]] = None
        self._api_config: Optional[APIConfig] = None
        self._auth_config: Optional[AuthConfig] = None
        self._logging_config: Optional[LoggingConfig] = None

    def _find_config_file(self, config_file_path: Optional[str]) -> Optional[str]:
        """Find the configuration file in the default locations."""
        if config_file_path and os.path.exists(config_file_path):
            return config_file_path

        search_paths = [
            Path("./zoho_creator_config.json"),
            Path.home() / ".zoho_creator" / "config.json",
            Path("/etc") / "zoho_creator" / "config.json",
        ]
        for path in search_paths:
            if path.exists():
                return str(path)
        return None

    @property
    def config_data(self) -> Mapping[str, Any]:
        """Load and return the configuration data from the file."""
        if self._config_data is None and self.config_file_path:
            self._config_data = self._load_config_file(self.config_file_path)
        return self._config_data or {}

    def _load_config_file(self, file_path: str) -> Mapping[str, Any]:
        """Load a configuration file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(".json"):
                    data = json.load(f)
                    if not isinstance(data, dict):
                        logger.warning(
                            "Config file at %s does not contain a JSON object",
                            file_path,
                        )
                        return {}
                    return cast(Mapping[str, Any], data)
                # Add support for other formats like YAML or TOML here if needed
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load config file at %s: %s", file_path, e)
        return {}

    def get_api_config(self) -> APIConfig:
        """Get the API configuration."""
        if self._api_config is None:
            self._api_config = self._load_config("api", APIConfig)
        return self._api_config

    def get_auth_config(self) -> AuthConfig:
        """Get the authentication configuration."""
        if self._auth_config is None:
            self._auth_config = self._load_config("auth", AuthConfig)
        return self._auth_config

    def get_logging_config(self) -> LoggingConfig:
        """Get the logging configuration."""
        if self._logging_config is None:
            self._logging_config = self._load_config("logging", LoggingConfig)
        return self._logging_config

    def _load_config(self, section: str, config_class: Type[T]) -> T:
        """Load a specific section of the configuration."""
        env_config = self._get_env_config(section)
        file_config = self.config_data.get(section, {})
        # Environment variables take precedence
        merged_config = {**file_config, **env_config}

        # Convert datacenter string to enum if needed
        if section == "api" and "datacenter" in merged_config:
            merged_config["datacenter"] = self._convert_datacenter(
                merged_config["datacenter"]
            )

        try:
            return config_class(**merged_config)
        except ValidationError as e:
            raise ConfigurationError(
                f"Invalid configuration in section '{section}': {e}"
            ) from e

    def _convert_datacenter(self, datacenter_value: Any) -> Datacenter:
        """Convert a datacenter value to the proper Datacenter enum."""
        if isinstance(datacenter_value, str):
            # Convert string to enum
            datacenter_map = {
                "US": Datacenter.US,
                "EU": Datacenter.EU,
                "IN": Datacenter.IN,
                "AU": Datacenter.AU,
                "CA": Datacenter.CA,
            }
            if datacenter_value.upper() in datacenter_map:
                return datacenter_map[datacenter_value.upper()]
            raise ConfigurationError(f"Invalid datacenter: {datacenter_value}")
        if isinstance(datacenter_value, Datacenter):
            return datacenter_value
        raise ConfigurationError(f"Invalid datacenter type: {type(datacenter_value)}")

    def _get_env_config(self, section: str) -> Mapping[str, Any]:
        """Get configuration from environment variables."""
        config: Dict[str, Any] = {}
        for key, (env_var, _) in ENV_VAR_MAP.get(section, {}).items():
            value = os.getenv(env_var)
            if value is not None:
                # Handle boolean and numeric values from environment variables
                # Check for boolean values first (including numeric booleans)
                if value.lower() in ("true", "false", "yes", "no", "on", "off"):
                    config[key] = value.lower() in ("true", "yes", "on")
                elif value.lower() == "1" or value == "1.0":
                    config[key] = True
                elif value.lower() == "0" or value == "0.0":
                    config[key] = False
                elif value.isdigit():
                    config[key] = int(value)
                elif self._is_float(value):
                    # Only convert to float if it's not meant to be a boolean
                    config[key] = float(value)
                else:
                    config[key] = value
        return config

    @staticmethod
    def _is_float(value: str) -> bool:
        """Check if a string value represents a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False


def setup_logging(config: LoggingConfig) -> None:
    """Set up logging for the SDK."""
    logging.basicConfig(
        level=config.level.upper(),
        format=config.format,
        filename=config.file_path,
        filemode="a" if config.file_path else "w",
    )
