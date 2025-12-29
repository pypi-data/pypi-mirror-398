import pytest

from zoho_projects_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ValidationError,
    ZohoSDKError,
)


def test_api_error_contains_status_and_message() -> None:
    error = APIError(status_code=401, message="unauthorized")
    assert isinstance(error, ZohoSDKError)
    assert error.status_code == 401
    assert "401" in str(error)


@pytest.mark.parametrize(
    "exception_cls", [ConfigurationError, AuthenticationError, ValidationError]
)
def test_exceptions_inherit_base(exception_cls) -> None:
    error = exception_cls("msg")
    assert isinstance(error, ZohoSDKError)
    assert str(error) == "msg"
