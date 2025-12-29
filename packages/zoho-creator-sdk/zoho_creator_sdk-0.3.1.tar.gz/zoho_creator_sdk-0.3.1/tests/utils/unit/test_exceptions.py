"""Unit tests for zoho_creator_sdk.exceptions module."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    InvalidCredentialsError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    TokenRefreshError,
    ValidationError,
    ZohoCreatorError,
    ZohoPermissionError,
    ZohoTimeoutError,
)


class TestZohoCreatorError:
    """Test cases for ZohoCreatorError base class."""

    def test_zoho_creator_error_basic(self) -> None:
        """ZohoCreatorError can be created with basic message."""
        error = ZohoCreatorError("Test error message")

        assert str(error) == "Test error message"
        assert repr(error) == "ZohoCreatorError('Test error message')"

    def test_zoho_creator_error_with_error_code(self) -> None:
        """ZohoCreatorError can store error code."""
        error = ZohoCreatorError("Test error", error_code=500)

        assert str(error) == "Test error"
        assert error.error_code == 500
        assert error.message == "Test error"

    def test_zoho_creator_error_inheritance(self) -> None:
        """ZohoCreatorError is subclass of Exception."""
        error = ZohoCreatorError("Test")

        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)


class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_authentication_error_basic(self) -> None:
        """AuthenticationError can be created with message."""
        error = AuthenticationError("Authentication failed")

        assert str(error) == "Authentication failed"
        assert isinstance(error, ZohoCreatorError)

    def test_authentication_error_inheritance(self) -> None:
        """AuthenticationError is subclass of ZohoCreatorError."""
        error = AuthenticationError("Auth failed")

        assert isinstance(error, ZohoCreatorError)
        assert isinstance(error, Exception)


class TestTokenRefreshError:
    """Test cases for TokenRefreshError."""

    def test_token_refresh_error_basic(self) -> None:
        """TokenRefreshError can be created with message."""
        error = TokenRefreshError("Token refresh failed")

        assert str(error) == "Token refresh failed"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, ZohoCreatorError)

    def test_token_refresh_error_with_recoverable_flag(self) -> None:
        """TokenRefreshError can set recoverable flag."""
        error = TokenRefreshError("Failed", is_recoverable=False)

        assert error.is_recoverable is False
        assert isinstance(error, AuthenticationError)

    def test_token_refresh_error_non_recoverable_classmethod(self) -> None:
        """TokenRefreshError.non_recoverable creates non-recoverable error."""
        error = TokenRefreshError.non_recoverable("Permanent failure")

        assert error.is_recoverable is False
        assert str(error) == "Permanent failure"


class TestAPIError:
    """Test cases for APIError."""

    def test_api_error_basic(self) -> None:
        """APIError can be created with message."""
        error = APIError("API call failed")

        assert str(error) == "API call failed"
        assert isinstance(error, ZohoCreatorError)

    def test_api_error_with_status_code(self) -> None:
        """APIError includes HTTP status code."""
        error = APIError("Request failed", status_code=400)

        assert error.status_code == 400
        assert isinstance(error, ZohoCreatorError)

    def test_api_error_with_error_code(self) -> None:
        """APIError includes error code."""
        error = APIError("Request failed", error_code=1001)

        assert error.error_code == 1001
        assert isinstance(error, ZohoCreatorError)


class TestNetworkError:
    """Test cases for NetworkError."""

    def test_network_error_basic(self) -> None:
        """NetworkError can be created with message."""
        error = NetworkError("Connection timeout")

        assert str(error) == "Connection timeout"
        assert isinstance(error, ZohoCreatorError)


class TestServerError:
    """Test cases for ServerError."""

    def test_server_error_basic(self) -> None:
        """ServerError can be created with message."""
        error = ServerError("Internal server error")

        assert str(error) == "Internal server error"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)

    def test_server_error_with_status_code(self) -> None:
        """ServerError includes HTTP status code."""
        error = ServerError("Server error", status_code=500)

        assert error.status_code == 500
        assert isinstance(error, APIError)


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_basic(self) -> None:
        """RateLimitError can be created with message."""
        error = RateLimitError("Rate limit exceeded")

        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestQuotaExceededError:
    """Test cases for QuotaExceededError."""

    def test_quota_exceeded_error_basic(self) -> None:
        """QuotaExceededError can be created with message."""
        error = QuotaExceededError("API quota exceeded")

        assert str(error) == "API quota exceeded"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestBadRequestError:
    """Test cases for BadRequestError."""

    def test_bad_request_error_basic(self) -> None:
        """BadRequestError can be created with message."""
        error = BadRequestError("Invalid request parameters")

        assert str(error) == "Invalid request parameters"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestResourceNotFoundError:
    """Test cases for ResourceNotFoundError."""

    def test_resource_not_found_error_basic(self) -> None:
        """ResourceNotFoundError can be created with message."""
        error = ResourceNotFoundError("Resource not found")

        assert str(error) == "Resource not found"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestZohoPermissionError:
    """Test cases for ZohoPermissionError."""

    def test_zoho_permission_error_basic(self) -> None:
        """ZohoPermissionError can be created with message."""
        error = ZohoPermissionError("Insufficient permissions")

        assert str(error) == "Insufficient permissions"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_basic(self) -> None:
        """ValidationError can be created with message."""
        error = ValidationError("Validation failed")

        assert str(error) == "Validation failed"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestZohoTimeoutError:
    """Test cases for ZohoTimeoutError."""

    def test_zoho_timeout_error_basic(self) -> None:
        """ZohoTimeoutError can be created with message."""
        error = ZohoTimeoutError("Request timeout")

        assert str(error) == "Request timeout"
        assert isinstance(error, APIError)
        assert isinstance(error, ZohoCreatorError)


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_basic(self) -> None:
        """ConfigurationError can be created with message."""
        error = ConfigurationError("Invalid configuration")

        assert str(error) == "Invalid configuration"
        assert isinstance(error, ZohoCreatorError)


class TestInvalidCredentialsError:
    """Test cases for InvalidCredentialsError."""

    def test_invalid_credentials_error_basic(self) -> None:
        """InvalidCredentialsError can be created with message."""
        error = InvalidCredentialsError("Invalid credentials")

        assert str(error) == "Invalid credentials"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, ZohoCreatorError)


class TestExceptionHierarchy:
    """Test cases for exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_zoho_creator_error(self) -> None:
        """All custom exceptions inherit from ZohoCreatorError."""
        exceptions = [
            AuthenticationError,
            TokenRefreshError,
            InvalidCredentialsError,
            APIError,
            NetworkError,
            ServerError,
            RateLimitError,
            QuotaExceededError,
            BadRequestError,
            ResourceNotFoundError,
            ZohoPermissionError,
            ValidationError,
            ZohoTimeoutError,
            ConfigurationError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, ZohoCreatorError)
            assert issubclass(exc_class, Exception)

    def test_api_error_subclasses(self) -> None:
        """API-related exceptions inherit from APIError."""
        api_errors = [
            ServerError,
            RateLimitError,
            QuotaExceededError,
            BadRequestError,
            ResourceNotFoundError,
            ZohoPermissionError,
            ValidationError,
            ZohoTimeoutError,
        ]

        for exc_class in api_errors:
            assert issubclass(exc_class, APIError)

    def test_auth_error_subclasses(self) -> None:
        """Auth-related exceptions inherit from AuthenticationError."""
        auth_errors = [TokenRefreshError, InvalidCredentialsError]

        for exc_class in auth_errors:
            assert issubclass(exc_class, AuthenticationError)

    @pytest.mark.parametrize(
        "exception_class,message",
        [
            (AuthenticationError, "Auth failed"),
            (APIError, "API failed"),
            (NetworkError, "Network failed"),
            (ServerError, "Server failed"),
            (RateLimitError, "Rate limit"),
            (QuotaExceededError, "Quota exceeded"),
            (BadRequestError, "Bad request"),
            (ResourceNotFoundError, "Not found"),
            (ZohoPermissionError, "Permission denied"),
            (ZohoTimeoutError, "Timeout"),
            (ConfigurationError, "Config error"),
            (ValidationError, "Validation error"),
            (InvalidCredentialsError, "Invalid creds"),
            (TokenRefreshError, "Token refresh"),
        ],
    )
    def test_exception_string_representation(
        self, exception_class: type, message: str
    ) -> None:
        """All exceptions have proper string representation."""
        error = exception_class(message)

        assert str(error) == message
        assert message in repr(error)
        assert exception_class.__name__ in repr(error)
