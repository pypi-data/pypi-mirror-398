"""Unit tests for :mod:`zoho_creator_sdk.config` components."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from zoho_creator_sdk.config import ConfigManager, LoggingConfig, setup_logging
from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.exceptions import ConfigurationError
from zoho_creator_sdk.models import APIConfig


def _make_config(tmp_path: Path, data: dict[str, Any]) -> str:
    path = tmp_path / "zoho_creator_config.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_find_config_file_prefers_explicit_path(tmp_path: Path) -> None:
    explicit = _make_config(tmp_path, {"api": {"timeout": 99}})

    manager = ConfigManager(config_file_path=explicit)

    assert manager.config_file_path == explicit
    assert manager.config_data["api"]["timeout"] == 99


def test_find_config_file_searches_default_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "zoho_creator_config.json"
    config_path.write_text(json.dumps({"api": {"timeout": 15}}))
    monkeypatch.chdir(tmp_path)

    manager = ConfigManager()

    assert Path(manager.config_file_path).resolve() == config_path.resolve()
    assert manager.config_data["api"]["timeout"] == 15


def test_load_config_file_handles_invalid_json(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    file_path = tmp_path / "zoho_creator_config.json"
    file_path.write_text("not-json")

    manager = ConfigManager(config_file_path=str(file_path))

    with caplog.at_level(logging.WARNING):
        assert manager.config_data == {}


def test_load_config_file_non_object_returns_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    file_path = tmp_path / "zoho_creator_config.json"
    file_path.write_text(json.dumps([1, 2, 3]))

    manager = ConfigManager(config_file_path=str(file_path))

    with caplog.at_level(logging.WARNING):
        assert manager.config_data == {}


def test_get_api_config_merges_env_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _make_config(tmp_path, {"api": {"timeout": 20, "retry_delay": 2}})
    monkeypatch.setenv("ZOHO_CREATOR_TIMEOUT", "45")
    monkeypatch.setenv("ZOHO_CREATOR_MAX_RETRIES", "4")
    monkeypatch.setenv("ZOHO_CREATOR_RETRY_DELAY", "3.5")

    manager = ConfigManager(config_file_path=config_path)
    api_config = manager.get_api_config()

    assert isinstance(api_config, APIConfig)
    assert api_config.timeout == 45
    assert api_config.retry_delay == pytest.approx(3.5)
    assert api_config.max_retries == 4


def test_convert_datacenter_accepts_string_and_enum() -> None:
    manager = ConfigManager()

    assert manager._convert_datacenter("eu") == Datacenter.EU
    assert manager._convert_datacenter(Datacenter.CA) == Datacenter.CA

    with pytest.raises(ConfigurationError):
        manager._convert_datacenter("unknown")


def test_convert_datacenter_invalid_type() -> None:
    manager = ConfigManager()

    with pytest.raises(ConfigurationError):
        manager._convert_datacenter(123)


def test_get_env_config_converts_types(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = ConfigManager()
    monkeypatch.setenv("ZOHO_CREATOR_TIMEOUT", "120")
    monkeypatch.setenv("ZOHO_CREATOR_RETRY_DELAY", "0.75")
    monkeypatch.setenv("ZOHO_CREATOR_MAX_RETRIES", "5")

    env_config = manager._get_env_config("api")

    assert env_config["timeout"] == 120
    assert env_config["retry_delay"] == pytest.approx(0.75)
    assert env_config["max_retries"] == 5


def test_get_env_config_boolean_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = ConfigManager()
    monkeypatch.setenv("ZOHO_CREATOR_TIMEOUT", "1.0")
    monkeypatch.setenv("ZOHO_CREATOR_MAX_RETRIES", "0")
    monkeypatch.setenv("ZOHO_CREATOR_RETRY_DELAY", "OFF")

    env = manager._get_env_config("api")

    assert env["timeout"] is True
    assert env["max_retries"] is False
    assert env["retry_delay"] is False


def test_is_float_helper() -> None:
    manager = ConfigManager()

    assert manager._is_float("1.23") is True
    assert manager._is_float("not-a-float") is False


def test_config_manager_without_file_uses_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Ensure no default config file is detected
    monkeypatch.chdir(tmp_path)
    manager = ConfigManager()

    assert manager.config_file_path is None
    assert manager.config_data == {}

    logging_config = manager.get_logging_config()
    assert logging_config.level == "INFO"


def test_invalid_config_raises_error(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path, {"api": {"max_records_per_request": 100}})
    manager = ConfigManager(config_file_path=config_path)

    with pytest.raises(ConfigurationError):
        manager.get_api_config()


def test_get_auth_config_cached(tmp_path: Path) -> None:
    config_path = _make_config(
        tmp_path,
        {
            "auth": {
                "client_id": "id",
                "client_secret": "secret",
                "redirect_uri": "uri",
                "refresh_token": "token",
            }
        },
    )
    manager = ConfigManager(config_file_path=config_path)

    first = manager.get_auth_config()
    second = manager.get_auth_config()

    assert first is second


def test_logging_setup_invokes_basic_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_basic_config(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", _fake_basic_config)

    config = LoggingConfig(level="debug", format="fmt", file_path=None)
    setup_logging(config)

    assert captured["level"] == "DEBUG"
    assert captured["format"] == "fmt"
    assert captured["filemode"] == "w"
