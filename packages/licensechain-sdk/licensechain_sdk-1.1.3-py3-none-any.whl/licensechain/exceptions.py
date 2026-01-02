"""
LicenseChain Python SDK Exceptions

Custom exceptions for the LicenseChain Python SDK.
"""


class LicenseChainException(Exception):
    """Base exception for all LicenseChain errors."""

    def __init__(self, message: str = "LicenseChain error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message


class AuthenticationError(LicenseChainException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ValidationError(LicenseChainException):
    """Exception raised when request validation fails."""

    def __init__(self, message: str = "Validation failed", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class NotFoundError(LicenseChainException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class RateLimitError(LicenseChainException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ServerError(LicenseChainException):
    """Exception raised when server returns an error."""

    def __init__(self, message: str = "Server error", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class NetworkError(LicenseChainException):
    """Exception raised when network operations fail."""

    def __init__(self, message: str = "Network error", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
