"""Unit tests for import/export models."""

from __future__ import annotations

from typing import Dict

import pytest

from zoho_creator_sdk.models.import_export import (
    ExportFormat,
    ExportOptions,
    ExportResult,
    ImportErrorDetail,
    ImportFormat,
    ImportMapping,
    ImportMode,
    ImportResult,
)


def test_import_mapping_validates_fields() -> None:
    with pytest.raises(ValueError):
        ImportMapping(source_field="", target_field="target")

    with pytest.raises(ValueError):
        ImportMapping(source_field="source", target_field=" ")

    mapping = ImportMapping(source_field="source", target_field="target")
    assert mapping.source_field == "source"


def test_import_error_detail_severity_normalization() -> None:
    detail = ImportErrorDetail(error_code="E1", message="msg", severity="WARNING")
    assert detail.severity == "warning"

    with pytest.raises(ValueError):
        ImportErrorDetail(error_code="E2", message="msg", severity="invalid")


def _import_result_payload() -> Dict[str, object]:
    return {
        "operation_id": "op",
        "total_records": 4,
        "successful_records": 3,
        "failed_records": 1,
        "duration_seconds": 1.0,
        "import_format": ImportFormat.CSV,
        "import_mode": ImportMode.CREATE,
        "application_id": "app",
        "form_id": "form",
        "created_records": 2,
        "updated_records": 1,
        "deleted_records": 1,
        "skipped_records": 0,
    }


def test_import_result_counts_must_balance() -> None:
    payload = _import_result_payload()
    result = ImportResult(**payload)

    assert pytest.approx(result.success_rate) == 75.0
    assert pytest.approx(result.failure_rate) == 25.0

    payload_wrong = _import_result_payload()
    payload_wrong["failed_records"] = 0
    with pytest.raises(ValueError):
        ImportResult(**payload_wrong)

    payload_components = _import_result_payload()
    payload_components["skipped_records"] = 2
    with pytest.raises(ValueError):
        ImportResult(**payload_components)


def test_import_result_zero_total_records() -> None:
    payload = _import_result_payload()
    payload.update(
        {
            "total_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "created_records": 0,
            "updated_records": 0,
            "deleted_records": 0,
            "skipped_records": 0,
        }
    )

    result = ImportResult(**payload)
    assert result.success_rate == 10.0
    assert result.failure_rate == 0.0


def test_export_options_validation() -> None:
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises(ValueError, match="sort_order must be either 'asc' or 'desc'"):
        ExportOptions(sort_order="invalid", export_format=ExportFormat.CSV)

    with pytest.raises(ValueError, match="columns list cannot be empty if provided"):
        ExportOptions(export_format=ExportFormat.CSV, columns=[])

    # Pydantic's built-in validation catches max_records=0 before our custom
    # validator. We can test the custom validator by creating a valid object
    # and then setting an invalid value
    options = ExportOptions(export_format=ExportFormat.CSV, max_records=10)
    options.max_records = 0  # Manually set to invalid value

    # Now test the validator directly
    with pytest.raises(ValueError, match="max_records must be greater than 0 or None"):
        options.validate_options()

    # Test negative values - Pydantic's ge constraint catches this
    with pytest.raises(PydanticValidationError):
        ExportOptions(export_format=ExportFormat.CSV, max_records=-1)

    options = ExportOptions(export_format=ExportFormat.CSV, sort_order="DESC")
    assert options.sort_order == "desc"


def test_export_result_validation() -> None:
    result = ExportResult(
        operation_id="op",
        total_records=10,
        file_path="/tmp/report.csv",
        file_size_bytes=100,
        export_format=ExportFormat.CSV,
        duration_seconds=1.0,
        application_id="app",
        form_id="form",
    )

    assert result.is_successful is True

    with pytest.raises(ValueError):
        ExportResult(
            operation_id="op",
            total_records=0,
            file_path="/tmp",
            file_size_bytes=0,
            export_format=ExportFormat.CSV,
            duration_seconds=0.0,
            application_id="app",
            form_id="form",
            is_successful=False,
        )

    with pytest.raises(ValueError):
        ExportResult(
            operation_id="op",
            total_records=0,
            file_path="/tmp",
            file_size_bytes=0,
            export_format=ExportFormat.CSV,
            duration_seconds=0.0,
            application_id="app",
            form_id="form",
            is_successful=True,
            error_message="should not",
        )
