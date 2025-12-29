"""
Import and export related models for the Zoho Creator SDK.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Optional, Sequence

from pydantic import Field, field_validator, model_validator

from .base import CreatorBaseModel
from .enums import ExportFormat, ImportFormat, ImportMode


class ImportMapping(CreatorBaseModel):
    """Model for field mapping during import operations."""

    source_field: str = Field(description="The name of the field in the source data.")
    target_field: str = Field(
        description="The name of the field in the target Zoho Creator form."
    )
    transformation_function: Optional[str] = Field(
        default=None,
        description="Optional transformation function to apply to the field value.",
    )
    required: bool = Field(
        default=False,
        description="Whether this field mapping is required for the import.",
    )
    default_value: Optional[Any] = Field(
        default=None, description="Default value to use if source field is missing."
    )
    data_type: Optional[str] = Field(
        default=None, description="Expected data type for validation purposes."
    )

    @field_validator("source_field")
    @classmethod
    def validate_source_field(cls, v: str) -> str:
        """Validate that source_field is not empty."""
        if not v or not v.strip():
            raise ValueError("source_field cannot be empty")
        return v

    @field_validator("target_field")
    @classmethod
    def validate_target_field(cls, v: str) -> str:
        """Validate that target_field is not empty."""
        if not v or not v.strip():
            raise ValueError("target_field cannot be empty")
        return v


class ImportErrorDetail(CreatorBaseModel):
    """Model for detailed error reporting during import operations."""

    error_code: str = Field(description="Unique error code for the import error.")
    message: str = Field(description="Human-readable error message.")
    field_name: Optional[str] = Field(
        default=None, description="Name of the field where the error occurred."
    )
    row_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="Row number in the source data where the error occurred.",
    )
    source_value: Optional[Any] = Field(
        default=None,
        description="Original value from the source data that caused the error.",
    )
    severity: str = Field(
        default="error",
        description="Severity level of the error (info, warning, error, critical).",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time when the error was detected."
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate that severity is one of the allowed values."""
        allowed_severities = {"info", "warning", "error", "critical"}
        if v.lower() not in allowed_severities:
            raise ValueError(
                f"Severity must be one of: {', '.join(allowed_severities)}"
            )
        return v.lower()


