"""Unit tests for additional client contexts."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from zoho_creator_sdk.client import (
    AppContext,
    ConnectionContext,
    CustomActionContext,
    PageContext,
    PermissionContext,
    SectionContext,
    WorkflowContext,
)
from zoho_creator_sdk.exceptions import APIError


@pytest.fixture
def http_client(api_config):  # type: ignore[override]
    client = Mock()
    client.config = api_config
    return client


def test_app_context_custom_action_requires_identifier(
    http_client,  # type: ignore[override]
) -> None:
    context = AppContext(http_client, "app", "owner")

    with pytest.raises(ValueError):
        context.custom_action("")

    custom_action = context.custom_action("action")
    assert isinstance(custom_action, CustomActionContext)


def test_workflow_context_get_and_execute(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"workflow": {"id": "wf"}}
    sentinel = object()
    fake_model = Mock(return_value=sentinel)
    monkeypatch.setattr("zoho_creator_sdk.client.Workflow", fake_model)

    context = WorkflowContext(http_client, "app", "wf", "owner")
    result = context.get_workflow()

    assert result is sentinel
    http_client.post.return_value = {"status": "ok"}
    payload = context.execute_workflow("rec", trigger=True)
    http_client.post.assert_called_once()
    assert payload["status"] == "ok"


def test_workflow_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"workflow": {}}
    context = WorkflowContext(http_client, "app", "wf", "owner")

    with pytest.raises(APIError):
        context.get_workflow()


def test_permission_context_operations(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"permission": {"id": "perm"}}
    fake_permission = Mock(return_value="perm-obj")
    monkeypatch.setattr("zoho_creator_sdk.client.Permission", fake_permission)

    context = PermissionContext(http_client, "app", "perm", "owner")

    assert context.get_permission() == "perm-obj"
    http_client.patch.return_value = {"status": "ok"}
    context.update_permission({"allow": True})
    http_client.patch.assert_called_once()


def test_permission_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"permission": {}}
    context = PermissionContext(http_client, "app", "perm", "owner")

    with pytest.raises(APIError):
        context.get_permission()


def test_connection_context_methods(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.side_effect = [
        {"connection": {"id": "conn"}},
        {"status": "up"},
    ]
    fake_connection = Mock(return_value="conn-obj")
    monkeypatch.setattr("zoho_creator_sdk.client.Connection", fake_connection)

    context = ConnectionContext(http_client, "app", "conn", "owner")

    assert context.get_connection() == "conn-obj"
    assert context.test_connection()["status"] == "up"


def test_connection_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"connection": {}}
    context = ConnectionContext(http_client, "app", "conn", "owner")

    with pytest.raises(APIError):
        context.get_connection()


def test_custom_action_context(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"customaction": {"id": "action"}}
    fake_action = Mock(return_value="action-obj")
    monkeypatch.setattr("zoho_creator_sdk.client.CustomAction", fake_action)

    context = CustomActionContext(http_client, "app", "action", "owner")

    assert context.get_custom_action() == "action-obj"
    http_client.post.return_value = {"success": True}
    result = context.execute_custom_action("rec", data="x")
    assert result == {"success": True}


def test_custom_action_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"customaction": {}}
    context = CustomActionContext(http_client, "app", "action", "owner")

    with pytest.raises(APIError):
        context.get_custom_action()


def test_page_context(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"page": {"id": "p"}}
    fake_page = Mock(return_value="page-obj")
    monkeypatch.setattr("zoho_creator_sdk.client.Page", fake_page)

    context = PageContext(http_client, "app", "page", "owner")
    assert context.get_page() == "page-obj"


def test_page_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"page": {"invalid": "data"}}
    context = PageContext(http_client, "app", "page", "owner")

    with pytest.raises(APIError):
        context.get_page()


def test_section_context(
    monkeypatch: pytest.MonkeyPatch,
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"section": {"id": "sec"}}
    fake_section = Mock(return_value="section-obj")
    monkeypatch.setattr("zoho_creator_sdk.client.Section", fake_section)

    context = SectionContext(http_client, "app", "section", "owner")
    assert context.get_section() == "section-obj"


def test_section_context_invalid_data_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"section": {}}
    context = SectionContext(http_client, "app", "section", "owner")

    with pytest.raises(APIError):
        context.get_section()
