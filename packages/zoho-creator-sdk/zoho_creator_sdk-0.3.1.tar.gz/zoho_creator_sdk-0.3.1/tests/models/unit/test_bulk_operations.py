"""Unit tests for bulk operations models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.models import BulkOperation
from zoho_creator_sdk.models.enums import BulkOperationStatus, BulkOperationType


class TestBulkOperation:
    """Test cases for BulkOperation."""

    def test_bulk_operation_minimal_creation(self) -> None:
        """BulkOperation can be created with minimal required fields."""
        operation = BulkOperation(
            operation_id="op123",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.PENDING,
            application_id="app456",
            form_id="form789",
            initiated_by="user123",
            total_records=100,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percentage=0.0,
        )

        assert operation.operation_id == "op123"
        assert operation.operation_type == BulkOperationType.IMPORT
        assert operation.status == BulkOperationStatus.PENDING
        assert operation.application_id == "app456"
        assert operation.form_id == "form789"
        assert operation.initiated_by == "user123"
        assert operation.total_records == 100
        assert operation.processed_records == 0

    def test_bulk_operation_complete_creation(self) -> None:
        """BulkOperation can be created with all fields."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(minutes=5)
        completion_time = now

        operation = BulkOperation(
            operation_id="op456",
            operation_type=BulkOperationType.EXPORT,
            status=BulkOperationStatus.COMPLETED,
            application_id="app789",
            form_id="form123",
            initiated_by="user456",
            initiated_at=start_time,
            started_at=start_time,
            completed_at=completion_time,
            duration_seconds=300.0,
            total_records=1000,
            processed_records=1000,
            successful_records=980,
            failed_records=20,
            progress_percentage=100.0,
            priority=1,
            estimated_completion=completion_time,
        )

        assert operation.operation_id == "op456"
        assert operation.operation_type == BulkOperationType.EXPORT
        assert operation.status == BulkOperationStatus.COMPLETED
        assert operation.duration_seconds == 300.0
        assert operation.successful_records == 980
        assert operation.failed_records == 20
        assert operation.priority == 1

    def test_bulk_operation_with_import_result(self) -> None:
        """BulkOperation can include ImportResult."""
        from zoho_creator_sdk.models.import_export import (
            ImportFormat,
            ImportMode,
            ImportResult,
        )

        import_result = ImportResult(
            operation_id="import_op_123",
            total_records=500,
            successful_records=450,
            failed_records=50,
            duration_seconds=120.5,
            import_format=ImportFormat.CSV,
            import_mode=ImportMode.CREATE,
            application_id="app_123",
            form_id="form_456",
            created_records=400,
            updated_records=50,
            deleted_records=0,
            skipped_records=50,
        )

        from datetime import datetime

        now = datetime.utcnow()
        operation = BulkOperation(
            operation_id="import_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.COMPLETED,
            application_id="app123",
            form_id="form456",
            initiated_by="admin",
            completed_at=now,  # Required for completed operations
            total_records=500,
            processed_records=500,
            successful_records=450,
            failed_records=50,
            progress_percentage=100.0,
            result_details=import_result,
        )

        assert operation.result_details is not None
        assert isinstance(operation.result_details, ImportResult)
        assert operation.result_details.total_records == 500
        assert operation.result_details.successful_records == 450

    def test_bulk_operation_with_export_result(self) -> None:
        """BulkOperation can include ExportResult."""
        from datetime import datetime

        from zoho_creator_sdk.models.import_export import ExportFormat, ExportResult

        now = datetime.utcnow()
        export_result = ExportResult(
            operation_id="export_op_123",
            total_records=200,
            file_path="/tmp/data.csv",
            file_size_bytes=1024000,
            export_format=ExportFormat.CSV,
            duration_seconds=45.2,
            application_id="app_123",
            form_id="form_456",
        )

        operation = BulkOperation(
            operation_id="export_op",
            operation_type=BulkOperationType.EXPORT,
            status=BulkOperationStatus.COMPLETED,
            application_id="app789",
            form_id="form123",
            initiated_by="user789",
            completed_at=now,  # Required for completed operations
            total_records=200,
            processed_records=200,
            successful_records=200,
            failed_records=0,
            progress_percentage=100.0,
            result_details=export_result,
        )

        assert operation.result_details is not None
        assert isinstance(operation.result_details, ExportResult)
        assert operation.result_details.file_path == "/tmp/data.csv"
        assert operation.result_details.export_format == ExportFormat.CSV

    def test_bulk_operation_delete_type(self) -> None:
        """BulkOperation supports DELETE operation type."""
        from datetime import datetime

        operation = BulkOperation(
            operation_id="delete_op",
            operation_type=BulkOperationType.DELETE,
            status=BulkOperationStatus.IN_PROGRESS,
            application_id="app123",
            form_id="form456",
            initiated_by="admin",
            total_records=50,
            processed_records=25,
            successful_records=24,
            failed_records=1,
            progress_percentage=50.0,
            started_at=datetime.utcnow(),
        )

        assert operation.operation_type == BulkOperationType.DELETE
        assert operation.status == BulkOperationStatus.IN_PROGRESS
        assert operation.progress_percentage == 50.0

    def test_bulk_operation_progress_calculation(self) -> None:
        """BulkOperation automatically calculates progress percentage."""
        from datetime import datetime

        operation = BulkOperation(
            operation_id="progress_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.IN_PROGRESS,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=1000,
            processed_records=350,
            successful_records=300,
            failed_records=50,
            progress_percentage=10.0,  # Should be overridden
            started_at=datetime.utcnow(),
        )

        # Progress should be recalculated
        expected_progress = (350 / 1000) * 100
        assert operation.progress_percentage == expected_progress

    def test_bulk_operation_zero_total_records(self) -> None:
        """BulkOperation handles zero total records correctly."""
        from datetime import datetime

        operation = BulkOperation(
            operation_id="zero_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.COMPLETED,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=0,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percentage=100.0,  # Should be 100 for completed with 0 records
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        assert operation.progress_percentage == 100.0

    def test_bulk_operation_priority_levels(self) -> None:
        """BulkOperation supports different priority levels."""
        high_priority = BulkOperation(
            operation_id="high_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.PENDING,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=100,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percentage=0.0,
            priority=1,
        )

        low_priority = BulkOperation(
            operation_id="low_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.PENDING,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=100,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percentage=0.0,
            priority=10,
        )

        assert high_priority.priority == 1
        assert low_priority.priority == 10

    def test_bulk_operation_duration_calculation(self) -> None:
        """BulkOperation duration is properly set."""
        start_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        end_time = datetime.now(timezone.utc)

        operation = BulkOperation(
            operation_id="duration_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.COMPLETED,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            started_at=start_time,
            completed_at=end_time,
            total_records=100,
            processed_records=100,
            successful_records=100,
            failed_records=0,
            progress_percentage=100.0,
            duration_seconds=300.0,
        )

        assert operation.duration_seconds == 300.0

    def test_bulk_operation_error_handling(self) -> None:
        """BulkOperation stores error information for failed operations."""
        operation = BulkOperation(
            operation_id="failed_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.FAILED,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=100,
            processed_records=50,
            successful_records=25,
            failed_records=25,
            progress_percentage=50.0,
            error_message="Validation failed for 25 records",
        )

        assert operation.status == BulkOperationStatus.FAILED
        assert operation.error_message == "Validation failed for 25 records"

    def test_bulk_operation_validation_completed_missing_timestamp(self) -> None:
        """BulkOperation raises validation error for completed operation
        without timestamp."""
        with pytest.raises(ValueError) as exc_info:
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.COMPLETED,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=100,
                successful_records=100,
                failed_records=0,
                progress_percentage=100.0,
                # Missing completed_at
            )

        assert "Completed operations must have a completed_at timestamp" in str(
            exc_info.value
        )

    def test_bulk_operation_validation_in_progress_missing_timestamp(self) -> None:
        """BulkOperation raises validation error for in-progress operation
        without timestamp."""
        with pytest.raises(ValueError) as exc_info:
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.IN_PROGRESS,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=50,
                successful_records=40,
                failed_records=10,
                progress_percentage=50.0,
                # Missing started_at
            )

        assert "In-progress operations must have a started_at timestamp" in str(
            exc_info.value
        )

    def test_bulk_operation_validation_processed_exceeds_total(self) -> None:
        """BulkOperation raises validation error when processed exceeds total."""
        with pytest.raises(ValueError) as exc_info:
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.IN_PROGRESS,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=150,  # Exceeds total
                successful_records=140,
                failed_records=10,
                progress_percentage=150.0,
            )

        assert "Input should be less than or equal to 100" in str(exc_info.value)

    def test_bulk_operation_validation_success_plus_failed_exceeds_processed(
        self,
    ) -> None:
        """BulkOperation raises validation error when success+failed
        exceeds processed."""
        from datetime import datetime

        with pytest.raises(ValueError) as exc_info:
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.IN_PROGRESS,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=50,
                successful_records=30,
                failed_records=30,  # Success + fail > processed
                progress_percentage=50.0,
                started_at=datetime.utcnow(),
            )

        assert (
            "successful_records + failed_records cannot exceed "
            "processed_records" in str(exc_info.value)
        )

    def test_bulk_operation_validation_failed_missing_error_message(self) -> None:
        """BulkOperation raises validation error for failed operation
        without error message."""
        with pytest.raises(ValueError) as exc_info:
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.FAILED,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=50,
                successful_records=0,
                failed_records=50,
                progress_percentage=50.0,
                # Missing error_message
            )

        assert "Failed operations must have an error message" in str(exc_info.value)

    def test_bulk_operation_validation_invalid_priority(self) -> None:
        """BulkOperation raises validation error for invalid priority."""
        with pytest.raises(PydanticValidationError):
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.PENDING,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=100,
                processed_records=0,
                successful_records=0,
                failed_records=0,
                progress_percentage=0.0,
                priority=11,  # Invalid priority (must be 1-10)
            )

    def test_bulk_operation_validation_negative_values(self) -> None:
        """BulkOperation raises validation error for negative numeric values."""
        with pytest.raises(PydanticValidationError):
            BulkOperation(
                operation_id="invalid_op",
                operation_type=BulkOperationType.IMPORT,
                status=BulkOperationStatus.PENDING,
                application_id="app123",
                form_id="form456",
                initiated_by="user123",
                total_records=-10,  # Invalid negative value
                processed_records=0,
                successful_records=0,
                failed_records=0,
                progress_percentage=0.0,
            )

    def test_bulk_operation_string_representation(self) -> None:
        """BulkOperation string representation includes operation ID."""
        from datetime import datetime

        operation = BulkOperation(
            operation_id="test_op_123",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.IN_PROGRESS,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=100,
            processed_records=50,
            successful_records=40,
            failed_records=10,
            progress_percentage=50.0,
            started_at=datetime.utcnow(),
        )

        operation_str = str(operation)
        assert "test_op_123" in operation_str

    def test_bulk_operation_timezones(self) -> None:
        """BulkOperation handles different timezones correctly."""
        utc_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        operation = BulkOperation(
            operation_id="timezone_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.PENDING,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=100,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percentage=0.0,
            estimated_completion=utc_time,
        )

        assert operation.estimated_completion == utc_time

    def test_bulk_operation_progress_rounding(self) -> None:
        """BulkOperation handles progress calculation rounding correctly."""
        from datetime import datetime

        operation = BulkOperation(
            operation_id="rounding_op",
            operation_type=BulkOperationType.IMPORT,
            status=BulkOperationStatus.IN_PROGRESS,
            application_id="app123",
            form_id="form456",
            initiated_by="user123",
            total_records=3,
            processed_records=1,
            successful_records=1,
            failed_records=0,
            progress_percentage=50.0,  # 1/3 * 100 = 33.33, should be updated
            started_at=datetime.utcnow(),
        )

        # Progress should be recalculated and rounded properly
        expected_progress = (1 / 3) * 100
        assert abs(operation.progress_percentage - expected_progress) < 0.01

    def test_bulk_operation_all_statuses(self) -> None:
        """BulkOperation can be created with all possible statuses."""
        statuses = [
            BulkOperationStatus.PENDING,
            BulkOperationStatus.IN_PROGRESS,
            BulkOperationStatus.PAUSED,
            BulkOperationStatus.COMPLETED,
            BulkOperationStatus.FAILED,
            BulkOperationStatus.CANCELLED,
        ]

        from datetime import datetime

        for status in statuses:
            # Base operation data
            operation_data = {
                "operation_id": f"test_{status.value}",
                "operation_type": BulkOperationType.IMPORT,
                "status": status,
                "application_id": "app123",
                "form_id": "form456",
                "initiated_by": "user123",
                "total_records": 0,
                "processed_records": 0,
                "successful_records": 0,
                "failed_records": 0,
                "progress_percentage": 0.0,
            }

            # Add required timestamps based on status
            if status == BulkOperationStatus.IN_PROGRESS:
                operation_data["started_at"] = datetime.utcnow()
            elif status == BulkOperationStatus.COMPLETED:
                operation_data["started_at"] = datetime.utcnow()
                operation_data["completed_at"] = datetime.utcnow()
            elif status == BulkOperationStatus.FAILED:
                operation_data["started_at"] = datetime.utcnow()
                operation_data["error_message"] = "Test error message"

            operation = BulkOperation(**operation_data)

            assert operation.status == status
            assert f"test_{status.value}" in operation.operation_id
