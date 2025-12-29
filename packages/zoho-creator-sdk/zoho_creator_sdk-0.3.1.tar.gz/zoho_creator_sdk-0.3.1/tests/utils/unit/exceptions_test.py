"""Unit tests for :mod:`zoho_creator_sdk.exceptions`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk import exceptions


class TestZohoCreatorError:
    """Test cases for ZohoCreatorError base class."""

    def test_zoho_creator_error_captures_message_and_code(self) -> None:
        """ZohoCreatorError stores message and error_code correctly."""
        err = exceptions.ZohoCreatorError("boom", error_code=99)

        assert err.message == "boom"
        assert err.error_code == 99
        assert isinstance(err, Exception)

    def test_zoho_creator_error_without_error_code(self) -> None:
        """ZohoCreatorError works without error_code."""
        err = exceptions.ZohoCreatorError("simple error")

        assert err.message == "simple error"
        assert err.error_code is None
        assert str(err) == "simple error"

    def test_zoho_creator_error_inheritance(self) -> None:
        """ZohoCreatorError inherits from Exception."""
        assert issubclass(exceptions.ZohoCreatorError, Exception)

    def test_zoho_creator_error_str_representation(self) -> None:
        """String representation returns the message."""
        err = exceptions.ZohoCreatorError("test message")
        assert str(err) == "test message"


class TestAPIError:
    """Test cases for APIError class."""

    def test_api_error_includes_status_code(self) -> None:
        """APIError stores status_code correctly."""
        err = exceptions.APIError("bad", status_code=500, error_code=123)

        assert err.status_code == 500
        assert err.error_code == 123
        assert str(err) == "bad"

    def test_api_error_without_status_code(self) -> None:
        """APIError works without status_code."""
        err = exceptions.APIError("api error", error_code=456)

        assert err.status_code is None
        assert err.error_code == 456

    def test_api_error_inheritance(self) -> None:
        """APIError inherits from ZohoCreatorError."""
        assert issubclass(exceptions.APIError, exceptions.ZohoCreatorError)


class TestTokenRefreshError:
    """Test cases for TokenRefreshError class."""

    def test_token_refresh_error_recoverable_flag(self) -> None:
        """TokenRefreshError has correct default recoverable flag."""
        err = exceptions.TokenRefreshError("retry")

        assert err.is_recoverable is True

    def test_token_refresh_error_non_recoverable_classmethod(self) -> None:
        """non_recoverable classmethod creates non-recoverable error."""
        non_rec = exceptions.TokenRefreshError.non_recoverable("stop", error_code=10)
        assert isinstance(non_rec, exceptions.TokenRefreshError)
        assert non_rec.is_recoverable is False
        assert non_rec.error_code == 10

    def test_token_refresh_error_non_recoverable_without_error_code(self) -> None:
        """non_recoverable works without error_code."""
        non_rec = exceptions.TokenRefreshError.non_recoverable("stop")
        assert non_rec.is_recoverable is False
        assert non_rec.error_code is None

    def test_token_refresh_error_inheritance(self) -> None:
        """TokenRefreshError inherits from AuthenticationError."""
        assert issubclass(exceptions.TokenRefreshError, exceptions.AuthenticationError)
        assert issubclass(exceptions.TokenRefreshError, exceptions.ZohoCreatorError)


class TestAuthenticationErrors:
    """Test cases for authentication-related exceptions."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            exceptions.AuthenticationError,
            exceptions.TokenExpiredError,
            exceptions.InvalidCredentialsError,
        ],
    )
    def test_authentication_error_hierarchy(
        self, exc_cls: type[exceptions.ZohoCreatorError]
    ) -> None:
        """Authentication errors inherit from ZohoCreatorError."""
        err = exc_cls("auth issue")

        assert isinstance(err, exceptions.ZohoCreatorError)
        assert err.message == "auth issue"
        assert issubclass(exc_cls, exceptions.ZohoCreatorError)

    def test_authentication_error_inheritance_chain(self) -> None:
        """AuthenticationError is base for other auth errors."""
        assert issubclass(exceptions.TokenExpiredError, exceptions.AuthenticationError)
        assert issubclass(
            exceptions.InvalidCredentialsError, exceptions.AuthenticationError
        )
        assert issubclass(exceptions.TokenRefreshError, exceptions.AuthenticationError)


