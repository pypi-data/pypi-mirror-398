"""Unit tests for application-related contexts."""

from __future__ import annotations

from datetime import datetime
from typing import Dict
from unittest.mock import Mock

import pytest

from zoho_creator_sdk.client import AppContext, FormContext, ReportContext
from zoho_creator_sdk.exceptions import APIError


@pytest.fixture
def http_client(api_config):  # type: ignore[override]
    client = Mock()
    client.config = api_config
    return client


def _record_payload(idx: int) -> Dict[str, object]:
    timestamp = datetime(2024, 1, 1, 12, 0, idx).isoformat()
    return {
        "ID": f"rec-{idx}",
        "Name": f"User {idx}",
        "created_time": timestamp,
        "modified_time": timestamp,
    }


def test_app_context_requires_form_name(http_client) -> None:  # type: ignore[override]
    context = AppContext(http_client, "app", "owner")

    with pytest.raises(ValueError):
        context.form("")

    form_ctx = context.form("leads")
    assert isinstance(form_ctx, FormContext)


def test_app_context_report_and_workflow_require_names(
    http_client,  # type: ignore[override]
) -> None:
    context = AppContext(http_client, "app", "owner")

    with pytest.raises(ValueError):
        context.report("")

    with pytest.raises(ValueError):
        context.workflow("")

    assert isinstance(context.report("pipeline"), ReportContext)


def test_app_context_creates_other_contexts(
    http_client,  # type: ignore[override]
) -> None:
    context = AppContext(http_client, "app", "owner")

    assert context.permission("perm").permission_id == "perm"
    assert context.connection("conn").connection_id == "conn"
    custom_action = context.custom_action("action")
    assert custom_action.custom_action_link_name == "action"


def test_form_context_add_record(http_client) -> None:  # type: ignore[override]
    http_client.post.return_value = {"data": {"id": "rec"}}
    context = FormContext(http_client, "app", "leads", "owner")

    payload = {"Name": "Ada"}
    data = context.add_record(payload)

    http_client.post.assert_called_once()
    assert data["data"]["id"] == "rec"


def test_form_context_get_records_paginates(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.side_effect = [
        {
            "data": [_record_payload(1)],
            "meta": {"more_records": True, "next_page_token": "abc"},
        },
        {"data": [_record_payload(2)], "meta": {"more_records": False}},
    ]
    context = FormContext(http_client, "app", "leads", "owner")

    records = list(context.get_records(limit=1))

    assert len(records) == 2
    http_client.get.assert_called_with(
        "https://www.zohoapis.com/creator/v2.1/data/owner/app/form/leads",
        params={"limit": 1, "next_page_token": "abc"},
    )


def test_form_context_invalid_record_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"data": [{"Name": "Missing"}], "meta": {}}
    context = FormContext(http_client, "app", "leads", "owner")

    with pytest.raises(APIError):
        list(context.get_records())


def test_form_context_missing_next_page_token_logs_warning(
    http_client,  # type: ignore[override]
    caplog,
) -> None:
    http_client.get.return_value = {
        "data": [_record_payload(1)],
        "meta": {"more_records": True, "next_page_token": None},
    }
    context = FormContext(http_client, "app", "leads", "owner")

    with caplog.at_level("WARNING", logger="zoho_creator_sdk.client"):
        list(context.get_records(limit=1))

    assert any("more_records is True" in message for message in caplog.messages)


def test_report_context_get_records(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {
        "data": [_record_payload(1)],
        "meta": {"more_records": False},
    }
    context = ReportContext(http_client, "app", "pipeline", "owner")

    records = list(context.get_records())

    assert records[0].ID == "rec-1"


def test_report_context_invalid_record_raises(
    http_client,  # type: ignore[override]
) -> None:
    http_client.get.return_value = {"data": [{"id": "missing"}], "meta": {}}
    context = ReportContext(http_client, "app", "pipeline", "owner")

    with pytest.raises(APIError):
        list(context.get_records())


def test_report_context_missing_token_logs_warning(
    http_client,  # type: ignore[override]
    caplog,
) -> None:
    http_client.get.return_value = {
        "data": [_record_payload(1)],
        "meta": {"more_records": True},
    }
    context = ReportContext(http_client, "app", "pipeline", "owner")

    with caplog.at_level("WARNING", logger="zoho_creator_sdk.client"):
        list(context.get_records())

    assert any("more_records is True" in message for message in caplog.messages)
