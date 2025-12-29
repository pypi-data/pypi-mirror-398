#!/usr/bin/env python3
"""
Advanced usage example for the Zoho Creator SDK.

This example demonstrates the new fluent interface for batch operations,
complex queries, and showcases the automatic pagination feature.
"""

from typing import Any, Dict, List

from zoho_creator_sdk import ZohoCreatorClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
)
from zoho_creator_sdk.models import FieldConfig


def batch_create_records(
    client: ZohoCreatorClient,
    app_link_name: str,
    form_link_name: str,
    owner_name: str,
    records_data: List[Dict[str, Any]],
) -> List[str]:
    """
    Create multiple records in batch using the fluent interface.

    The new SDK design uses a fluent interface for all operations,
    making the code more readable and concise.
    """
    created_ids = []

    for record_data in records_data:
        try:
            # Use fluent interface: client.application().form().add_record()
            record = (
                client.application(app_link_name, owner_name)
                .form(form_link_name)
                .add_record(data=record_data)
            )
            # Extract ID from API response (Mapping[str, Any])
            # The API response has 'data' containing record info
            if isinstance(record, dict):
                record_data = record.get("data", {})
                # Get ID from data field
                record_id = (
                    record_data.get("id") if isinstance(record_data, dict) else None
                )
                # If not found in 'data', try directly in response
                if not record_id and "id" in record:
                    record_id = record.get("id")
            else:
                record_id = getattr(record, "id", None)
            if record_id:
                created_ids.append(record_id)
                print(f"Successfully created record with ID: {record_id}")
            else:
                print(f"Failed to create record. Response: {record}")
        except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
            print(f"Failed to create record with data {record_data}: {e}")

    return created_ids


def main() -> None:
    """
    Demonstrates advanced usage with the new SDK design.

    Key improvements:
    - Zero-config initialization (no auth handler needed)
    - Fluent interface for all operations
    - Automatic pagination handling
    """
    # Zero-config initialization - configuration loaded automatically!
    client = ZohoCreatorClient()

    # Use actual application and form names
    app_link_name = "your_app_link_name"
    form_link_name = "your_form_link_name"
    report_link_name = "your_report_link_name"
    owner_name = "your_owner_name"

    # Batch create records using fluent interface
    print("--- Testing Batch Record Creation ---")
    records_to_create = [
        {"name": "Record 1", "status": "active"},
        {"name": "Record 2", "status": "pending"},
        {"name": "Record 3", "status": "active"},
    ]
    try:
        created_ids = batch_create_records(
            client, app_link_name, form_link_name, owner_name, records_to_create
        )
        print(
            f"\nBatch creation summary: Created {len(created_ids)} records "
            f"with IDs: {created_ids}"
        )
    except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
        print(f"Error in batch creation: {e}")

    # Complex query with automatic pagination
    print("\n--- Testing Complex Query with Automatic Pagination ---")
    try:
        # Use fluent interface for queries
        # Automatic pagination is now handled by the generator
        records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records(
                criteria="(status==\"active\" && created_time>'2023-01-01 00:00')"
            )
        )

        print("Found active records created after 2023-01-01:")
        print(
            "(Pagination is handled automatically - no need for manual page handling!)"
        )

        # Simple iteration over the generator - pagination happens automatically
        for record in records:
            print(f"  - Record ID: {record.id}, Data: {record.get_form_data()}")

    except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
        print(f"Error in complex query: {e}")

    # Demonstrate automatic pagination with large datasets
    print("\n--- Demonstrating Automatic Pagination ---")
    try:
        # This will automatically handle pagination behind the scenes
        all_records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records()
        )

        # Count total records (this will iterate through all pages automatically)
        total_count = sum(1 for _ in all_records)
        print(f"Total records in report: {total_count}")

        # Get records again (fresh generator since we consumed the previous one)
        records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records()
        )

        # Process first 5 records as an example
        print("First 5 records:")
        for i, record in enumerate(records):
            if i >= 5:
                break
            print(f"  - Record {i+1}: ID={record.id}")

    except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
        print(f"Error demonstrating pagination: {e}")

    # Example: Using different query parameters
    print("\n--- Using Query Parameters ---")
    try:
        # Example with various query parameters
        records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records(
                criteria="status == 'active'",
                sort_field="created_time",
                sort_order="desc",
                max_records=10,
            )
        )

        print("Active records sorted by creation time (descending):")
        for i, record in enumerate(records):
            if i >= 5:  # Limit to first 5 for example
                break
            created_time = record.get_form_data().get("created_time", "N/A")
            print(f"  - Record {i+1}: ID={record.id}, Created: {created_time}")

    except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
        print(f"Error using query parameters: {e}")

    # Example: Using field_config, fields, and record_cursor for integration reports
    print("\n--- Using field_config, fields, and record_cursor ---")
    try:
        # Fetch only specific fields from the detail view layout
        detail_records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records(
                field_config=FieldConfig.DETAIL_VIEW,
                fields=["Email", "Phone"],
                criteria='status == "active"',
            )
        )

        for i, record in enumerate(detail_records):
            if i >= 5:
                break
            print(f"  - Detail record {i+1}: ID={record.id}")

        # For integration form reports that return a record_cursor header, use
        # the dedicated iterator to automatically follow the cursor across
        # pages.
        cursor_records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .iter_records_with_cursor(
                field_config=FieldConfig.ALL,
                fields=["Order_ID", "Total"],
            )
        )

        for i, record in enumerate(cursor_records):
            if i >= 5:
                break
            print(f"  - Cursor record {i+1}: ID={record.id}")

    except (APIError, AuthenticationError, ConfigurationError, NetworkError) as e:
        print(f"Error using field_config/record_cursor: {e}")


if __name__ == "__main__":
    main()