class TestAPIErrorSubclasses:
    """Test cases for API error subclasses."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            exceptions.RateLimitError,
            exceptions.ResourceNotFoundError,
            exceptions.BadRequestError,
            exceptions.ServerError,
            exceptions.ZohoPermissionError,
            exceptions.ValidationError,
            exceptions.ZohoTimeoutError,
            exceptions.QuotaExceededError,
        ],
    )
    def test_api_error_subclass_hierarchy(
        self, exc_cls: type[exceptions.ZohoCreatorError]
    ) -> None:
        """API error subclasses inherit from APIError."""
        err = exc_cls("api issue")

        assert isinstance(err, exceptions.APIError)
        assert isinstance(err, exceptions.ZohoCreatorError)
        assert err.message == "api issue"
        assert issubclass(exc_cls, exceptions.APIError)

    def test_api_error_subclass_with_status_code(self) -> None:
        """API error subclasses can have status codes."""
        err = exceptions.RateLimitError("too many requests", status_code=429)
        assert err.status_code == 429
        assert isinstance(err, exceptions.APIError)


class TestOtherExceptions:
    """Test cases for other exception classes."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            exceptions.ConfigurationError,
            exceptions.NetworkError,
        ],
    )
    def test_other_exception_hierarchy(
        self, exc_cls: type[exceptions.ZohoCreatorError]
    ) -> None:
        """Other exceptions inherit from ZohoCreatorError."""
        err = exc_cls("other issue")

        assert isinstance(err, exceptions.ZohoCreatorError)
        assert err.message == "other issue"
        assert issubclass(exc_cls, exceptions.ZohoCreatorError)

    def test_configuration_error_with_error_code(self) -> None:
        """ConfigurationError can have error codes."""
        err = exceptions.ConfigurationError("config missing", error_code=1001)
        assert err.error_code == 1001

    def test_network_error_with_error_code(self) -> None:
        """NetworkError can have error codes."""
        err = exceptions.NetworkError("connection failed", error_code=1002)
        assert err.error_code == 1002


class TestExceptionMessageHandling:
    """Test cases for exception message handling."""

    def test_empty_message(self) -> None:
        """Exceptions handle empty messages."""
        err = exceptions.ZohoCreatorError("")
        assert err.message == ""
        assert str(err) == ""

    def test_none_message_handling(self) -> None:
        """Exceptions handle None messages gracefully."""
        # This should work if the constructor allows it
        try:
            err = exceptions.ZohoCreatorError(None)  # type: ignore[arg-type]
            assert err.message is None
        except (TypeError, AttributeError):
            # If None is not allowed, that's also acceptable
            pass

    def test_long_message(self) -> None:
        """Exceptions handle long messages."""
        long_msg = "x" * 1000
        err = exceptions.ZohoCreatorError(long_msg)
        assert err.message == long_msg
        assert str(err) == long_msg


class TestExceptionChaining:
    """Test cases for exception chaining."""

    def test_exception_with_cause(self) -> None:
        """Exceptions can be chained with causes."""
        original_error = ValueError("original")

        try:
            raise exceptions.APIError("wrapped") from original_error
        except exceptions.APIError as api_error:
            assert api_error.__cause__ is original_error
            assert isinstance(api_error, exceptions.APIError)

    def test_exception_with_context(self) -> None:
        """Exceptions can have context."""
        try:
            raise ValueError("context")
        except ValueError as context:
            api_error = exceptions.APIError("wrapped")
            api_error.__context__ = context

            assert api_error.__context__ is context
