"""Unit tests for the connection model."""

from __future__ import annotations

from datetime import datetime

from zoho_creator_sdk.models.connection import Connection


def test_connection_model_accepts_configuration() -> None:
    connection = Connection(
        id="conn",
        name="CRM",
        connection_type="REST",
        application_id="app",
        configuration={"endpoint": "https://example.com"},
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow(),
        owner="owner",
    )

    assert connection.configuration["endpoint"] == "https://example.com"
