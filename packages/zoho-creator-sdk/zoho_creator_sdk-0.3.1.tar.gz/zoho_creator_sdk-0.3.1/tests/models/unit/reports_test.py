"""Unit tests for report models."""

from __future__ import annotations

from datetime import datetime

from zoho_creator_sdk.models.enums import ReportType
from zoho_creator_sdk.models.reports import Report, ReportColumn, ReportFilter


def test_report_model() -> None:
    report = Report(
        id="r1",
        name="Leads",
        link_name="leads",
        application_id="app",
        form_id="form",
        report_type=ReportType.LIST,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
        owner="owner",
        active=True,
    )

    assert report.is_public is False


def test_report_column_defaults() -> None:
    column = ReportColumn(
        id="c1",
        name="Name",
        link_name="name",
        field_id="field",
        report_id="report",
        display_order=1,
    )

    assert column.sortable is True


def test_report_filter_instantiation() -> None:
    filt = ReportFilter(
        id="f1",
        name="Recent",
        report_id="report",
        criteria={"Created_Time": {"between": ["2024-01-01", "2024-01-31"]}},
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
    )

    assert filt.is_default is False
