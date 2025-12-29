"""Unit tests for enumerations."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.models import enums


@pytest.mark.parametrize(
    "enum_cls",
    [
        enums.ImportFormat,
        enums.ImportMode,
        enums.ExportFormat,
        enums.BulkOperationStatus,
        enums.BulkOperationType,
        enums.ResponseStatus,
        enums.ReportType,
        enums.WorkflowType,
        enums.WorkflowStatus,
        enums.TriggerType,
        enums.FieldType,
        enums.PermissionType,
        enums.EntityType,
        enums.ActionType,
    ],
)
def test_enum_contains_values(enum_cls) -> None:  # type: ignore[no-untyped-def]
    members = {member.value for member in enum_cls}

    assert len(members) == len(list(enum_cls))
    for value in members:
        assert enum_cls(value) in enum_cls
