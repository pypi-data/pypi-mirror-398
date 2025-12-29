"""
Example demonstrating the new add_records functionality for bulk adding
records to Zoho Creator forms.
"""

from zoho_creator_sdk import ZohoCreatorClient


def main() -> None:
    """Demonstrate bulk adding records to a Zoho Creator form."""

    # Initialize the client (uses environment variables for configuration)
    client = ZohoCreatorClient()

    # Example data to add
    records = [
        {
            "Name": "John Doe",
            "Email": "john.doe@example.com",
            "Phone": "+1-555-0123",
            "Department": "Engineering",
        },
        {
            "Name": "Jane Smith",
            "Email": "jane.smith@example.com",
            "Phone": "+1-555-0124",
            "Department": "Marketing",
        },
        {
            "Name": "Bob Johnson",
            "Email": "bob.johnson@example.com",
            "Phone": "+1-555-0125",
            "Department": "Sales",
        },
    ]

    try:
        # Add multiple records in a single API call
        # Using the fluent interface: client.application().form().add_records()
        result = (
            client.application(app_link_name="my-app", owner_name="my-owner")
            .form(form_link_name="employee-form")
            .add_records(records)
        )

        print(f"Successfully added {len(result.result)} records!")
        print(f"Response code: {result.code}")
        print(f"Response message: {result.message}")

        # Print details of each added record
        for i, record_result in enumerate(result.result, 1):
            print(f"Record {i}: ID = {record_result.data.get('ID', 'N/A')}")

    except ValueError as e:
        if "Maximum 200 records" in str(e):
            print(f"Error: {e}")
            print(
                "Please split your records into smaller batches (max 200 per request)"
            )
        else:
            print(f"Validation error: {e}")
    except Exception as e:
        print(f"Error adding records: {e}")


def advanced_example() -> None:
    """Demonstrate advanced usage with optional parameters."""

    client = ZohoCreatorClient()

    records = [
        {"Name": "Alice Brown", "Email": "alice@example.com"},
        {"Name": "Charlie Davis", "Email": "charlie@example.com"},
    ]

    try:
        # Add records with advanced options
        result = (
            client.application(app_link_name="my-app", owner_name="my-owner")
            .form(form_link_name="employee-form")
            .add_records(
                records,
                skip_workflow=["form_workflow"],  # Skip form workflows
                fields=["Name", "Email", "ID"],  # Include specific fields in response
                message=False,  # Don't include success message
                tasks=True,  # Include task info (redirect URLs)
            )
        )

        print(f"Advanced bulk add completed with {len(result.result)} records")

    except Exception as e:
        print(f"Error in advanced example: {e}")


if __name__ == "__main__":
    print("=== Basic Bulk Add Records Example ===")
    main()

    print("\n=== Advanced Bulk Add Records Example ===")
    advanced_example()
