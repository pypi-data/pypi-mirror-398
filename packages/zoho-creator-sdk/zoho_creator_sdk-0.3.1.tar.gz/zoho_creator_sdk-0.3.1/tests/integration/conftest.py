"""Pytest configuration for integration tests.

This module provides fixtures and configuration for integration tests,
including setup and teardown of test environments.
"""

from __future__ import annotations

import asyncio
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from zoho_creator_sdk.client import ZohoCreatorClient
from zoho_creator_sdk.models import APIConfig, AuthConfig

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_config() -> APIConfig:
    """Create a mock API configuration for testing."""
    return APIConfig(dc="US", environment="testing", timeout=30, max_retries=3)


@pytest.fixture
def mock_auth_config() -> AuthConfig:
    """Create a mock authentication configuration for testing."""
    return AuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://example.com/callback",
        refresh_token="test_refresh_token",
    )


@pytest.fixture
def mock_client(
    mock_api_config: APIConfig, mock_auth_config: AuthConfig
) -> ZohoCreatorClient:
    """Create a ZohoCreatorClient with mocked HTTP client for integration testing."""
    with patch("zoho_creator_sdk.client.ConfigManager") as mock_config_manager, patch(
        "zoho_creator_sdk.client.get_auth_handler"
    ) as mock_get_auth_handler, patch(
        "zoho_creator_sdk.client.HTTPClient"
    ) as mock_http_client_class:
        # Setup mock config manager
        mock_config_manager.return_value.get_auth_config.return_value = mock_auth_config
        mock_config_manager.return_value.get_api_config.return_value = mock_api_config

        # Setup mock auth handler
        mock_auth_handler = Mock()
        mock_get_auth_handler.return_value = mock_auth_handler

        # Setup mock HTTP client
        mock_http_client = Mock()
        mock_http_client_class.return_value = mock_http_client

        # Create client with mocked dependencies
        client = ZohoCreatorClient()

        # Setup default successful response
        mock_http_client.get.return_value = Mock(
            status_code=200, json=lambda: {"message": "success"}
        )
        mock_http_client.post.return_value = Mock(
            status_code=201, json=lambda: {"message": "created"}
        )
        mock_http_client.put.return_value = Mock(
            status_code=200, json=lambda: {"message": "updated"}
        )
        mock_http_client.delete.return_value = Mock(
            status_code=200, json=lambda: {"message": "deleted"}
        )

        yield client


@pytest.fixture
def sample_application_data() -> dict:
    """Sample application data for testing."""
    return {
        "application_name": "Test Application",
        "link_name": "test_application",
        "application_id": "123456789",
        "creation_date": "2023-01-01",
        "category": "business",
        "date_format": "dd-MM-yyyy",
        "time_zone": "America/New_York",
        "created_by": "admin@example.com",
        "workspace_name": "test_workspace",
    }


@pytest.fixture
def sample_form_data() -> dict:
    """Sample form data for testing."""
    return {
        "form_name": "Contacts",
        "link_name": "contacts",
        "form_id": "987654321",
        "display_name": "Contact Information",
        "description": "Store contact details",
    }


@pytest.fixture
def sample_record_data() -> dict:
    """Sample record data for testing."""
    return {
        "ID": "12345",
        "Name": "John Doe",
        "Email": "john@example.com",
        "Phone": "+1-555-0123",
        "Created_Time": "2023-01-01T10:00:00Z",
    }


# Integration test markers
pytest.mark.integration = pytest.mark.integration
pytest.mark.api_test = pytest.mark.api_test
pytest.mark.workflow_test = pytest.mark.workflow_test
pytest.mark.e2e_test = pytest.mark.e2e_test


# Skip integration tests by default unless explicitly requested
def pytest_configure(config):
    """Configure pytest to handle integration tests."""
    config.addinivalue_line(
        "markers",
        (
            "integration: mark test as an integration test "
            "(requires real API or complex setup)"
        ),
    )
    config.addinivalue_line("markers", "api_test: mark test as an API integration test")
    config.addinivalue_line(
        "markers", "workflow_test: mark test as a workflow integration test"
    )
    config.addinivalue_line("markers", "e2e_test: mark test as an end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration tests appropriately."""
    # Check if integration tests should be run
    integration_flag = False

    # Check various ways integration tests might be enabled
    if hasattr(config, "option") and hasattr(config.option, "integration"):
        integration_flag = config.option.integration
    elif "--integration" in config.invocation_params.args:
        integration_flag = True
    elif "integration" in config.invocation_params.args:
        integration_flag = True

    # Skip integration tests unless explicitly requested
    if not integration_flag:
        skip_integration = pytest.mark.skip(
            reason=(
                "Integration tests are skipped by default. "
                "Use appropriate flag to run them."
            )
        )
        for item in items:
            if any(
                marker.name in ["integration", "api_test", "workflow_test", "e2e_test"]
                for marker in item.iter_markers()
            ):
                item.add_marker(skip_integration)
