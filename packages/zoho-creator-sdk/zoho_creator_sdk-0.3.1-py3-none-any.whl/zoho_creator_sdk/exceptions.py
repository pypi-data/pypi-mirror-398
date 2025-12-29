"""
Custom exception classes for the Zoho Creator SDK.
"""

from typing import Optional


class ZohoCreatorError(Exception):
    """Base exception for all Zoho Creator SDK errors."""

    def __init__(self, message: str, error_code: Optional[int] = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(ZohoCreatorError):
    """Raised when authentication fails."""


class TokenExpiredError(AuthenticationError):
    """Raised when access token has expired."""


class TokenRefreshError(AuthenticationError):
    """Raised when the OAuth2 token refresh fails."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        is_recoverable: bool = True,
    ) -> None:
        super().__init__(message, error_code)
        self.is_recoverable = is_recoverable

    @classmethod
    def non_recoverable(
        cls, message: str, error_code: Optional[int] = None
    ) -> "TokenRefreshError":
        """Create a non-recoverable TokenRefreshError for permanent auth failures."""
        return cls(message, error_code, is_recoverable=False)


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are invalid."""


class APIError(ZohoCreatorError):
    """Base exception for API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[int] = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message, error_code)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""


class ResourceNotFoundError(APIError):
    """Raised when requested resource is not found."""


class BadRequestError(APIError):
    """Raised when API request is malformed."""


class ServerError(APIError):
    """Raised when server returns 5xx errors."""


class ZohoPermissionError(APIError):
    """Raised when access is forbidden (403 errors)."""


class ValidationError(APIError):
    """Raised when request data validation fails."""


class ZohoTimeoutError(APIError):
    """Raised when request times out."""


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""


class ConfigurationError(ZohoCreatorError):
    """Raised when configuration is invalid or missing."""


class NetworkError(ZohoCreatorError):
    """Raised when network connectivity issues occur."""
