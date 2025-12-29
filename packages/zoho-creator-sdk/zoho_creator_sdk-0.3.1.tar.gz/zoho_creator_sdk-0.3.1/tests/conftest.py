"""Global pytest fixtures for the Zoho Creator SDK test suite."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

import pytest

from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.models import APIConfig, AuthConfig

# Test markers
pytest.mark.api_test = pytest.mark.api_test
pytest.mark.integration = pytest.mark.integration
pytest.mark.workflow_test = pytest.mark.workflow_test
pytest.mark.e2e_test = pytest.mark.e2e_test


def pytest_configure(config):
    """Configure pytest to handle custom markers."""
    config.addinivalue_line("markers", "api_test: mark test as an API integration test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line(
        "markers", "workflow_test: mark test as a workflow integration test"
    )
    config.addinivalue_line("markers", "e2e_test: mark test as an end-to-end test")


@pytest.fixture
def api_config() -> APIConfig:
    """Provide a baseline API configuration for tests."""

    return APIConfig(
        datacenter=Datacenter.US,
        timeout=10,
        max_retries=2,
        retry_delay=0.1,
    )


@pytest.fixture
def auth_config() -> AuthConfig:
    """Provide a baseline Auth configuration for tests."""

    return AuthConfig(
        client_id="client",
        client_secret="secret",
        redirect_uri="https://example.com/callback",
        refresh_token="refresh",
        access_token="initial",
        token_expiry=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


@pytest.fixture
def sample_record_data() -> Mapping[str, object]:
    """Common record payload used by multiple tests."""

    return {
        "id": "rec1",
        "form_link_name": "leads",
        "data": {"Name": "Ada"},
        "created_time": "2024-01-01T10:00:00Z",
    }
