#!/usr/bin/env python3
"""
Configuration example for the Zoho Creator SDK.

This example demonstrates the new "zero-config" initialization and how
configuration is now loaded automatically from environment variables or
configuration files. Also shows datacenter configuration.
"""

import os

from zoho_creator_sdk import ZohoCreatorClient


def main():
    """
    Demonstrates the new configuration system with zero-config initialization.

    Key improvements:
    - Zero-config initialization (no parameters needed)
    - Automatic configuration loading from environment variables
    - Automatic configuration loading from configuration files
    - Simple datacenter configuration via environment variable
    """
    # Method 1: Zero-config initialization (RECOMMENDED)
    print("--- Zero-Config Initialization ---")
    print("The client now uses zero-config initialization - no parameters needed!")
    print("Configuration is loaded automatically from:")
    print("  1. Environment variables")
    print("  2. Configuration files in standard locations (see below)")

    try:
        # This is the new, simplified way - no auth handler or config needed!
        ZohoCreatorClient()
        print("✓ Client initialized successfully with zero-config!")
        print("  Configuration was loaded automatically from available sources.")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")

    # Method 2: Environment variable configuration
    print("\n--- Environment Variable Configuration ---")
    print("Set these environment variables for configuration:")
    print("  export ZOHO_CREATOR_CLIENT_ID='your_client_id'")
    print("  export ZOHO_CREATOR_CLIENT_SECRET='your_client_secret'")
    print("  export ZOHO_CREATOR_REFRESH_TOKEN='your_refresh_token'")
    print("  export ZOHO_CREATOR_DATACENTER='US'  # or EU, IN, AU, CN, JP")

    client_id_env = os.getenv("ZOHO_CREATOR_CLIENT_ID")
    datacenter_env = os.getenv("ZOHO_CREATOR_DATACENTER", "US")

    if client_id_env:
        try:
            ZohoCreatorClient()
            print(
                "✓ Client configured with OAuth2 credentials from environment variables"
            )
            print(f"  Datacenter: {datacenter_env}")
        except Exception as e:
            print(f"✗ Failed to configure client: {e}")
    else:
        print("ℹ OAuth2 environment variables not set")
        print(
            "  The client will still initialize but API calls will fail"
            " without authentication"
        )

    # Method 3: Configuration file (automatic loading)
    print("\n--- Configuration File (Automatic Loading) ---")
    print("The SDK automatically looks for configuration files:")
    print("  1. zoho_creator_config.json (current directory)")
    print("  2. ~/.zoho_creator/config.json (user home directory)")
    print("  3. /etc/zoho_creator/config.json (system-wide)")

    print("\nExample config.json content:")
    print(
        """
{
    "auth": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "redirect_uri": "your_redirect_uri",
        "refresh_token": "your_refresh_token"
    },
    "api": {
        "timeout": 60,
        "max_retries": 5,
        "retry_delay": 2.0
    },
    "datacenter": "US"
}
    """.strip()
    )

    try:
        # The client will automatically load configuration from files
        ZohoCreatorClient()
        print("✓ Client initialized with configuration from file")
        print("  Configuration files are loaded automatically on initialization")
    except Exception as e:
        print(f"ℹ No configuration file found or error loading: {e}")
        print("  This is normal if no config file exists")

    # Method 4: Multiple configuration sources
    print("\n--- Configuration Source Priority ---")
    print("Configuration is loaded in this order (later sources override earlier):")
    print("  1. Default values")
    print("  2. Configuration files")
    print("  3. Environment variables")
    print("  4. Programmatically passed parameters (if supported in future)")

    print("\nExample: Set ZOHO_CREATOR_DATACENTER to override file configuration")
    print("  export ZOHO_CREATOR_DATACENTER='https://creator.zoho.eu'")

    try:
        ZohoCreatorClient()
        print("✓ Client configured with multiple sources")
        print("  Files + Environment variables merged automatically")
    except Exception as e:
        print(f"✗ Error with multiple configuration sources: {e}")

    print("\n--- Configuration Summary ---")
    print("✓ Zero-config initialization is now the standard approach")
    print("✓ Configuration is loaded automatically from multiple sources")
    print("✓ Environment variables override file configuration")
    print("✓ No need to manually create auth handlers or pass config objects")
    print("✓ Datacenter configuration is simple via ZOHO_CREATOR_DATACENTER")


if __name__ == "__main__":
    main()
