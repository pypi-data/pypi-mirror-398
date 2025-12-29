"""
Bulk operations related models for the Zoho Creator SDK.
"""

from datetime import datetime
from typing import Optional, Union

from pydantic import Field, model_validator

from .base import CreatorBaseModel
from .enums import BulkOperationStatus, BulkOperationType
from .import_export import ExportResult, ImportResult


class BulkOperation(CreatorBaseModel):
    """Model for tracking bulk operations (import/export/delete)."""

    operation_id: str = Field(description="Unique identifier for the bulk operation.")
    operation_type: BulkOperationType = Field(description="Type of bulk operation.")
    status: BulkOperationStatus = Field(description="Current status of the operation.")
    application_id: str = Field(
        description="ID of the application where the operation is performed."
    )
    form_id: str = Field(description="ID of the form where the operation is performed.")
    initiated_by: str = Field(
        description="User ID or system identifier that initiated the operation."
    )
    initiated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when the operation was initiated.",
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Time when the operation started processing."
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Time when the operation completed."
    )
    duration_seconds: Optional[float] = Field(
        default=None, ge=0, description="Total duration of the operation in seconds."
    )
    total_records: int = Field(
        ge=0, description="Total number of records to be processed."
    )
    processed_records: int = Field(
        ge=0, description="Number of records that have been processed so far."
    )
    successful_records: int = Field(
        ge=0, description="Number of records processed successfully."
    )
    failed_records: int = Field(
        ge=0, description="Number of records that failed to process."
    )
    progress_percentage: float = Field(
        ge=0, le=100, description="Percentage of completion for the operation."
    )
    result_details: Optional[Union[ImportResult, ExportResult]] = Field(
        default=None,
        description="Detailed results of the operation (ImportResult or ExportResult).",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if the operation failed."
    )
    priority: int = Field(
        default=5, ge=1, le=10, description="Priority level of the operation (1-10)."
    )
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated time of completion for the operation."
    )

    @model_validator(mode="after")
    def validate_bulk_operation(self) -> "BulkOperation":
        """Validate bulk operation consistency."""
        if self.status == BulkOperationStatus.COMPLETED and not self.completed_at:
            raise ValueError("Completed operations must have a completed_at timestamp")

        if self.status == BulkOperationStatus.IN_PROGRESS and not self.started_at:
            raise ValueError("In-progress operations must have a started_at timestamp")

        if self.processed_records > self.total_records:
            raise ValueError("processed_records cannot exceed total_records")

        if self.successful_records + self.failed_records > self.processed_records:
            raise ValueError(
                "successful_records + failed_records cannot exceed processed_records"
            )

        if self.status == BulkOperationStatus.FAILED and not self.error_message:
            raise ValueError("Failed operations must have an error message")

        # Calculate progress percentage if not provided
        if self.total_records > 0:
            calculated_progress = (self.processed_records / self.total_records) * 100
            if (
                abs(self.progress_percentage - calculated_progress) > 0.1
            ):  # Allow small rounding differences
                self.progress_percentage = calculated_progress
        elif self.total_records == 0:
            self.progress_percentage = (
                100.0 if self.status == BulkOperationStatus.COMPLETED else 0.0
            )

        # Calculate duration if start and completion times are available
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            if self.duration_seconds is None:
                self.duration_seconds = duration
            elif abs(self.duration_seconds - duration) > 1:  # Allow 1 second tolerance
                raise ValueError("duration_seconds doesn't match calculated duration")

        return self

    @property
    def is_complete(self) -> bool:
        """Check if the bulk operation is complete."""
        return self.status in [
            BulkOperationStatus.COMPLETED,
            BulkOperationStatus.FAILED,
            BulkOperationStatus.CANCELLED,
        ]

    @property
    def failure_rate(self) -> float:
        """Calculate the failure rate as a percentage."""
        if self.processed_records == 0:
            return 0.0
        return (self.failed_records / self.processed_records) * 100.0

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.processed_records == 0:
            return 10.0
        return (self.successful_records / self.processed_records) * 100.0
