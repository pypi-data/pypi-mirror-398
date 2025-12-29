"""Unit tests for :mod:`zoho_creator_sdk.constants`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.constants import Datacenter


class TestDatacenter:
    """Test cases for Datacenter enum."""

    @pytest.mark.parametrize(
        "datacenter, api_url, accounts_url",
        [
            (Datacenter.US, "https://www.zohoapis.com", "https://accounts.zoho.com"),
            (Datacenter.EU, "https://www.zohoapis.eu", "https://accounts.zoho.eu"),
            (Datacenter.IN, "https://www.zohoapis.in", "https://accounts.zoho.in"),
            (Datacenter.AU, "https://www.zohoapis.com.au", "https://accounts.zoho.au"),
            (Datacenter.CA, "https://www.zohoapis.ca", "https://accounts.zoho.ca"),
        ],
    )
    def test_datacenter_urls(
        self,
        datacenter: Datacenter,
        api_url: str,
        accounts_url: str,
    ) -> None:
        """Each datacenter exposes the expected service URLs."""
        assert datacenter.api_url == api_url
        assert datacenter.accounts_url == accounts_url

    def test_datacenter_enum_values(self) -> None:
        """Datacenter enum has correct values."""
        assert Datacenter.US.value == (
            "https://www.zohoapis.com",
            "https://accounts.zoho.com",
        )
        assert Datacenter.EU.value == (
            "https://www.zohoapis.eu",
            "https://accounts.zoho.eu",
        )
        assert Datacenter.IN.value == (
            "https://www.zohoapis.in",
            "https://accounts.zoho.in",
        )
        assert Datacenter.AU.value == (
            "https://www.zohoapis.com.au",
            "https://accounts.zoho.au",
        )
        assert Datacenter.CA.value == (
            "https://www.zohoapis.ca",
            "https://accounts.zoho.ca",
        )

    @pytest.mark.parametrize("datacenter", Datacenter)
    def test_datacenter_api_url_property(self, datacenter: Datacenter) -> None:
        """api_url property returns first element of value tuple."""
        assert datacenter.api_url == datacenter.value[0]

    @pytest.mark.parametrize("datacenter", Datacenter)
    def test_datacenter_accounts_url_property(self, datacenter: Datacenter) -> None:
        """accounts_url property returns second element of value tuple."""
        assert datacenter.accounts_url == datacenter.value[1]

    def test_datacenter_iteration(self) -> None:
        """Datacenter enum can be iterated."""
        datacenters = list(Datacenter)
        assert len(datacenters) == 5
        assert Datacenter.US in datacenters
        assert Datacenter.EU in datacenters
        assert Datacenter.IN in datacenters
        assert Datacenter.AU in datacenters
        assert Datacenter.CA in datacenters

    def test_datacenter_string_representation(self) -> None:
        """Datacenter enum has proper string representation."""
        assert str(Datacenter.US) == "Datacenter.US"
        assert repr(Datacenter.US) == (
            "<Datacenter.US: ('https://www.zohoapis.com', "
            "'https://accounts.zoho.com')>"
        )

    def test_datacenter_comparison(self) -> None:
        """Datacenter enum values can be compared."""
        assert Datacenter.US == Datacenter.US
        assert Datacenter.US != Datacenter.EU
        assert Datacenter.US is not None

    def test_datacenter_hashable(self) -> None:
        """Datacenter enum values are hashable."""
        datacenter_set = {Datacenter.US, Datacenter.EU, Datacenter.US}
        assert len(datacenter_set) == 2  # US appears only once

    def test_datacenter_name_property(self) -> None:
        """Datacenter enum has correct name property."""
        assert Datacenter.US.name == "US"
        assert Datacenter.EU.name == "EU"
        assert Datacenter.IN.name == "IN"
        assert Datacenter.AU.name == "AU"
        assert Datacenter.CA.name == "CA"

    @pytest.mark.parametrize("url_part", ["www.zohoapis", "accounts.zoho"])
    def test_url_patterns(self, url_part: str) -> None:
        """All URLs follow expected patterns."""
        for datacenter in Datacenter:
            api_url = datacenter.api_url
            accounts_url = datacenter.accounts_url

            assert "https://" in api_url
            assert "https://" in accounts_url
            assert url_part in api_url or url_part in accounts_url

    def test_datacenter_value_structure(self) -> None:
        """Each datacenter value is a tuple with exactly 2 elements."""
        for datacenter in Datacenter:
            value = datacenter.value
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert all(isinstance(url, str) for url in value)
            assert all(url.startswith("https://") for url in value)
