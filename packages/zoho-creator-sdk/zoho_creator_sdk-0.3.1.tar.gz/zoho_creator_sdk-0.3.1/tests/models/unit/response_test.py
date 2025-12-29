"""Unit tests for response models."""

from __future__ import annotations

from zoho_creator_sdk.models.response import (
    BulkResponse,
    BulkResult,
    ErrorInfo,
    ErrorResponse,
    ListInfo,
    ListResponse,
    StatusResponse,
    SuccessResponse,
    TaskInfo,
    TokenResponse,
)


def test_success_response_with_task() -> None:
    task = TaskInfo(type="redirect", url="https://example.com")
    response = SuccessResponse(
        code=200, message="ok", data={"id": 1}, tasks={"redirect": task}
    )

    assert response.tasks["redirect"].url == "https://example.com"


def test_list_response_info_alias() -> None:
    info = ListInfo(moreRecords=True, next_page_token="token")
    resp = ListResponse(code=200, data=[], info=info)

    assert resp.info.more_records is True


def test_bulk_response_result() -> None:
    result = BulkResult(code=200, message="ok")
    resp = BulkResponse(code=200, message=None, result=[result])

    assert resp.result[0].message == "ok"


def test_error_response_accepts_error_info_list() -> None:
    err = ErrorInfo(code="E1", message="oops")
    resp = ErrorResponse(code=400, message="error", error=[err])

    assert resp.error[0].code == "E1"


def test_token_and_status_response() -> None:
    token = TokenResponse(
        access_token="token",
        expires_in=3600,
        api_domain="https://api",
        token_type="Bearer",
    )
    status = StatusResponse(status="success")

    assert token.token_type == "Bearer"
    assert status.status == "success"
