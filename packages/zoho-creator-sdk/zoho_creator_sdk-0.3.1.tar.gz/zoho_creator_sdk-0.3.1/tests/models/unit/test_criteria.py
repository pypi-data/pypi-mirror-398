"""Unit tests for criteria functionality."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.models.criteria import (
    CriteriaBuilder,
    create_complex_criteria,
    create_criteria,
)


class TestCriteriaBuilder:
    """Test cases for CriteriaBuilder class."""

    def test_simple_equals_condition(self) -> None:
        """Test simple equals condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Name").equals("John").build()

        expected = {"Name": "John"}
        assert criteria == expected

    def test_string_equals_condition(self) -> None:
        """Test string equals condition with quotes."""
        builder = CriteriaBuilder()
        criteria = builder.field("Status").equals("Active").build()

        expected = {"Status": "Active"}
        assert criteria == expected

    def test_numeric_equals_condition(self) -> None:
        """Test numeric equals condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Age").equals(25).build()

        expected = {"Age": 25}
        assert criteria == expected

    def test_not_equals_condition(self) -> None:
        """Test not equals condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Status").not_equals("Deleted").build()

        expected = {"Status": {"not_equals": "Deleted"}}
        assert criteria == expected

    def test_greater_than_condition(self) -> None:
        """Test greater than condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Age").greater_than(18).build()

        expected = {"Age": {"greater_than": 18}}
        assert criteria == expected

    def test_less_than_condition(self) -> None:
        """Test less than condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Score").less_than(100).build()

        expected = {"Score": {"less_than": 100}}
        assert criteria == expected

    def test_between_condition(self) -> None:
        """Test between condition."""
        builder = CriteriaBuilder()
        criteria = (
            builder.field("Created_Time").between("2024-01-01", "2024-12-31").build()
        )

        expected = {"Created_Time": {"between": ["2024-01-01", "2024-12-31"]}}
        assert criteria == expected

    def test_contains_condition(self) -> None:
        """Test contains condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Description").contains("urgent").build()

        expected = {"Description": {"contains": "urgent"}}
        assert criteria == expected

    def test_starts_with_condition(self) -> None:
        """Test starts with condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Email").starts_with("john@").build()

        expected = {"Email": {"starts_with": "john@"}}
        assert criteria == expected

    def test_ends_with_condition(self) -> None:
        """Test ends with condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Email").ends_with("@company.com").build()

        expected = {"Email": {"ends_with": "@company.com"}}
        assert criteria == expected

    def test_in_list_condition(self) -> None:
        """Test in list condition."""
        builder = CriteriaBuilder()
        criteria = (
            builder.field("Status").in_list(["Active", "Pending", "Review"]).build()
        )

        expected = {"Status": {"in": ["Active", "Pending", "Review"]}}
        assert criteria == expected

    def test_not_in_list_condition(self) -> None:
        """Test not in list condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Status").not_in_list(["Deleted", "Archived"]).build()

        expected = {"Status": {"not_in": ["Deleted", "Archived"]}}
        assert criteria == expected

    def test_is_empty_condition(self) -> None:
        """Test is empty condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Notes").is_empty().build()

        expected = {"Notes": {"is_empty": True}}
        assert criteria == expected

    def test_is_not_empty_condition(self) -> None:
        """Test is not empty condition."""
        builder = CriteriaBuilder()
        criteria = builder.field("Notes").is_not_empty().build()

        expected = {"Notes": {"is_not_empty": True}}
        assert criteria == expected

    def test_multiple_conditions(self) -> None:
        """Test multiple conditions with AND logic."""
        builder = CriteriaBuilder()
        criteria = (
            builder.field("Name")
            .equals("John")
            .and_field("Age")
            .greater_than(25)
            .and_field("Status")
            .equals("Active")
            .build()
        )

        expected = {"Name": "John", "Age": {"greater_than": 25}, "Status": "Active"}
        assert criteria == expected

    def test_or_conditions(self) -> None:
        """Test OR conditions - no longer overwrites first condition."""
        builder = CriteriaBuilder()
        criteria = (
            builder.field("Name").equals("John").or_field("Name").equals("Jane").build()
        )

        # Implementation no longer overwrites first condition
        expected = {"Name": ["John", "Jane"]}
        assert criteria == expected

    def test_chained_conditions(self) -> None:
        """Test chained conditions - no longer overwrites first condition."""
        builder = CriteriaBuilder()
        criteria = (
            builder.field("Age")
            .greater_than_or_equal(18)
            .and_field("Age")
            .less_than_or_equal(65)
            .build()
        )

        # Implementation no longer overwrites first condition
        expected = {"Age": [{"greater_than_or_equal": 18}, {"less_than_or_equal": 65}]}
        assert criteria == expected

    def test_empty_builder_error(self) -> None:
        """Test that building without conditions raises an error."""
        builder = CriteriaBuilder()

        with pytest.raises(ValueError, match="No conditions have been added"):
            builder.build()

    def test_field_without_condition_error(self) -> None:
        """Test that calling field() without adding a condition raises an error."""
        builder = CriteriaBuilder()
        builder.field("Name")

        with pytest.raises(
            ValueError, match="No conditions have been added to the criteria builder"
        ):
            builder.build()

    def test_to_criteria_string_simple(self) -> None:
        """Test conversion to string format for simple criteria."""
        builder = CriteriaBuilder()
        criteria_str = builder.field("Name").equals("John").to_criteria_string()

        assert criteria_str == '(Name == "John")'

    def test_to_criteria_string_multiple(self) -> None:
        """Test conversion to string format for multiple criteria."""
        builder = CriteriaBuilder()
        criteria_str = (
            builder.field("Name")
            .equals("John")
            .and_field("Age")
            .greater_than(25)
            .to_criteria_string()
        )

        assert criteria_str == '(Name == "John") && (Age > 25)'

    def test_to_criteria_string_between(self) -> None:
        """Test conversion to string format for between criteria."""
        builder = CriteriaBuilder()
        criteria_str = (
            builder.field("Created_Time")
            .between("2024-01-01", "2024-12-31")
            .to_criteria_string()
        )

        assert criteria_str == '(Created_Time between "2024-01-01" and "2024-12-31")'


class TestCreateCriteria:
    """Test cases for create_criteria function."""

    def test_simple_criteria(self) -> None:
        """Test simple criteria creation."""
        criteria = create_criteria(Name="John", Status="Active")

        expected = {"Name": "John", "Status": "Active"}
        assert criteria == expected

    def test_empty_criteria(self) -> None:
        """Test empty criteria creation."""
        criteria = create_criteria()

        assert criteria == {}

    def test_mixed_types(self) -> None:
        """Test criteria with mixed data types."""
        criteria = create_criteria(Name="John", Age=25, Active=True)

        expected = {"Name": "John", "Age": 25, "Active": True}
        assert criteria == expected


class TestCreateComplexCriteria:
    """Test cases for create_complex_criteria function."""

    def test_simple_conditions(self) -> None:
        """Test simple condition list."""
        conditions = [
            {"field": "Name", "operator": "equals", "value": "John"},
            {"field": "Age", "operator": "greater_than", "value": 25},
        ]
        criteria = create_complex_criteria(conditions)

        expected = {"Name": "John", "Age": {"greater_than": 25}}
        assert criteria == expected

    def test_mixed_operators(self) -> None:
        """Test conditions with different operators."""
        conditions = [
            {"field": "Status", "operator": "equals", "value": "Active"},
            {"field": "Score", "operator": "less_than", "value": 100},
            {
                "field": "Created",
                "operator": "between",
                "value": ["2024-01-01", "2024-12-31"],
            },
        ]
        criteria = create_complex_criteria(conditions)

        expected = {
            "Status": "Active",
            "Score": {"less_than": 100},
            "Created": {"between": ["2024-01-01", "2024-12-31"]},
        }
        assert criteria == expected

    def test_default_equals_operator(self) -> None:
        """Test that missing operator defaults to equals."""
        conditions = [{"field": "Name", "value": "John"}]  # No operator specified
        criteria = create_complex_criteria(conditions)

        expected = {"Name": "John"}
        assert criteria == expected

    def test_empty_conditions(self) -> None:
        """Test empty conditions list."""
        criteria = create_complex_criteria([])

        assert criteria == {}