class ImportResult(CreatorBaseModel):
    """Model for tracking import operation results."""

    operation_id: str = Field(description="Unique identifier for the import operation.")
    total_records: int = Field(ge=0, description="Total number of records processed.")
    successful_records: int = Field(
        ge=0, description="Number of successfully processed records."
    )
    failed_records: int = Field(
        ge=0, description="Number of records that failed to process."
    )
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when the import operation was completed.",
    )
    duration_seconds: float = Field(
        ge=0, description="Total duration of the import operation in seconds."
    )
    errors: Sequence[ImportErrorDetail] = Field(
        default_factory=list,
        description="List of detailed errors that occurred during the import.",
    )
    warnings: Sequence[ImportErrorDetail] = Field(
        default_factory=list,
        description="List of warnings that occurred during the import.",
    )
    import_format: ImportFormat = Field(description="Format of the imported data.")
    import_mode: ImportMode = Field(description="Mode used for the import operation.")
    application_id: str = Field(
        description="ID of the application where records were imported."
    )
    form_id: str = Field(description="ID of the form where records were imported.")
    created_records: int = Field(
        default=0, ge=0, description="Number of new records created during the import."
    )
    updated_records: int = Field(
        default=0,
        ge=0,
        description="Number of existing records updated during the import.",
    )
    deleted_records: int = Field(
        default=0,
        ge=0,
        description="Number of records deleted during the import (if applicable).",
    )
    skipped_records: int = Field(
        default=0, ge=0, description="Number of records skipped during the import."
    )
    import_mappings: Sequence[ImportMapping] = Field(
        default_factory=list,
        description="Field mappings used during the import operation.",
    )

    @model_validator(mode="after")
    def validate_counts(self) -> "ImportResult":
        """Validate that the record counts are consistent."""
        if self.successful_records + self.failed_records != self.total_records:
            raise ValueError(
                "successful_records + failed_records must equal total_records"
            )

        if (
            self.created_records
            + self.updated_records
            + self.deleted_records
            + self.skipped_records
            != self.total_records
        ):
            raise ValueError(
                "created_records + updated_records + "
                "deleted_records + skipped_records must equal total_records"
            )

        return self

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_records == 0:
            return 10.0
        return (self.successful_records / self.total_records) * 100.0

    @property
    def failure_rate(self) -> float:
        """Calculate the failure rate as a percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.failed_records / self.total_records) * 100.0


class ExportOptions(CreatorBaseModel):
    """Model for export configuration (filters, columns, formatting)."""

    include_header: bool = Field(
        default=True,
        description="Whether to include a header row in the exported data.",
    )
    columns: Optional[Sequence[str]] = Field(
        default=None, description="List of specific columns to include in the export."
    )
    filters: Optional[Mapping[str, Any]] = Field(
        default=None, description="Filter conditions to apply to the exported records."
    )
    sort_by: Optional[str] = Field(
        default=None, description="Field name to sort the exported records by."
    )
    sort_order: str = Field(
        default="asc",
        description="Sort order ('asc' for ascending, 'desc' for descending).",
    )
    format_options: Optional[Mapping[str, Any]] = Field(
        default=None,
        description="Format-specific options (e.g., date format, number format).",
    )
    max_records: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of records to export (None for all records).",
    )
    export_format: ExportFormat = Field(description="Format to export the data in.")
    include_metadata: bool = Field(
        default=False, description="Whether to include metadata fields in the export."
    )
    encoding: str = Field(
        default="utf-8", description="Character encoding for the exported file."
    )
    delimiter: str = Field(
        default=",", description="Delimiter character for delimited formats (CSV, TSV)."
    )
    include_form_schema: bool = Field(
        default=False,
        description="Whether to include form schema information in the export.",
    )

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate that sort_order is either 'asc' or 'desc'."""
        if v.lower() not in {"asc", "desc"}:
            raise ValueError("sort_order must be either 'asc' or 'desc'")
        return v.lower()

    @model_validator(mode="after")
    def validate_options(self) -> "ExportOptions":
        """Validate export options configuration."""
        if self.max_records is not None and self.max_records <= 0:
            raise ValueError("max_records must be greater than 0 or None")

        if self.columns is not None and len(self.columns) == 0:
            raise ValueError("columns list cannot be empty if provided")

        return self


class ExportResult(CreatorBaseModel):
    """Model for tracking export operations."""

    operation_id: str = Field(description="Unique identifier for the export operation.")
    total_records: int = Field(ge=0, description="Total number of records exported.")
    file_path: str = Field(description="Path to the exported file.")
    file_size_bytes: int = Field(
        ge=0, description="Size of the exported file in bytes."
    )
    export_format: ExportFormat = Field(description="Format of the exported data.")
    exported_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when the export operation was completed.",
    )
    duration_seconds: float = Field(
        ge=0, description="Total duration of the export operation in seconds."
    )
    application_id: str = Field(
        description="ID of the application from which records were exported."
    )
    form_id: str = Field(description="ID of the form from which records were exported.")
    filters_applied: Optional[Mapping[str, Any]] = Field(
        default=None, description="Filters that were applied during the export."
    )
    columns_exported: Optional[Sequence[str]] = Field(
        default=None, description="List of columns that were included in the export."
    )
    export_options: Optional[ExportOptions] = Field(
        default=None, description="Options used for the export operation."
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if the export failed."
    )
    is_successful: bool = Field(
        default=True, description="Whether the export operation completed successfully."
    )

    @model_validator(mode="after")
    def validate_export_result(self) -> "ExportResult":
        """Validate export result consistency."""
        if not self.is_successful and not self.error_message:
            raise ValueError("Unsuccessful export must have an error message")

        if self.is_successful and self.error_message:
            raise ValueError("Successful export should not have an error message")

        return self
