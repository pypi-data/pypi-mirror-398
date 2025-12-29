"""
Datacenter constants for Zoho Creator SDK.
"""

from enum import Enum


class Datacenter(Enum):
    """Enumeration of Zoho Creator datacenters."""

    US = ("https://www.zohoapis.com", "https://accounts.zoho.com")
    EU = ("https://www.zohoapis.eu", "https://accounts.zoho.eu")
    IN = ("https://www.zohoapis.in", "https://accounts.zoho.in")
    AU = ("https://www.zohoapis.com.au", "https://accounts.zoho.au")
    CA = ("https://www.zohoapis.ca", "https://accounts.zoho.ca")

    @property
    def api_url(self) -> str:
        """Get the API URL for this datacenter."""
        return self.value[0]

    @property
    def accounts_url(self) -> str:
        """Get the accounts URL for this datacenter."""
        return self.value[1]
