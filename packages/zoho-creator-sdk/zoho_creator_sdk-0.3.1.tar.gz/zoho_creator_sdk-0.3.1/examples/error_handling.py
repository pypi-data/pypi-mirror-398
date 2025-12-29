#!/usr/bin/env python3
"""
Error handling example for the Zoho Creator SDK.

This example demonstrates proper error handling techniques with the new
zero-config initialization and fluent interface design.
"""

from zoho_creator_sdk import ZohoCreatorClient
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    TokenRefreshError,
    ZohoCreatorError,
    ZohoPermissionError,
    ZohoTimeoutError,
)


def main() -> None:
    """
    Demonstrates error handling with the new SDK design.

    Key improvements:
    - Zero-config initialization (no auth handler needed)
    - Configuration loaded automatically from environment variables
    - Same exception handling patterns work with new design
    """
    # Zero-config initialization - configuration loaded automatically!
    # Using invalid configuration to trigger AuthenticationError
    print("--- Testing Error Handling with Zero-Config ---")
    print("The client uses zero-config initialization:")
    print("  client = ZohoCreatorClient()  # No parameters needed!")

    try:
        # This will likely raise an AuthenticationError due to missing/invalid config
        print("\nAttempting to fetch applications with invalid configuration...")
        client = ZohoCreatorClient()
        client.get_applications("owner-name")  # Need owner name parameter
    except AuthenticationError as e:
        print("\n✓ Successfully caught an AuthenticationError:")
        print(f"  Message: {e.message}")
        print(f"  Error Code: {e.error_code}")
        if hasattr(e, "status_code"):
            print(f"  Status Code: {e.status_code}")
    except ResourceNotFoundError as e:
        print("\n✓ Caught a ResourceNotFoundError:")
        print(f"  Message: {e.message}")
    except RateLimitError as e:
        print("\n✓ Caught a RateLimitError:")
        print(f"  Message: {e.message}")
    except APIError as e:
        print("\n✓ Caught a generic APIError:")
        print(f"  Message: {e.message}")
    except ZohoCreatorError as e:
        print("\n✓ Caught a ZohoCreatorError:")
        print(f"  Message: {e.message}")
    except (ConnectionError, TimeoutError, OSError) as e:
        print("\n✓ Caught an unexpected error:")
        print(f"  Error: {e}")

    # Example: Error handling with fluent interface
    print("\n--- Error Handling with Fluent Interface ---")
    try:
        print("Attempting to access non-existent application and report...")
        client = ZohoCreatorClient()
        # This will likely raise a ResourceNotFoundError
        list(
            client.application("non-existent-app", "owner-name")
            .report("non-existent-report")
            .get_records()
        )
    except ResourceNotFoundError as e:
        print("\n✓ Successfully caught ResourceNotFoundError with fluent interface:")
        print(f"  Message: {e.message}")
    except AuthenticationError as e:
        print("\n✓ Caught AuthenticationError (likely due to missing config):")
        print(f"  Message: {e.message}")
    except (ConnectionError, TimeoutError, OSError) as e:
        print("\n✓ Caught other error:")
        print(f"  Error: {e}")

    # Example: Configuration error handling
    print("\n--- Configuration Error Handling ---")
    print("Common configuration issues:")
    print(" 1. Missing ZOHO_CREATOR_CLIENT_ID environment variable")
    print("  2. Missing ZOHO_CREATOR_CLIENT_SECRET environment variable")
    print("  3. Missing ZOHO_CREATOR_REFRESH_TOKEN environment variable")
    print("  4. Missing or invalid configuration file")
    print(" 5. Network connectivity issues")

    try:
        # This will fail if no valid configuration is available
        client = ZohoCreatorClient()
        print("✓ Configuration loaded successfully")
    except ConfigurationError as e:
        print("\n✗ Configuration error:")
        print(f"  {e.message}")
        print(
            "\n  To fix: Set ZOHO_CREATOR_CLIENT_ID, ZOHO_CREATOR_CLIENT_SECRET,"
            " and ZOHO_CREATOR_REFRESH_TOKEN environment variables"
        )
    except (ConnectionError, TimeoutError, OSError) as e:
        print("\n✗ Other configuration error:")
        print(f" {e}")

    # Example: Comprehensive error handling
    print("\n--- Comprehensive Error Handling ---")
    try:
        client = ZohoCreatorClient()
        # Attempt various operations to demonstrate different error types
        applications = client.get_applications("owner-name")
        print(f"Found {len(applications)} applications")
    except TokenRefreshError as e:
        print(f"  - TokenRefreshError: Failed to refresh token - {e.message}")
    except AuthenticationError:
        print(" - AuthenticationError: Invalid or missing credentials")
    except ConfigurationError:
        print(" - ConfigurationError: Missing configuration")
    except NetworkError:
        print("  - NetworkError: Network connectivity issue")
    except ServerError as e:
        print(f"  - ServerError: Server-side error - {e.message}")
    except BadRequestError as e:
        print(f"  - BadRequestError: Invalid request - {e.message}")
    except ZohoPermissionError as e:
        print(f"  - ZohoPermissionError: Insufficient permissions - {e.message}")
    except QuotaExceededError as e:
        print(f"  - QuotaExceededError: API quota exceeded - {e.message}")
    except ZohoTimeoutError as e:
        print(f"  - ZohoTimeoutError: Request timed out - {e.message}")
    except (ConnectionError, TimeoutError, OSError) as e:
        print(f"  - Unexpected error: {e}")

    print("\n--- Error Handling Best Practices ---")
    print("✓ All existing exception types work with the new SDK")
    print("✓ Zero-config initialization doesn't change error handling")
    print("✓ Fluent interface operations throw the same exceptions")
    print("✓ Configuration errors are handled gracefully")
    print("✓ Network and API errors are properly categorized")
    print("✓ Specific exception types allow for targeted error handling")


if __name__ == "__main__":
    main()
