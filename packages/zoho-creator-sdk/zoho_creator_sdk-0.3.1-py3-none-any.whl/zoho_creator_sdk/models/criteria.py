"""
Criteria builder for Zoho Creator API filtering.

This module provides a fluent interface for building complex filtering criteria
for Zoho Creator API requests, supporting multiple conditions and operators.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


class CriteriaBuilder:
    """
    A fluent interface for building complex filtering criteria.

    This builder supports various operators and allows combining multiple conditions
    for sophisticated filtering of Zoho Creator records.

    Example:
        builder = CriteriaBuilder()
        criteria = (builder.field("Name").equals("John")
                   .and_field("Age").greater_than(25)
                   .or_field("Status").equals("Active")
                   .build())
    """

    def __init__(self) -> None:
        """Initialize an empty criteria builder."""
        self._conditions: List[Dict[str, Any]] = []
        self._current_field: Optional[str] = None
        self._current_operator: Optional[str] = None
        self._current_value: Any = None

    def field(self, field_name: str) -> CriteriaBuilder:
        """
        Start a new condition for a specific field.

        Args:
            field_name: The name of the field to filter on

        Returns:
            Self for method chaining

        Example:
            builder.field("Name").equals("John")
        """
        self._current_field = field_name
        self._current_operator = None
        self._current_value = None
        return self

    def equals(self, value: Any) -> CriteriaBuilder:
        """
        Add an equals condition for the current field.

        Args:
            value: The value to match

        Returns:
            Self for method chaining

        Example:
            builder.field("Name").equals("John")
        """
        self._current_operator = "equals"
        self._current_value = value
        return self._add_condition()

    def not_equals(self, value: Any) -> CriteriaBuilder:
        """
        Add a not equals condition for the current field.

        Args:
            value: The value to exclude

        Returns:
            Self for method chaining

        Example:
            builder.field("Status").not_equals("Deleted")
        """
        self._current_operator = "not_equals"
        self._current_value = value
        return self._add_condition()

    def contains(self, value: str) -> CriteriaBuilder:
        """
        Add a contains condition for the current field.

        Args:
            value: The substring to search for

        Returns:
            Self for method chaining

        Example:
            builder.field("Description").contains("urgent")
        """
        self._current_operator = "contains"
        self._current_value = value
        return self._add_condition()

    def not_contains(self, value: str) -> CriteriaBuilder:
        """
        Add a not contains condition for the current field.

        Args:
            value: The substring to exclude

        Returns:
            Self for method chaining

        Example:
            builder.field("Description").not_contains("spam")
        """
        self._current_operator = "not_contains"
        self._current_value = value
        return self._add_condition()

    def starts_with(self, value: str) -> CriteriaBuilder:
        """
        Add a starts with condition for the current field.

        Args:
            value: The prefix to match

        Returns:
            Self for method chaining

        Example:
            builder.field("Email").starts_with("john@")
        """
        self._current_operator = "starts_with"
        self._current_value = value
        return self._add_condition()

    def ends_with(self, value: str) -> CriteriaBuilder:
        """
        Add an ends with condition for the current field.

        Args:
            value: The suffix to match

        Returns:
            Self for method chaining

        Example:
            builder.field("Email").ends_with("@company.com")
        """
        self._current_operator = "ends_with"
        self._current_value = value
        return self._add_condition()

    def greater_than(self, value: Union[int, float, str]) -> CriteriaBuilder:
        """
        Add a greater than condition for the current field.

        Args:
            value: The value to compare against

        Returns:
            Self for method chaining

        Example:
            builder.field("Age").greater_than(18)
        """
        self._current_operator = "greater_than"
        self._current_value = value
        return self._add_condition()

    def greater_than_or_equal(self, value: Union[int, float, str]) -> CriteriaBuilder:
        """
        Add a greater than or equal condition for the current field.

        Args:
            value: The value to compare against

        Returns:
            Self for method chaining

        Example:
            builder.field("Score").greater_than_or_equal(80)
        """
        self._current_operator = "greater_than_or_equal"
        self._current_value = value
        return self._add_condition()

    def less_than(self, value: Union[int, float, str]) -> CriteriaBuilder:
        """
        Add a less than condition for the current field.

        Args:
            value: The value to compare against

        Returns:
            Self for method chaining

        Example:
            builder.field("Age").less_than(65)
        """
        self._current_operator = "less_than"
        self._current_value = value
        return self._add_condition()

    def less_than_or_equal(self, value: Union[int, float, str]) -> CriteriaBuilder:
        """
        Add a less than or equal condition for the current field.

        Args:
            value: The value to compare against

        Returns:
            Self for method chaining

        Example:
            builder.field("Score").less_than_or_equal(100)
        """
        self._current_operator = "less_than_or_equal"
        self._current_value = value
        return self._add_condition()

    def between(self, start_value: Any, end_value: Any) -> CriteriaBuilder:
        """
        Add a between condition for the current field.

        Args:
            start_value: The start of the range (inclusive)
            end_value: The end of the range (inclusive)

        Returns:
            Self for method chaining

        Example:
            builder.field("Created_Time").between("2024-01-01", "2024-12-31")
        """
        self._current_operator = "between"
        self._current_value = [start_value, end_value]
        return self._add_condition()

    def in_list(self, values: List[Any]) -> CriteriaBuilder:
        """
        Add an in list condition for the current field.

        Args:
            values: List of values to match against

        Returns:
            Self for method chaining

        Example:
            builder.field("Status").in_list(["Active", "Pending", "Review"])
        """
        self._current_operator = "in_list"
        self._current_value = values
        return self._add_condition()

    def not_in_list(self, values: List[Any]) -> CriteriaBuilder:
        """
        Add a not in list condition for the current field.

        Args:
            values: List of values to exclude

        Returns:
            Self for method chaining

        Example:
            builder.field("Status").not_in_list(["Deleted", "Archived"])
        """
        self._current_operator = "not_in_list"
        self._current_value = values
        return self._add_condition()

    def is_empty(self) -> CriteriaBuilder:
        """
        Add an is empty condition for the current field.

        Returns:
            Self for method chaining

        Example:
            builder.field("Notes").is_empty()
        """
        self._current_operator = "is_empty"
        self._current_value = True
        return self._add_condition()

    def is_not_empty(self) -> CriteriaBuilder:
        """
        Add an is not empty condition for the current field.

        Returns:
            Self for method chaining

        Example:
            builder.field("Notes").is_not_empty()
        """
        self._current_operator = "is_not_empty"
        self._current_value = True
        return self._add_condition()

    def and_field(self, field_name: str) -> CriteriaBuilder:
        """
        Start a new condition with AND logic for a specific field.

        Args:
            field_name: The name of the field to filter on

        Returns:
            Self for method chaining

        Example:
            builder.field("Name").equals("John").and_field("Age").greater_than(25)
        """
        self._conditions.append({"operator": "AND"})
        return self.field(field_name)

    def or_field(self, field_name: str) -> CriteriaBuilder:
        """
        Start a new condition with OR logic for a specific field.

        Args:
            field_name: The name of the field to filter on

        Returns:
            Self for method chaining

        Example:
            builder.field("Name").equals("John").or_field("Name").equals("Jane")
        """
        self._conditions.append({"operator": "OR"})
        return self.field(field_name)

    def _add_condition(self) -> CriteriaBuilder:
        """Add the current condition to the conditions list."""
        if self._current_field is None:
            raise ValueError("Must call field() before adding a condition")

        condition = {
            "field": self._current_field,
            "operator": self._current_operator,
            "value": self._current_value,
        }
        self._conditions.append(condition)

        # Reset current field for next condition
        self._current_field = None
        self._current_operator = None
        self._current_value = None

        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the final criteria dictionary.

        Returns:
            A dictionary representing the criteria that can be used with
            Zoho Creator API

        Raises:
            ValueError: If no conditions have been added
        """
        if not self._conditions:
            raise ValueError("No conditions have been added to the criteria builder")

        # Convert conditions to the format expected by Zoho Creator API
        criteria_dict: Dict[str, Any] = {}

        for condition in self._conditions:
            if condition.get("operator") in ["AND", "OR"]:
                # Simple Dict[str, Any] can't easily represent OR structure
                # We'll just continue and allow multiple conditions via lists
                # For a full tree representation, a different structure is needed
                continue

            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            # Map operator names to what the client expects
            api_operator = operator
            if operator == "in_list":
                api_operator = "in"
            elif operator == "not_in_list":
                api_operator = "not_in"

            # Map operators to Zoho Creator API format
            cond_val = value if api_operator == "equals" else {api_operator: value}

            if field in criteria_dict:
                if not isinstance(criteria_dict[field], list):
                    criteria_dict[field] = [criteria_dict[field]]
                criteria_dict[field].append(cond_val)
            else:
                criteria_dict[field] = cond_val

        return criteria_dict

    def to_criteria_string(self) -> str:
        """
        Convert the criteria to a string format for backward compatibility.

        Returns:
            A string representation of the criteria in Zoho Creator format
        """
        if not self._conditions:
            raise ValueError("No conditions have been added to the criteria builder")

        def quote(v: Any) -> str:
            if isinstance(v, str):
                return f'"{v}"'
            return str(v)

        conditions = []
        for condition in self._conditions:
            if condition.get("operator") == "AND":
                conditions.append("&&")
                continue
            if condition.get("operator") == "OR":
                conditions.append("||")
                continue

            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            # Convert to string format
            if operator == "equals":
                conditions.append(f"({field} == {quote(value)})")
            elif operator == "not_equals":
                conditions.append(f"({field} != {quote(value)})")
            elif operator == "greater_than":
                conditions.append(f"({field} > {quote(value)})")
            elif operator == "greater_than_or_equal":
                conditions.append(f"({field} >= {quote(value)})")
            elif operator == "less_than":
                conditions.append(f"({field} < {quote(value)})")
            elif operator == "less_than_or_equal":
                conditions.append(f"({field} <= {quote(value)})")
            elif operator == "between":
                conditions.append(
                    f"({field} between {quote(value[0])} and {quote(value[1])})"
                )
            elif operator == "contains":
                conditions.append(f'({field}.contains("{value}"))')
            elif operator == "not_contains":
                conditions.append(f'(!({field}.contains("{value}")))')
            elif operator == "starts_with":
                conditions.append(f'({field}.startsWith("{value}"))')
            elif operator == "ends_with":
                conditions.append(f'({field}.endsWith("{value}"))')
            elif operator == "in_list":
                vals = ",".join(quote(v) for v in value)
                conditions.append(f"({field} in {{{vals}}})")
            elif operator == "not_in_list":
                vals = ",".join(quote(v) for v in value)
                conditions.append(f"({field} not in {{{vals}}})")
            elif operator == "is_empty":
                conditions.append(f'({field} == "")')
            elif operator == "is_not_empty":
                conditions.append(f'({field} != "")')

        return " ".join(conditions)


def create_criteria(**field_conditions: Any) -> Dict[str, Any]:
    """
    Create a simple criteria dictionary from keyword arguments.

    This is a convenience function for creating basic criteria without using
    the fluent CriteriaBuilder interface.

    Args:
        **field_conditions: Field names and their values for equality matching

    Returns:
        A criteria dictionary

    Example:
        criteria = create_criteria(Name="John", Status="Active")
        # Results in: {"Name": "John", "Status": "Active"}
    """
    return field_conditions


def create_complex_criteria(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a criteria dictionary from a list of condition dictionaries.

    Args:
        conditions: List of condition dictionaries with 'field', 'operator',
                    and 'value' keys

    Returns:
        A criteria dictionary

    Example:
        conditions = [
            {"field": "Name", "operator": "equals", "value": "John"},
            {"field": "Age", "operator": "greater_than", "value": 25}
        ]
        criteria = create_complex_criteria(conditions)
    """
    criteria: Dict[str, Any] = {}

    for condition in conditions:
        field = condition["field"]
        operator = condition.get("operator", "equals")
        value = condition["value"]

        if operator == "equals":
            criteria[field] = value
        else:
            criteria[field] = {operator: value}

    return criteria
