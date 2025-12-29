"""Unit tests for :class:`zoho_creator_sdk.client.ReportContext`."""

from __future__ import annotations

from collections.abc import Generator
from typing import Dict
from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from zoho_creator_sdk.client import ReportContext
from zoho_creator_sdk.exceptions import APIError
from zoho_creator_sdk.models import FieldConfig, Record


class TestReportContext:
    """Test cases for ReportContext class."""

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        client = Mock()
        client.config.base_url = "https://www.zohoapis.com"
        client.config.max_records_per_request = 200
        return client

    @pytest.fixture
    def report_context(self, mock_http_client: Mock) -> ReportContext:
        """Create a ReportContext instance for testing."""
        return ReportContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            report_link_name="test-report",
            owner_name="test-owner",
        )

    def test_initialization(self, mock_http_client: Mock) -> None:
        """ReportContext initializes correctly."""
        report_context = ReportContext(
            http_client=mock_http_client,
            app_link_name="test-app",
            report_link_name="test-report",
            owner_name="test-owner",
        )

        assert report_context.http_client is mock_http_client
        assert report_context.app_link_name == "test-app"
        assert report_context.report_link_name == "test-report"
        assert report_context.owner_name == "test-owner"

    def test_get_records_single_page(self, report_context: ReportContext) -> None:
        """get_records handles single page response correctly."""
        response_data = {
            "data": [
                {"ID": "1", "Name": "John", "Email": "john@example.com"},
                {"ID": "2", "Name": "Jane", "Email": "jane@example.com"},
            ],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records(limit=10))

        assert len(records) == 2
        assert all(isinstance(record, Record) for record in records)
        assert records[0].ID == "1"
        assert records[1].ID == "2"

        report_context.http_client.get.assert_called_once_with(
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report",
            params={"limit": 10},
        )

    def test_get_records_multiple_pages(self, report_context: ReportContext) -> None:
        """get_records handles pagination correctly."""
        # First page response
        first_page = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {
                "more_records": True,
                "next_page_token": "token123",
            },
        }

        # Second page response
        second_page = {
            "data": [{"ID": "2", "Name": "Jane"}],
            "meta": {"more_records": False},
        }

        # Third page response (empty)
        third_page = {
            "data": [],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.side_effect = [
            first_page,
            second_page,
            third_page,
        ]

        records = list(report_context.get_records(limit=5))

        assert len(records) == 2
        assert records[0].ID == "1"
        assert records[1].ID == "2"

        # Verify two API calls were made (no extra call after more_records=False)
        assert report_context.http_client.get.call_count == 2

        # First call
        first_call = report_context.http_client.get.call_args_list[0]
        assert first_call[0][0] == (
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report"
        )
        assert first_call[1]["params"] == {"limit": 5}

        # Second call with pagination token
        second_call = report_context.http_client.get.call_args_list[1]
        assert second_call[0][0] == (
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report"
        )
        assert second_call[1]["params"] == {"limit": 5, "next_page_token": "token123"}

        # Third response is provided but should not be used since
        # the second page had more_records=False

    def test_get_records_empty_response(self, report_context: ReportContext) -> None:
        """get_records handles empty response correctly."""
        response_data = {"data": [], "meta": {"more_records": False}}

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records())

        assert len(records) == 0
        report_context.http_client.get.assert_called_once()

    def test_get_records_no_data_field(self, report_context: ReportContext) -> None:
        """get_records handles response without data field correctly."""
        response_data = {"meta": {"more_records": False}}

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records())

        assert len(records) == 0
        report_context.http_client.get.assert_called_once()

    def test_get_records_with_invalid_record_data(
        self, report_context: ReportContext
    ) -> None:
        """get_records raises APIError when record data is invalid."""
        response_data = {
            "data": [{"invalid": "data"}],  # Missing required fields
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        with pytest.raises(APIError) as exc_info:
            list(report_context.get_records())

        assert "Failed to parse record data" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, PydanticValidationError)

    def test_get_records_pagination_warning(
        self, report_context: ReportContext
    ) -> None:
        """get_records logs warning when more_records is True but no token."""
        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": True},  # No next_page_token
        }

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records())

        # Should stop after first page due to missing token
        assert len(records) == 1
        assert report_context.http_client.get.call_count == 1

    def test_get_records_with_complex_parameters(
        self, report_context: ReportContext
    ) -> None:
        """get_records passes through complex query parameters correctly."""
        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        records = list(
            report_context.get_records(
                limit=20,
                sort_by="Name",
                sort_order="asc",
                criteria="Name='John'",
                start_index=10,
                end_index=30,
                custom_fields="Email,Phone",
            )
        )

        assert len(records) == 1

        report_context.http_client.get.assert_called_once_with(
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report",
            params={
                "limit": 20,
                "sort_by": "Name",
                "sort_order": "asc",
                "criteria": "Name='John'",
                "start_index": 10,
                "end_index": 30,
                "custom_fields": "Email,Phone",
            },
        )

    def test_get_records_generator_behavior(
        self, report_context: ReportContext
    ) -> None:
        """get_records returns a generator that yields records lazily."""
        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        # Should return a generator
        result = report_context.get_records()
        assert isinstance(result, Generator)

        # API call should not be made yet
        report_context.http_client.get.assert_not_called()

        # API call should be made when we start iterating
        first_record = next(result)
        assert isinstance(first_record, Record)
        assert first_record.ID == "1"

        # API call should have been made now
        report_context.http_client.get.assert_called_once()

    def test_get_records_with_pagination_token_in_params(
        self, report_context: ReportContext
    ) -> None:
        """get_records handles initial pagination token in parameters."""
        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records(next_page_token="initial_token"))

        assert len(records) == 1

        report_context.http_client.get.assert_called_once_with(
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report",
            params={"next_page_token": "initial_token"},
        )

    def test_get_records_pagination_token_override(
        self, report_context: ReportContext
    ) -> None:
        """get_records overrides pagination token when provided in response."""
        # First call with initial token
        first_page = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {
                "more_records": True,
                "next_page_token": "new_token",
            },
        }

        # Second call with new token
        second_page = {
            "data": [{"ID": "2", "Name": "Jane"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.side_effect = [first_page, second_page]

        records = list(report_context.get_records(next_page_token="initial_token"))

        assert len(records) == 2

        # Verify calls
        first_call = report_context.http_client.get.call_args_list[0]
        assert first_call[1]["params"] == {"next_page_token": "initial_token"}

        second_call = report_context.http_client.get.call_args_list[1]
        assert second_call[1]["params"] == {"next_page_token": "new_token"}

    def test_get_records_with_field_config_and_fields(
        self, report_context: ReportContext
    ) -> None:
        """get_records applies field_config enum and fields list correctly."""

        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        records = list(
            report_context.get_records(
                field_config=FieldConfig.DETAIL_VIEW,
                fields=["Email", "Phone"],
            )
        )

        assert len(records) == 1

        report_context.http_client.get.assert_called_once_with(
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report",
            params={
                "field_config": "detail_view",
                "fields": "Email,Phone",
                "max_records": 200,
            },
        )

    def test_get_records_with_record_cursor_header(
        self, report_context: ReportContext
    ) -> None:
        """get_records sends record_cursor header when provided."""

        response_data = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": False},
        }

        report_context.http_client.get.return_value = response_data

        records = list(report_context.get_records(record_cursor="cursor123"))

        assert len(records) == 1

        report_context.http_client.get.assert_called_once_with(
            "https://www.zohoapis.com/data/test-owner/test-app/report/test-report",
            params={"max_records": 200},
            headers={"record_cursor": "cursor123"},
        )

    @pytest.mark.parametrize(
        "app_link_name,report_link_name,owner_name,expected_url",
        [
            (
                "app1",
                "report1",
                "owner1",
                "https://www.zohoapis.com/data/owner1/app1/report/report1",
            ),
            (
                "my-app",
                "sales-report",
                "john-doe",
                "https://www.zohoapis.com/data/john-doe/my-app/report/sales-report",
            ),
            (
                "app_with_underscores",
                "report_with_underscores",
                "owner_with_underscores",
                (
                    "https://www.zohoapis.com/data/owner_with_underscores/"
                    "app_with_underscores/report/report_with_underscores"
                ),
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_http_client: Mock,
        app_link_name: str,
        report_link_name: str,
        owner_name: str,
        expected_url: str,
    ) -> None:
        """ReportContext constructs URLs correctly from various inputs."""
        report_context = ReportContext(
            http_client=mock_http_client,
            app_link_name=app_link_name,
            report_link_name=report_link_name,
            owner_name=owner_name,
        )

        # Test get_records URL
        report_context.http_client.get.return_value = {
            "data": [],
            "meta": {"more_records": False},
        }
        list(report_context.get_records())

        report_context.http_client.get.assert_called_once_with(
            expected_url, params={"max_records": 200}
        )

    def test_get_records_large_dataset(self, report_context: ReportContext) -> None:
        """get_records handles large datasets with multiple pages efficiently."""
        # Simulate 5 pages of data
        pages = []
        for i in range(5):
            page_data = {
                "data": [
                    {"ID": f"{i*10 + j}", "Name": f"User {i*10 + j}"} for j in range(10)
                ],
                "meta": {
                    "more_records": i < 4,  # Last page has more_records=False
                    "next_page_token": f"token_{i+1}" if i < 4 else None,
                },
            }
            pages.append(page_data)

        report_context.http_client.get.side_effect = pages

        records = list(report_context.get_records(limit=10))

        # Should have 50 records total (5 pages * 10 records each)
        assert len(records) == 50
        assert report_context.http_client.get.call_count == 5

        # Verify first and last records
        assert records[0].ID == "0"
        assert records[-1].ID == "49"

    def test_iter_records_with_cursor_uses_record_cursor_header(
        self, report_context: ReportContext
    ) -> None:
        """iter_records_with_cursor follows the record_cursor header across pages."""

        first_page = {
            "data": [{"ID": "1", "Name": "John"}],
            "meta": {"more_records": True},
        }
        second_page = {
            "data": [{"ID": "2", "Name": "Jane"}],
            "meta": {"more_records": False},
        }

        def _get_with_response(
            url: str, params: Dict[str, object], headers: Dict[str, str]
        ):
            if not headers:
                return first_page, {"record_cursor": "cursor2"}
            assert headers.get("record_cursor") == "cursor2"
            return second_page, {}

        report_context.http_client.get_with_response = Mock(  # type: ignore[assignment]
            side_effect=_get_with_response
        )

        records = list(report_context.iter_records_with_cursor())

        assert [r.ID for r in records] == ["1", "2"]
