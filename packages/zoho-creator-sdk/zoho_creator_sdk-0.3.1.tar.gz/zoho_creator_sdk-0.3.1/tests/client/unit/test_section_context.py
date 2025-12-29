"""Unit tests for :class:`zoho_creator_sdk.client.SectionContext`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import SectionContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import Section


class TestSectionContext:
    """Test cases for SectionContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        return client

    @pytest.fixture
    def section_context(self, mock_http_client: Mock) -> SectionContext:
        """Create a SectionContext instance for testing."""
        return SectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            section_link_name="test-section",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """SectionContext initializes correctly."""
        section_context = SectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            section_link_name="test-section",
            owner_name="test-owner",
        )

        assert section_context.http_client is mock_http_client
        assert section_context.app_link_name == "test-app"
        assert section_context.section_link_name == "test-section"
        assert section_context.owner_name == "test-owner"

    def test_get_section_success(self, section_context: SectionContext) -> None:
        """get_section makes correct API call and returns Section object."""
        section_data = {
            "id": "section-123",
            "name": "Test Section",
            "link_name": "test-section",
            "application_id": "test-app",
            "page_id": "test-page",
            "description": "A test section",
        }
        response_data = {"section": section_data}

        section_context.http_client.get.return_value = response_data

        result = section_context.get_section()

        expected_url = (
            "https://www.zohoapis.com/settings/test-owner/test-app/section/test-section"
        )
        section_context.http_client.get.assert_called_once_with(expected_url)

        assert isinstance(result, Section)
        assert result.name == "Test Section"
        assert result.id == "section-123"

    def test_get_section_with_minimal_data(
        self, section_context: SectionContext
    ) -> None:
        """get_section handles minimal section data correctly."""
        section_data = {
            "id": "basic-section",
            "name": "Basic Section",
            "link_name": "basic-section",
            "application_id": "test-app",
            "page_id": "test-page",
        }
        response_data = {"section": section_data}

        section_context.http_client.get.return_value = response_data

        result = section_context.get_section()

        assert isinstance(result, Section)
        assert result.name == "Basic Section"

    def test_get_section_with_missing_section_field(
        self, section_context: SectionContext
    ) -> None:
        """get_section handles response without section field."""
        response_data = {"status": "success"}  # No section field

        section_context.http_client.get.return_value = response_data

        # Should raise APIError when section data is missing
        with pytest.raises(APIError) as exc_info:
            section_context.get_section()

        assert "Failed to parse section data" in str(exc_info.value)

    def test_get_section_with_invalid_data(
        self, section_context: SectionContext
    ) -> None:
        """get_section raises APIError when section data is invalid."""
        response_data = {"section": {"invalid": "data"}}  # Invalid section data

        section_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            section_context.get_section()

        assert "Failed to parse section data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    @pytest.mark.parametrize(
        "app_link_name,section_link_name,owner_name,expected_url",
        [
            (
                "app1",
                "section1",
                "owner1",
                "https://www.zohoapis.com/settings/owner1/app1/section/section1",
            ),
            (
                "my-app",
                "header-section",
                "john-doe",
                (
                    "https://www.zohoapis.com/settings/"
                    "john-doe/my-app/section/header-section"
                ),
            ),
            (
                "app_with_underscores",
                "section_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/settings/owner_with_underscores/"
                    "app_with_underscores/section/section_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        section_link_name: str,
        owner_name: str,
        expected_url: str,
    ) -> None:
        """SectionContext constructs URLs correctly from various inputs."""
        section_context = SectionContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            section_link_name=section_link_name,
            owner_name=owner_name,
        )

        # Test get_section URL
        section_data = {
            "id": "test-section",
            "name": "Test",
            "link_name": "test",
            "application_id": "test-app",
            "page_id": "test-page",
        }
        section_context.http_client.get.return_value = {"section": section_data}
        section_context.get_section()

        section_context.http_client.get.assert_called_once_with(expected_url)

    def test_get_section_api_error_handling(
        self, section_context: SectionContext
    ) -> None:
        """get_section handles API errors correctly."""
        section_context.http_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            section_context.get_section()

        assert "API Error" in str(exc_info.value)

    @pytest.mark.parametrize(
        "section_link_name",
        [
            "section-123",
            "section-with-dashes",
            "section_with_underscores",
            "123456789",
            "header_section_main",
        ],
    )
    def test_with_various_section_names(
        self, mock_http_client: Mock, section_link_name: str
    ) -> None:
        """SectionContext works with various section name formats."""
        section_context = SectionContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            section_link_name=section_link_name,
            owner_name="test-owner",
        )

        # Test get_section
        section_data = {
            "id": "test-section",
            "name": "Test",
            "link_name": "test",
            "application_id": "test-app",
            "page_id": "test-page",
        }
        section_context.http_client.get.return_value = {"section": section_data}
        result = section_context.get_section()

        expected_url = (
            f"https://www.zohoapis.com/settings/test-owner/"
            f"test-app/section/{section_link_name}"
        )
        section_context.http_client.get.assert_called_once_with(expected_url)
        assert isinstance(result, Section)

    def test_get_section_with_complex_data(
        self, section_context: SectionContext
    ) -> None:
        """get_section handles complex section data correctly."""
        section_data = {
            "id": "section-456",
            "name": "Complex Section",
            "link_name": "complex-section",
            "application_id": "test-app",
            "page_id": "test-page",
            "description": "A complex section with many fields",
            "display_order": 1,
            "components": [
                {
                    "id": "comp-1",
                    "name": "Text Component",
                    "link_name": "text-component",
                    "component_type": 1,
                    "section_id": "section-456",
                },
                {
                    "id": "comp-2",
                    "name": "Image Component",
                    "link_name": "image-component",
                    "component_type": 2,
                    "section_id": "section-456",
                },
            ],
            "layout_settings": {
                "background_color": "#ffffff",
                "padding": 10,
                "margin": 5,
            },
            "conditional_display": {
                "condition": "user_role == 'admin'",
                "show_when_true": True,
            },
        }
        response_data = {"section": section_data}

        section_context.http_client.get.return_value = response_data

        result = section_context.get_section()

        assert isinstance(result, Section)
        assert result.name == "Complex Section"
        assert result.id == "section-456"

    def test_get_section_with_different_response_formats(
        self, section_context: SectionContext
    ) -> None:
        """get_section handles different response formats correctly."""
        # Valid cases that should succeed
        valid_test_cases = [
            {
                "section": {
                    "id": "test-section",
                    "name": "Test",
                    "link_name": "test",
                    "application_id": "test-app",
                    "page_id": "test-page",
                }
            },
            {
                "section": {
                    "id": "test-section",
                    "name": "Test",
                    "link_name": "test",
                    "application_id": "test-app",
                    "page_id": "test-page",
                    "is_visible": False,
                }
            },
        ]

        for response_data in valid_test_cases:
            section_context.http_client.get.return_value = response_data

            result = section_context.get_section()

            expected_url = (
                "https://www.zohoapis.com/settings/test-owner/"
                "test-app/section/test-section"
            )
            section_context.http_client.get.assert_called_once_with(expected_url)
            assert isinstance(result, Section)

            # Reset mock for next iteration
            section_context.http_client.get.reset_mock()

    def test_get_section_with_components(self, section_context: SectionContext) -> None:
        """get_section handles sections with components correctly."""
        section_data = {
            "id": "section-with-components",
            "name": "Section with Components",
            "link_name": "section-with-components",
            "application_id": "test-app",
            "page_id": "test-page",
            "components": [
                {
                    "id": "comp-header",
                    "name": "Header Component",
                    "link_name": "header-component",
                    "component_type": 1,
                    "section_id": "section-with-components",
                },
                {
                    "id": "comp-content",
                    "name": "Content Component",
                    "link_name": "content-component",
                    "component_type": 2,
                    "section_id": "section-with-components",
                },
                {
                    "id": "comp-footer",
                    "name": "Footer Component",
                    "link_name": "footer-component",
                    "component_type": 3,
                    "section_id": "section-with-components",
                },
            ],
        }
        response_data = {"section": section_data}

        section_context.http_client.get.return_value = response_data

        result = section_context.get_section()

        assert isinstance(result, Section)
        assert result.name == "Section with Components"
        assert result.id == "section-with-components"
        assert len(result.components) == 3
