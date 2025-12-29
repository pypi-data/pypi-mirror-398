"""Unit tests for :class:`zoho_creator_sdk.client.ZohoCreatorClient`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from zoho_creator_sdk.client import ZohoCreatorClient
from zoho_creator_sdk.exceptions import APIError


@pytest.fixture
def initialized_client(monkeypatch: pytest.MonkeyPatch):
    config_manager = Mock()
    config_manager.get_auth_config.return_value = Mock()
    config_manager.get_api_config.return_value = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.ConfigManager", Mock(return_value=config_manager)
    )

    auth_handler = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.get_auth_handler", Mock(return_value=auth_handler)
    )

    http_client = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.HTTPClient", Mock(return_value=http_client)
    )

    client = ZohoCreatorClient()
    client.http_client = http_client
    client.api_config = Mock(base_url="https://api")
    return client


def test_initialization_sets_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    config_manager = Mock()
    config_manager.get_auth_config.return_value = Mock()
    config_manager.get_api_config.return_value = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.ConfigManager", Mock(return_value=config_manager)
    )

    auth_handler = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.get_auth_handler", Mock(return_value=auth_handler)
    )

    http_client = Mock()
    monkeypatch.setattr(
        "zoho_creator_sdk.client.HTTPClient", Mock(return_value=http_client)
    )

    client = ZohoCreatorClient()

    assert client.auth_handler is auth_handler
    assert client.http_client is http_client


def test_context_builders(initialized_client: ZohoCreatorClient) -> None:
    workflow = initialized_client.workflow("app", "owner", "wf")
    permission = initialized_client.permission("app", "owner", "p")
    connection = initialized_client.connection("app", "owner", "c")
    custom_action = initialized_client.custom_action("app", "owner", "action")
    form = initialized_client.form("app", "owner", "form")
    report = initialized_client.report("app", "owner", "report")
    page = initialized_client.page("app", "owner", "page")
    section = initialized_client.section("app", "owner", "section")
    app_context = initialized_client.application("app", "owner")

    assert workflow.workflow_link_name == "wf"
    assert permission.permission_id == "p"
    assert connection.connection_id == "c"
    assert custom_action.custom_action_link_name == "action"
    assert form.form_link_name == "form"
    assert report.report_link_name == "report"
    assert page.page_link_name == "page"
    assert section.section_link_name == "section"
    assert app_context.app_link_name == "app"


def test_get_applications(
    monkeypatch: pytest.MonkeyPatch, initialized_client: ZohoCreatorClient
) -> None:
    initialized_client.http_client.get.return_value = {"applications": [{"id": 1}]}
    fake_app = Mock(side_effect=lambda **_: "app")
    monkeypatch.setattr("zoho_creator_sdk.client.Application", fake_app)

    apps = initialized_client.get_applications("owner")

    assert apps == ["app"]


def test_get_permissions(
    monkeypatch: pytest.MonkeyPatch, initialized_client: ZohoCreatorClient
) -> None:
    initialized_client.http_client.get.return_value = {"permissions": [{"id": 1}]}
    fake_perm = Mock(side_effect=lambda **_: "perm")
    monkeypatch.setattr("zoho_creator_sdk.client.Permission", fake_perm)

    perms = initialized_client.get_permissions("owner", "app")

    assert perms == ["perm"]


def test_get_applications_invalid_data(initialized_client: ZohoCreatorClient) -> None:
    initialized_client.http_client.get.return_value = {"applications": [{}]}

    with pytest.raises(APIError):
        initialized_client.get_applications("owner")


def test_get_permissions_invalid_data(initialized_client: ZohoCreatorClient) -> None:
    initialized_client.http_client.get.return_value = {"permissions": [{}]}

    with pytest.raises(APIError):
        initialized_client.get_permissions("owner", "app")


def test_update_and_delete_record(initialized_client: ZohoCreatorClient) -> None:
    initialized_client.http_client.patch.return_value = {"updated": True}
    initialized_client.http_client.delete.return_value = {"deleted": True}

    result = initialized_client.update_record(
        "owner", "app", "report", "1", data={"x": 1}
    )
    delete = initialized_client.delete_record("owner", "app", "report", "1")

    assert result["updated"] is True
    assert delete["deleted"] is True
