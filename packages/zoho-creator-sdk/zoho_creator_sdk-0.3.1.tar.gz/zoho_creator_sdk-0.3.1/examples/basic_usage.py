#!/usr/bin/env python3
"""
Basic usage example for the Zoho Creator SDK.

This example demonstrates the new "zero-config" initialization and how to use
the fluent interface to fetch records from a report.

Tested with modern Python versions (3.8.1+), matching the SDK's minimum
supported version.
"""

from zoho_creator_sdk import ZohoCreatorClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
)


def main() -> None:
    """
    Demonstrates initializing the client and fetching records using the new
    fluent interface.

    The client now uses "zero-config" initialization - configuration is loaded
    automatically from environment variables. No parameters needed!
    """
    # Initialize client with zero-config - no parameters needed!
    # Configuration is loaded automatically from environment variables
    client = ZohoCreatorClient()

    # Example: Fetch records using the fluent interface
    # This demonstrates the chained-method approach:
    # client.application(app_link_name, owner_name)
    #     .report(report_link_name)
    #     .get_records()
    try:
        # Get records from a specific report using fluent interface
        # Replace these placeholder values with your actual Zoho Creator data:
        # - "my-app": Your application link name
        # - "owner-name": Your Zoho Creator username/email
        # - "my-report": Your report link name
        records = (
            client.application("my-app", "owner-name").report("my-report").get_records()
        )

        print("Found records:")

        # The get_records() method now returns a generator that handles
        # pagination automatically
        record_count = 0
        for record in records:
            print(f"  - Record ID: {record.id}, Data: {record.get_form_data()}")
            record_count += 1

        if record_count == 0:
            print(" No records found.")

    except (APIError, AuthenticationError, NetworkError, ConfigurationError) as e:
        print(f"Error fetching records: {e}")
        if isinstance(e, AuthenticationError):
            print("  Tip: Check your ZOHO_CREATOR_CLIENT_ID,")
            print("        ZOHO_CREATOR_CLIENT_SECRET, and")
            print("        ZOHO_CREATOR_REFRESH_TOKEN environment variables.")
        elif isinstance(e, APIError):
            print("  Tip: Verify that the application name,")
            print("        owner name, and report name are correct.")

    # Example: List all applications (requires owner_name parameter)
    try:
        # Note: get_applications() requires the owner_name parameter
        owner_name = "your-owner-name"  # Replace with actual owner name
        applications = client.get_applications(owner_name)
        print(f"\nFound {len(applications)} applications:")
        for app in applications:
            print(f"  - {app.application_name} (link: {app.link_name})")
    except (APIError, AuthenticationError, NetworkError, ConfigurationError) as e:
        print(f"Error fetching applications: {e}")

    # Example: Working with forms using the fluent interface
    try:
        # Add a new record to a form using fluent interface
        new_record_data = {"field1": "value1", "field2": "value2"}
        result = (
            client.application("my-app", "owner-name")
            .form("my-form")
            .add_record(data=new_record_data)
        )
        print(f"\nAdded new record: {result}")
    except (APIError, AuthenticationError, NetworkError, ConfigurationError) as e:
        print(f"Error adding record: {e}")


if __name__ == "__main__":
    main()
