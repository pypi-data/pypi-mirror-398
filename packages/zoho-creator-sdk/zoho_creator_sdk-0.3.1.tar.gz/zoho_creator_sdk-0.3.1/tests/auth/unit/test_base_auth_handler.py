"""Unit tests for :class:`zoho_creator_sdk.auth.BaseAuthHandler`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.auth import BaseAuthHandler


class TestBaseAuthHandler:
    """Test cases for BaseAuthHandler abstract class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """BaseAuthHandler cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseAuthHandler()  # type: ignore[abstract]

        assert "Can't instantiate abstract class" in str(exc_info.value)
        assert "get_auth_headers" in str(exc_info.value)
        assert "refresh_auth" in str(exc_info.value)

    def test_abstract_methods_raise_not_implemented(self) -> None:
        """Abstract methods raise NotImplementedError when called on subclass."""

        class ConcreteAuthHandler(BaseAuthHandler):
            """Concrete implementation for testing abstract methods."""

            pass

        handler = ConcreteAuthHandler()

        with pytest.raises(NotImplementedError) as exc_info:
            handler.get_auth_headers()

        assert "get_auth_headers" in str(exc_info.value)

        with pytest.raises(NotImplementedError) as exc_info:
            handler.refresh_auth()

        assert "refresh_auth" in str(exc_info.value)

    def test_concrete_implementation_works(self) -> None:
        """Concrete implementation of abstract methods works correctly."""

        class ConcreteAuthHandler(BaseAuthHandler):
            """Concrete implementation for testing."""

            def get_auth_headers(self) -> dict[str, str]:
                return {"Authorization": "Bearer token"}

            def refresh_auth(self) -> None:
                pass

        handler = ConcreteAuthHandler()

        # Should not raise any exceptions
        headers = handler.get_auth_headers()
        assert headers == {"Authorization": "Bearer token"}

        # Should not raise any exceptions
        handler.refresh_auth()

    def test_abstract_method_signatures(self) -> None:
        """Abstract methods have correct signatures."""
        import inspect

        # Check get_auth_headers signature
        get_auth_headers_sig = inspect.signature(BaseAuthHandler.get_auth_headers)
        assert list(get_auth_headers_sig.parameters.keys()) == ["self"]
        assert get_auth_headers_sig.return_annotation == "Mapping[str, str]"

        # Check refresh_auth signature
        refresh_auth_sig = inspect.signature(BaseAuthHandler.refresh_auth)
        assert list(refresh_auth_sig.parameters.keys()) == ["self"]
        assert refresh_auth_sig.return_annotation is None
