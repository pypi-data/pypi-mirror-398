"""Unit tests for :class:`zoho_creator_sdk.client.PageContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import PageContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Page


class TestPageContext:
    """Test cases for PageContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def page_context(self, mock_http_client: Mock) -> PageContext:
        """Create a PageContext instance for testing."""
        return PageContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            page_link_name="test-page",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """PageContext initializes correctly."""
        page_context = PageContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            page_link_name="test-page",
            owner_name="test-owner",
        )

        assert page_context.http_client is mock_http_client
        assert page_context.app_link_name == "test-app"
        assert page_context.page_link_name == "test-page"
        assert page_context.owner_name == "test-owner"

    def test_get_page_success(self, page_context: PageContext) -> None:
        """get_page makes correct API call and returns Page object."""
        page_data = {
            "page_name": "Test Page",
            "page_id": "page-123",
            "description": "A test page",
            "is_published": True,
        }
        response_data = {"page": page_data}

        page_context.http_client.get.return_value = response_data

        result = page_context.get_page()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/page/test-page"
        )
        page_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, Page)
        assert result.page_name == "Test Page"
        assert result.page_id == "page-123"

    def test_get_page_with_minimal_data(self, page_context: PageContext) -> None:
        """get_page handles minimal page data correctly."""
        page_data = {"page_name": "Basic Page"}
        response_data = {"page": page_data}

        page_context.http_client.get.return_value = response_data

        result = page_context.get_page()

        assert isinstance(result, Page)
        assert result.page_name == "Basic Page"

    def test_get_page_with_missing_page_field(self, page_context: PageContext) -> None:
        """get_page handles response without page field."""
        response_data = {"status": "success"}  # No page field

        page_context.http_client.get.return_value = response_data

        result = page_context.get_page()

        # Should create Page with empty data
        assert isinstance(result, Page)

    def test_get_page_with_invalid_data(self, page_context: PageContext) -> None:
        """get_page raises APIError when page data is invalid."""
        response_data = {"page": {"invalid": "data"}}  # Invalid page data

        page_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            page_context.get_page()

        assert "Failed to parse page data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    @pytest.mark.parametrize(
        "app_link_name,page_link_name,owner_name,expected_url",
        [
            (
                "app1",
                "page1",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/page/page1",
            ),
            (
                "my-app",
                "home-page",
                "john-doe",
                "https://www.zohoapis.com/settings/john-doe/my-app/page/home-page",
            ),
            (
                "app_with_underscores",
                "page_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/page/page_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        page_link_name: str,
        owner_name: str,
        expected_url: str,
    ) -> None:
        """PageContext constructs URLs correctly from various inputs."""
        page_context = PageContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            page_link_name=page_link_name,
            owner_name=owner_name,
        )

        # Test get_page URL
        page_data = {"page_name": "Test"}
        page_context.http_client.get.return_value = {"page": page_data}
        page_context.get_page()

        page_context.http_client.get.assert_called_once_with(expected_url)

    def test_get_page_api_error_handling(self, page_context: PageContext) -> None:
        """get_page handles API errors correctly."""
        page_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            page_context.get_page()

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "page_link_name",
        [
            "page-123",
            "page-with-dashes",
            "page_with_underscores",
            "123456789",
            "home_page_main",
        ],
    )
    def test_with_various_page_names(
        self, mock_http_client: Mock, page_link_name: str
    ) -> None:
        """PageContext works with various page name formats."""
        page_context = PageContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            page_link_name=page_link_name,
            owner_name="test-owner",
        )

        # Test get_page
        page_data = {"page_name": "Test"}
        page_context.http_client.get.return_value = {"page": page_data}
        result = page_context.get_page()

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/"
            f"test-app/page/{page_link_name}"
        )
        page_context.http_client.get.assert_called_once_with(expected_url)
        assert isinstance(result, Page)

    def test_get_page_with_complex_data(self, page_context: PageContext) -> None:
        """get_page handles complex page data correctly."""
        page_data = {
            "page_name": "Complex Page",
            "page_id": "page-456",
            "description": "A complex page with many fields",
            "is_published": True,
            "layout": "grid",
            "components": [
                {"type": "header", "content": "Header"},
                {"type": "content", "content": "Main content"},
                {"type": "footer", "content": "Footer"},
            ],
            "seo_settings": {
                "title": "Page Title",
                "description": "Page description",
                "keywords": ["keyword1", "keyword2"],
            },
            "access_permissions": {
                "public": True,
                "allowed_roles": ["admin", "editor"],
            },
        }
        response_data = {"page": page_data}

        page_context.http_client.get.return_value = response_data

        result = page_context.get_page()

        assert isinstance(result, Page)
        assert result.page_name == "Complex Page"
        assert result.page_id == "page-456"

    def test_get_page_with_different_response_formats(
        self, page_context: PageContext
    ) -> None:
        """get_page handles different response formats correctly."""
        test_cases = [
            {"page": {"page_name": "Test Page"}},
            {"page": {"page_name": "Test", "page_id": "123"}},
            {"page": {"page_name": "Test", "is_published": False}},
            {"page": {}},  # Empty page object
            {"page": {"page_name": None}},  # Null values
        ]

        for i, response_data in enumerate(test_cases):
            page_context.http_client.get.return_value = response_data

            result = page_context.get_page()

            expected_url = (
                "https://www.zohoapis.com/settings/test-owner/test-app/page/test-page"
            )
            page_context.http_client.get.assert_called_once_with(expected_url)
            assert isinstance(result, Page)

            # Reset mock for next iteration
            page_context.http_client.get.reset_mock()
