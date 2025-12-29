#!/usr/bin/env python3
"""
OAuth2 authentication example for the Zoho Creator SDK.

This example demonstrates how OAuth2 authentication works with the new
zero-config initialization system. OAuth2 credentials are now loaded
automatically from environment variables.
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
    Demonstrates OAuth2 authentication with the new SDK design.

    Key improvements:
    - Zero-config initialization (no auth handler needed)
    - OAuth2 credentials loaded automatically from environment variables
    - Automatic token refresh handling
    - Fluent interface support
    """
    print("--- OAuth2 Authentication with Zero-Config ---")
    print("The client now uses zero-config initialization:")
    print("  client = ZohoCreatorClient()  # No parameters needed!")

    print(
        "\nOAuth2 credentials are loaded automatically from these"
        " environment variables:"
    )
    print("  export ZOHO_CREATOR_CLIENT_ID='your_client_id'")
    print("  export ZOHO_CREATOR_CLIENT_SECRET='your_client_secret'")
    print("  export ZOHO_CREATOR_REFRESH_TOKEN='your_refresh_token'")

    try:
        # Zero-config initialization - OAuth2 credentials loaded automatically!
        client = ZohoCreatorClient()
        print("✓ Client initialized successfully with OAuth2 authentication!")
        print("  OAuth2 credentials loaded from environment variables")
        print("  Token refresh handled automatically")

        # Example: Get all applications using the new fluent interface approach
        print("\n--- Fetching Applications ---")
        # Note: get_applications() requires owner_name parameter
        owner_name = "your-owner-name"  # Replace with actual owner name
        applications = client.get_applications(owner_name)
        print(f"Found {len(applications)} applications:")
        for app in applications:
            print(f"  - {app.name} ({app.link_name})")

        # Example: Using fluent interface with OAuth2
        print("\n--- Using Fluent Interface with OAuth2 ---")
        print("OAuth2 authentication works seamlessly with the fluent interface:")
        print("  client.application('app').report('report').get_records()")

        # Note: Actual API calls would require valid OAuth2 credentials
        # This example shows the structure but won't execute without valid tokens

    except (AuthenticationError, ConfigurationError, APIError, NetworkError) as e:
        print(f"✗ Error with OAuth2 authentication: {e}")
        print("\nTroubleshooting OAuth2 issues:")
        print("  1. Ensure all required environment variables are set")
        print("  2. Verify OAuth2 credentials are valid")
        print("  3. Check that redirect URI matches your OAuth2 app configuration")
        print("  4. Ensure refresh token is valid and not expired")

    # Example: Configuration file approach for OAuth2
    print("\n--- OAuth2 Configuration File ---")
    print("You can also use a configuration file for OAuth2 credentials:")
    print(
        """
# .zoho_config.json
{
    "auth": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "redirect_uri": "your_redirect_uri",
        "refresh_token": "your_refresh_token"
    },
    "api": {
        "timeout": 60
    }
}
    """.strip()
    )

    try:
        # Configuration will be loaded automatically from file
        ZohoCreatorClient()
        print("✓ Client can also load OAuth2 config from configuration file")
    except (ConfigurationError, AuthenticationError) as e:
        print(f"ℹ Configuration file not found or invalid: {e}")
        print("  This is normal if no config file exists")

    print("\n--- OAuth2 Best Practices ---")
    print("✓ Use zero-config initialization: ZohoCreatorClient()")
    print("✓ Set OAuth2 credentials via environment variables")
    print("✓ Use configuration files for development environments")
    print("✓ Token refresh is handled automatically")
    print("✓ Same fluent interface works with OAuth2 authentication")
    print("✓ No need to manually create OAuth2AuthHandler")


if __name__ == "__main__":
    main()
