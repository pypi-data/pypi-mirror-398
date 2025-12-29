"""
Tests for criteria conversion methods in FormContext and ReportContext.
"""

import pytest

from zoho_creator_sdk.client import FormContext, ReportContext


@pytest.fixture
def form_context():
    """Create a FormContext instance for testing."""
    # HTTP client and config not needed for testing criteria conversion
    return FormContext(None, "test-app", "test-form", "test-owner")


@pytest.fixture
def report_context():
    """Create a ReportContext instance for testing."""
    # HTTP client and config not needed for testing criteria conversion
    return ReportContext(None, "test-app", "test-report", "test-owner")


class TestFormContextCriteriaConversion:
    """Test FormContext criteria conversion methods."""

    def test_handle_in_with_strings(self, form_context):
        """Test _handle_in with string values."""
        result = form_context._handle_in("Bug_ID", ["BUG-001", "BUG-002"])
        assert result == 'Bug_ID in {"BUG-001","BUG-002"}'

    def test_handle_in_with_numbers(self, form_context):
        """Test _handle_in with numeric values."""
        result = form_context._handle_in("Age", [25, 30, 35])
        assert result == "Age in {25,30,35}"

    def test_handle_in_with_mixed_types(self, form_context):
        """Test _handle_in with mixed types."""
        result = form_context._handle_in("Status", [1, "Active", 2])
        assert result == 'Status in {1,"Active",2}'

    def test_handle_not_in_with_strings(self, form_context):
        """Test _handle_not_in with string values."""
        result = form_context._handle_not_in("Status", ["Deleted", "Archived"])
        assert result == 'Status not in {"Deleted","Archived"}'

    def test_handle_not_in_with_numbers(self, form_context):
        """Test _handle_not_in with numeric values."""
        result = form_context._handle_not_in("Age", [0, 1, 2])
        assert result == "Age not in {0,1,2}"

    def test_convert_criteria_to_api_format_with_in_list(self, form_context):
        """Test full criteria conversion with in_list operator."""
        criteria = {"Bug_ID": {"in": ["BUG-001", "BUG-002"]}}
        result = form_context._convert_criteria_to_api_format(criteria)
        assert result == '(Bug_ID in {"BUG-001","BUG-002"})'

    def test_convert_criteria_to_api_format_with_not_in_list(self, form_context):
        """Test full criteria conversion with not_in_list operator."""
        criteria = {"Status": {"not_in": ["Deleted", "Archived"]}}
        result = form_context._convert_criteria_to_api_format(criteria)
        assert result == '(Status not in {"Deleted","Archived"})'


class TestReportContextCriteriaConversion:
    """Test ReportContext criteria conversion methods."""

    def test_handle_in_with_strings(self, report_context):
        """Test _handle_in with string values."""
        result = report_context._handle_in("Bug_ID", ["BUG-001", "BUG-002"])
        assert result == 'Bug_ID in {"BUG-001","BUG-002"}'

    def test_handle_in_with_numbers(self, report_context):
        """Test _handle_in with numeric values."""
        result = report_context._handle_in("Age", [25, 30, 35])
        assert result == "Age in {25,30,35}"

    def test_handle_in_with_mixed_types(self, report_context):
        """Test _handle_in with mixed types."""
        result = report_context._handle_in("Status", [1, "Active", 2])
        assert result == 'Status in {1,"Active",2}'

    def test_handle_not_in_with_strings(self, report_context):
        """Test _handle_not_in with string values."""
        result = report_context._handle_not_in("Status", ["Deleted", "Archived"])
        assert result == 'Status not in {"Deleted","Archived"}'

    def test_handle_not_in_with_numbers(self, report_context):
        """Test _handle_not_in with numeric values."""
        result = report_context._handle_not_in("Age", [0, 1, 2])
        assert result == "Age not in {0,1,2}"

    def test_convert_criteria_to_api_format_with_in_list(self, report_context):
        """Test full criteria conversion with in_list operator."""
        criteria = {"Bug_ID": {"in": ["BUG-001", "BUG-002"]}}
        result = report_context._convert_criteria_to_api_format(criteria)
        assert result == '(Bug_ID in {"BUG-001","BUG-002"})'

    def test_convert_criteria_to_api_format_with_not_in_list(self, report_context):
        """Test full criteria conversion with not_in_list operator."""
        criteria = {"Status": {"not_in": ["Deleted", "Archived"]}}
        result = report_context._convert_criteria_to_api_format(criteria)
        assert result == '(Status not in {"Deleted","Archived"})'
