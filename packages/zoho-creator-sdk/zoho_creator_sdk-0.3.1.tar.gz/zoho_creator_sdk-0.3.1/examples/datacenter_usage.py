#!/usr/bin/env python3
"""
Datacenter usage example for the Zoho Creator SDK.

This example demonstrates how to configure and use different Zoho datacenters
with the new zero-config initialization approach.
"""

from zoho_creator_sdk import ZohoCreatorClient
from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
)


def main() -> None:
    """
    Demonstrates datacenter configuration with the new SDK design.

    Key improvements:
    - Zero-config initialization (no auth handler needed)
    - Automatic datacenter configuration from environment variables
    - Support for multiple Zoho datacenters (US, EU, IN, AU, CA)
    """
    print("--- Datacenter Configuration ---")
    print("The SDK supports multiple Zoho datacenters:")
    print("  - US: https://www.zohoapis.com (default)")
    print(" - EU: https://www.zohoapis.eu")
    print("  - IN: https://www.zohoapis.in")
    print("  - AU: https://www.zohoapis.com.au")
    print(" - CA: https://www.zohoapis.ca")

    print("\nTo configure datacenter, set the environment variable:")
    print("  export ZOHO_CREATOR_DATACENTER='US'  # or EU, IN, AU, CA")

    # Example: Using default datacenter (US)
    print("\n--- Using Default Datacenter (US) ---")
    try:
        client = ZohoCreatorClient()
        print("✓ Client initialized with default datacenter (US)")

        # Display the configured datacenter
        api_config = client.api_config
        # Access datacenter name with error handling for static analysis tools
        try:
            datacenter_name = api_config.datacenter.name
        except AttributeError:
            # Fallback in case of static analysis issues
            datacenter_name = str(api_config.datacenter)
        print(f"  Configured datacenter: {datacenter_name}")
        print(f"  Base URL: {api_config.base_url}")
    except (AuthenticationError, ConfigurationError, NetworkError, APIError) as e:
        print(f"ℹ Could not initialize client: {e}")
        print(" (This is expected if no credentials are configured)")

    # Example: Using EU datacenter
    print("\n--- Using EU Datacenter ---")
    print("To use EU datacenter, set: export ZOHO_CREATOR_DATACENTER='EU'")
    try:
        client = ZohoCreatorClient()
        api_config = client.api_config
        # Access datacenter name with error handling for static analysis tools
        try:
            datacenter_name = api_config.datacenter.name
        except AttributeError:
            # Fallback in case of static analysis issues
            datacenter_name = str(api_config.datacenter)
        print(f"  Configured datacenter: {datacenter_name}")
        print(f"  Base URL: {api_config.base_url}")
    except (AuthenticationError, ConfigurationError, NetworkError, APIError) as e:
        print(f"ℹ Could not initialize client: {e}")

    # Example: Programmatic datacenter information
    print("\n--- Datacenter Information ---")
    for datacenter in Datacenter:
        print(f"  {datacenter.name}: {datacenter.api_url}")

    # Example: Using the client with different datacenters
    print("\n--- Datacenter Usage Example ---")
    try:
        client = ZohoCreatorClient()
        print("Client initialized - will use configured datacenter automatically")

        # When making API calls, the correct datacenter URL will be used automatically
        print("All API calls will automatically use the configured datacenter URL")

    except (AuthenticationError, ConfigurationError, NetworkError, APIError) as e:
        print(f"Error with datacenter configuration: {e}")
        print("\nCommon issues:")
        print("  - Check that ZOHO_CREATOR_DATACENTER is set correctly")
        print("  - Verify that your OAuth2 credentials are valid")
        print("    for the selected datacenter")
        print("  - Ensure your Zoho account is registered in the")
        print("    selected datacenter region")

    print("\n--- Datacenter Best Practices ---")
    print(
        "✓ Set ZOHO_CREATOR_DATACENTER environment variable to match your Zoho account"
    )
    print("✓ Use the same datacenter region as your Zoho account for best performance")
    print("✓ Datacenter configuration loads automatically with zero-config")
    print("  initialization")
    print("✓ All API calls automatically use the correct regional endpoints")
    print("✓ Token refresh URLs are automatically configured based on datacenter")


if __name__ == "__main__":
    main()
