"""Unit tests for :mod:`zoho_creator_sdk.models.bulk_operations`."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from zoho_creator_sdk.models.bulk_operations import BulkOperation
from zoho_creator_sdk.models.enums import BulkOperationStatus, BulkOperationType


def _base_payload() -> dict[str, object]:
    now = datetime.utcnow()
    return {
        "operation_id": "op",
        "operation_type": BulkOperationType.IMPORT,
        "status": BulkOperationStatus.IN_PROGRESS,
        "application_id": "app",
        "form_id": "form",
        "initiated_by": "user",
        "initiated_at": now,
        "started_at": now,
        "completed_at": now + timedelta(seconds=10),
        "total_records": 10,
        "processed_records": 8,
        "successful_records": 6,
        "failed_records": 2,
        "progress_percentage": 0,
        "duration_seconds": None,
    }


def test_bulk_operation_progress_and_duration() -> None:
    payload = _base_payload()
    bulk = BulkOperation(**payload)

    assert pytest.approx(bulk.progress_percentage, rel=1e-3) == 80.0
    assert bulk.duration_seconds == 10
    assert bulk.is_complete is False
    assert pytest.approx(bulk.success_rate) == 75.0
    assert pytest.approx(bulk.failure_rate) == 25.0

    payload_done = _base_payload()
    payload_done.update(
        {
            "status": BulkOperationStatus.CANCELLED,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "total_records": 0,
        }
    )
    assert BulkOperation(**payload_done).is_complete is True


def test_bulk_operation_completed_requires_timestamp() -> None:
    payload = _base_payload()
    payload.update({"status": BulkOperationStatus.COMPLETED, "completed_at": None})

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_bulk_operation_failed_requires_error_message() -> None:
    payload = _base_payload()
    payload.update({"status": BulkOperationStatus.FAILED, "error_message": None})

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_bulk_operation_processed_constraints() -> None:
    payload = _base_payload()
    payload["processed_records"] = 5
    payload["successful_records"] = 5
    payload["failed_records"] = 1

    with pytest.raises(ValueError):
        BulkOperation(**payload)

    payload_over = _base_payload()
    payload_over["processed_records"] = 11

    with pytest.raises(ValueError):
        BulkOperation(**payload_over)


def test_bulk_operation_duration_mismatch() -> None:
    payload = _base_payload()
    payload["duration_seconds"] = 1

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_zero_processed_records_rates() -> None:
    payload = _base_payload()
    payload.update(
        {"processed_records": 0, "successful_records": 0, "failed_records": 0}
    )

    bulk = BulkOperation(**payload)

    assert bulk.failure_rate == 0.0
    assert bulk.success_rate == 10.0


def test_bulk_operation_in_progress_requires_start_time() -> None:
    payload = _base_payload()
    payload["started_at"] = None

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_bulk_operation_zero_total_records_progress_calculation() -> None:
    """Test progress calculation when total_records is 0."""
    payload = _base_payload()
    payload.update(
        {
            "total_records": 0,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "status": BulkOperationStatus.PENDING,
        }
    )

    bulk = BulkOperation(**payload)
    assert bulk.progress_percentage == 0.0

    # When completed with 0 total records, progress should be 100%
    payload["status"] = BulkOperationStatus.COMPLETED
    bulk = BulkOperation(**payload)
    assert bulk.progress_percentage == 100.0


def test_bulk_operation_progress_calculation_tolerance() -> None:
    """Test that progress calculation allows small rounding differences."""
    payload = _base_payload()
    payload.update(
        {
            "total_records": 3,
            "processed_records": 1,
            "successful_records": 1,
            "failed_records": 0,
            "progress_percentage": 33.34,  # Slightly different from calculated 33.33
        }
    )

    bulk = BulkOperation(**payload)
    # Should not change progress due to tolerance
    assert bulk.progress_percentage == 33.34

    # Large difference should trigger recalculation
    payload["progress_percentage"] = 50.0
    bulk = BulkOperation(**payload)
    assert pytest.approx(bulk.progress_percentage, rel=1e-3) == 33.33


def test_bulk_operation_duration_calculation() -> None:
    """Test duration calculation when start and completion times are provided."""
    payload = _base_payload()
    payload.update(
        {
            "started_at": datetime(2024, 1, 1, 12, 0, 0),
            "completed_at": datetime(2024, 1, 1, 12, 0, 10),
            "duration_seconds": None,
        }
    )

    bulk = BulkOperation(**payload)
    assert bulk.duration_seconds == 10.0


def test_bulk_operation_duration_tolerance() -> None:
    """Test that duration calculation allows 1 second tolerance."""
    payload = _base_payload()
    payload.update(
        {
            "started_at": datetime(2024, 1, 1, 12, 0, 0),
            "completed_at": datetime(2024, 1, 1, 12, 0, 10),
            "duration_seconds": 10.5,  # Within 1 second tolerance
        }
    )

    bulk = BulkOperation(**payload)
    assert bulk.duration_seconds == 10.5

    # Outside tolerance should raise error
    payload["duration_seconds"] = 12.0  # More than 1 second difference
    with pytest.raises(
        ValueError, match="duration_seconds doesn't match calculated duration"
    ):
        BulkOperation(**payload)


def test_bulk_operation_is_complete_property() -> None:
    """Test the is_complete property for different statuses."""
    # Completed statuses
    for status in [
        BulkOperationStatus.COMPLETED,
        BulkOperationStatus.CANCELLED,
    ]:
        payload = _base_payload()
        payload["status"] = status
        bulk = BulkOperation(**payload)
        assert bulk.is_complete is True

    # FAILED status requires error message
    payload = _base_payload()
    payload["status"] = BulkOperationStatus.FAILED
    payload["error_message"] = "Operation failed"
    bulk = BulkOperation(**payload)
    assert bulk.is_complete is True

    # Non-completed statuses
    for status in [
        BulkOperationStatus.PENDING,
        BulkOperationStatus.IN_PROGRESS,
        BulkOperationStatus.PAUSED,
    ]:
        payload = _base_payload()
        payload["status"] = status
        bulk = BulkOperation(**payload)
        assert bulk.is_complete is False


def test_bulk_operation_failure_rate_zero_processed() -> None:
    """Test failure_rate property when no records are processed."""
    payload = _base_payload()
    payload.update(
        {"processed_records": 0, "failed_records": 0, "successful_records": 0}
    )

    bulk = BulkOperation(**payload)
    assert bulk.failure_rate == 0.0


def test_bulk_operation_failure_rate_with_processed_records() -> None:
    """Test failure_rate property when records are processed."""
    payload = _base_payload()
    payload.update(
        {"processed_records": 10, "failed_records": 3, "successful_records": 7}
    )

    bulk = BulkOperation(**payload)
    assert bulk.failure_rate == 30.0


def test_bulk_operation_success_rate_zero_processed() -> None:
    """Test success_rate property when no records are processed."""
    payload = _base_payload()
    payload.update(
        {"processed_records": 0, "successful_records": 0, "failed_records": 0}
    )

    bulk = BulkOperation(**payload)
    assert bulk.success_rate == 10.0


def test_bulk_operation_success_rate_with_processed_records() -> None:
    """Test success_rate property when records are processed."""
    payload = _base_payload()
    payload.update(
        {"processed_records": 10, "successful_records": 7, "failed_records": 3}
    )

    bulk = BulkOperation(**payload)
    assert bulk.success_rate == 70.0
