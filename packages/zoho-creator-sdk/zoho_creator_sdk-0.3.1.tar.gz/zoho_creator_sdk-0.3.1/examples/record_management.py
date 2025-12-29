#!/usr/bin/env python3
"""
Record management example for Zoho Creator SDK.

This example demonstrates CRUD operations using the new fluent interface
and zero-config initialization.

Compatible with modern Python versions (3.8.1+), matching the SDK's minimum
supported version.
"""

from zoho_creator_sdk import ZohoCreatorClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    ZohoTimeoutError,
)


def main() -> None:
    """
    Demonstrates CRUD operations with the new fluent interface.

    Key improvements:
    - Zero-config initialization (no auth handler needed)
    - Fluent interface for all operations
    - Automatic pagination handling
    """
    # Initialize client with zero-config - no parameters needed!
    client = ZohoCreatorClient()

    # Replace with your actual application and form names
    app_link_name = "your_app_link_name"
    form_link_name = "your_form_link_name"
    report_link_name = "your_report_link_name"
    owner_name = "your_owner_name"

    # Create a new record using the fluent interface
    try:
        new_record_data = {"field1": "value1", "field2": "value2", "number_field": 42}

        # Use fluent interface: client.application().form().add_record()
        created_record = (
            client.application(app_link_name, owner_name)
            .form(form_link_name)
            .add_record(data=new_record_data)
        )
        print(f"Created record: {created_record}")

        # Extract ID from API response (Mapping[str, Any])
        # The API response has 'data' containing record info
        if isinstance(created_record, dict):
            record_data = created_record.get("data", {})
            # Get ID from data field (lowercase 'id')
            created_record_id = (
                record_data.get("id") if isinstance(record_data, dict) else None
            )
            # If not found in 'data', try directly in response
            if not created_record_id and "id" in created_record:
                created_record_id = created_record.get("id")
        else:
            created_record_id = getattr(created_record, "id", None)
        if created_record_id:
            print(f"Created record with ID: {created_record_id}")
        else:
            print("Could not get created record ID.")
            return

        # Update the record using the client method
        update_data = {"field1": "updated_value"}

        updated_record = client.update_record(
            owner_name=owner_name,
            app_link_name=app_link_name,
            report_link_name=report_link_name,
            record_id=created_record_id,
            data=update_data,
        )
        print(f"Updated record: {updated_record}")

        # Get the specific record using fluent interface
        records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records(criteria=f"ID=={created_record_id}")
        )

        # Convert generator to list to access first record
        record_list = list(records)
        if record_list:
            print(f"Retrieved record: {record_list[0].data}")

        # Get multiple records with criteria using fluent interface
        # Automatic pagination is handled by the generator
        all_records = (
            client.application(app_link_name, owner_name)
            .report(report_link_name)
            .get_records(criteria="field1=='updated_value'")
        )

        # Count matching records (this will iterate through all pages automatically)
        matching_count = sum(1 for _ in all_records)
        print(f"Found {matching_count} matching records")

        # Delete the record using the client method (not fluent interface)
        deleted = client.delete_record(
            owner_name=owner_name,
            app_link_name=app_link_name,
            report_link_name=report_link_name,
            record_id=created_record_id,
        )
        print(f"Record deleted response: {deleted}")

    except (
        APIError,
        AuthenticationError,
        ConfigurationError,
        NetworkError,
        ZohoTimeoutError,
    ) as e:
        print(f"Error in record operations: {e}")
        print("\nCommon issues:")
        print("  - Check that your Zoho Creator credentials are valid")
        print(" - Verify that the app_link_name, form_link_name, and")
        print("    report_link_name are correct")
        print("  - Ensure the owner_name matches your Zoho account")


if __name__ == "__main__":
    main()
