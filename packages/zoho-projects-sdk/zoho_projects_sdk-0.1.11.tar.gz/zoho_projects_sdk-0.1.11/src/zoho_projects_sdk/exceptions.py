"""
Custom exceptions for the Zoho Projects SDK.
"""


class ZohoSDKError(Exception):
    """Base exception for all SDK-specific errors."""


class ConfigurationError(ZohoSDKError):
    """Raised when there is a configuration problem."""


class AuthenticationError(ZohoSDKError):
    """Raised when authentication fails."""


class APIError(ZohoSDKError):
    """
    Raised when the Zoho Projects API returns an error.

    Attributes:
        status_code (int): The HTTP status code of the error response.
        message (str): The error message from the API.
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class ValidationError(ZohoSDKError):
    """Raised when API response validation fails."""
