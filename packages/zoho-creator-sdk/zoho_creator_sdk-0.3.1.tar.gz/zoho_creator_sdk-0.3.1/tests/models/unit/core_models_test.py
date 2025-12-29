"""Unit tests for core models."""

from __future__ import annotations

from datetime import datetime

from zoho_creator_sdk.models.core import Application, Record, User


def test_application_accepts_alias_fields() -> None:
    app = Application(
        application_name="CRM",
        date_format="dd-MMM-yyyy",
        creation_date="2024-01-01",
        link_name="crm",
        category=1,
        time_zone="UTC",
        created_by="user",
        workspace_name="workspace",
    )

    assert app.link_name == "crm"


def test_record_parses_datetime_fields() -> None:
    record = Record(
        id="1",
        form_id="form",
        created_time="2024-01-01T00:00:00Z",
        modified_time="2024-01-01T01:00:00Z",
        owner="owner",
        data={"Name": "Ada"},
    )

    assert isinstance(record.created_time, datetime)


def test_user_optional_attributes() -> None:
    user = User(
        id="1",
        email="user@example.com",
        first_name="Ada",
        last_name="Lovelace",
        role="admin",
        active=True,
    )

    assert user.status is None


def test_record_get_form_data() -> None:
    """Test the get_form_data method of Record model."""
    # Test with only metadata fields
    record = Record(
        id="1",
        form_id="form",
        created_time="2024-01-01T00:00:00Z",
        modified_time="2024-01-01T01:00:00Z",
        owner="owner",
    )

    form_data = record.get_form_data()
    assert form_data == {}

    # Test with metadata and form fields
    record = Record(
        id="1",
        form_id="form",
        created_time="2024-01-01T00:00:00Z",
        modified_time="2024-01-01T01:00:00Z",
        owner="owner",
        Name="Test Name",
        Email="test@example.com",
        Age=25,
    )

    form_data = record.get_form_data()
    expected = {"Name": "Test Name", "Email": "test@example.com", "Age": 25}
    assert form_data == expected

    # Test with None values in form fields
    record = Record(
        id="1",
        form_id="form",
        created_time="2024-01-01T00:00:00Z",
        modified_time="2024-01-01T01:00:00Z",
        owner="owner",
        Name="Test Name",
        Email=None,
        Age=25,
    )

    form_data = record.get_form_data()
    expected = {"Name": "Test Name", "Age": 25}
    assert form_data == expected
