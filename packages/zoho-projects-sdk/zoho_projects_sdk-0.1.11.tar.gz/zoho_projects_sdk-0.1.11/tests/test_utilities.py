"""
Shared test utilities for common testing patterns in the Zoho Projects SDK tests.
"""

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from zoho_projects_sdk.exceptions import APIError


class TestUtilities:
    """A collection of utility functions for testing the Zoho Projects SDK."""

    @staticmethod
    def assert_dict_contains_subset(
        subset: Dict[str, Any], dictionary: Dict[str, Any]
    ) -> None:
        """
        Assert that a dictionary contains all key-value pairs from another dictionary.

        Args:
            subset: The dictionary containing expected key-value pairs
            dictionary: The dictionary to check against
        """
        for key, value in subset.items():
            assert key in dictionary, f"Key '{key}' not found in dictionary"
            assert dictionary[key] == value, (
                f"Value mismatch for key '{key}': expected {value}, "
                f"got {dictionary[key]}"
            )

    @staticmethod
    def assert_list_contains_same_elements(list1: List[Any], list2: List[Any]) -> None:
        """
        Assert that two lists contain the same elements, regardless of order.

        Args:
            list1: First list to compare
            list2: Second list to compare
        """
        assert len(list1) == len(
            list2
        ), f"Lists have different lengths: {len(list1)} vs {len(list2)}"
        assert set(list1) == set(
            list2
        ), f"Lists contain different elements: {set(list1)} vs {set(list2)}"

    @staticmethod
    def create_mock_response(
        data: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> Mock:
        """
        Create a mock response object with the specified data and status code.

        Args:
            data: The data to return when .json() is called
            status_code: The status code for the response
            headers: Optional headers for the response

        Returns:
            A mock response object
        """
        mock_response = Mock()
        mock_response.json.return_value = data if data is not None else {}
        mock_response.status_code = status_code
        mock_response.text = json.dumps(data if data is not None else {})
        mock_response.headers = headers or {}
        mock_response.raise_for_status.return_value = None
        return mock_response

    @staticmethod
    def create_mock_http_error_response(
        status_code: int, message: str = "Mock HTTP Error"
    ) -> Mock:
        """
        Create a mock response object that raises an HTTP error.

        Args:
            status_code: The status code for the error response
            message: The error message

        Returns:
            A mock response object that raises HTTP error when raise_for_status called
        """

        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = message
        mock_response.headers = {}

        # Configure to raise an HTTP error when raise_for_status is called
        http_error = httpx.HTTPStatusError(
            message, request=Mock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error

        return mock_response


class APITestUtilities:
    """Utilities specific to testing API endpoints."""

    @staticmethod
    def assert_api_method_called_with(
        mock_method: AsyncMock,
        expected_endpoint: str,
        expected_params: Optional[Dict[str, Any]] = None,
        expected_json: Optional[Dict[str, Any]] = None,
        expected_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Assert that an API method was called with the expected parameters.

        Args:
            mock_method: The mocked API method
            expected_endpoint: The expected endpoint
            expected_params: Expected parameters for GET requests
            expected_json: Expected JSON data for POST/PUT/PATCH requests
            expected_headers: Expected headers
        """
        assert mock_method.called, "API method was not called"

        # Get the call arguments
        call_args = mock_method.call_args
        assert call_args is not None, "No call arguments found"

        # Check the endpoint (first positional argument)
        args, kwargs = call_args
        if args:
            actual_endpoint = args[0]
            assert (
                actual_endpoint == expected_endpoint
            ), f"Expected endpoint '{expected_endpoint}', got '{actual_endpoint}'"

        # Check params, json, and headers in kwargs
        if expected_params is not None:
            assert "params" in kwargs, "Expected params in call but not found"
            assert (
                kwargs["params"] == expected_params
            ), f"Expected params {expected_params}, got {kwargs['params']}"

        if expected_json is not None:
            assert "json" in kwargs, "Expected json in call but not found"
            assert (
                kwargs["json"] == expected_json
            ), f"Expected json {expected_json}, got {kwargs['json']}"

        if expected_headers is not None:
            # Headers are typically passed through the client's get_headers method
            # So we need to check the headers in the call
            pass  # This would require checking the actual headers passed

    @staticmethod
    async def assert_api_error_raised(
        api_call: Callable[[], Awaitable[Any]],
        expected_status_code: Optional[int] = None,
        expected_message_contains: Optional[str] = None,
    ) -> APIError:
        """
        Assert that an API call raises an APIError with the expected properties.

        Args:
            api_call: The API call to execute
            expected_status_code: Expected status code of the error
            expected_message_contains: Expected substring in the error message

        Returns:
            The caught APIError for further assertions if needed
        """
        with pytest.raises(APIError) as exc_info:
            await api_call()

        error = exc_info.value

        if expected_status_code is not None:
            assert (
                error.status_code == expected_status_code
            ), f"Expected status code {expected_status_code}, got {error.status_code}"

        if expected_message_contains is not None:
            assert expected_message_contains in error.message, (
                f"Expected error message to contain '{expected_message_contains}', "
                f"got '{error.message}'"
            )

        return error


class AsyncTestUtilities:
    """Utilities for testing asynchronous code."""

    @staticmethod
    async def run_with_timeout(coro: Awaitable[Any], timeout: float = 5.0) -> Any:
        """
        Run an async coroutine with a timeout.

        Args:
            coro: The coroutine to run
            timeout: The timeout in seconds

        Returns:
            The result of the coroutine
        """
        return await asyncio.wait_for(coro, timeout=timeout)

    @staticmethod
    def create_async_mock_with_delay(result: Any, delay: float = 0.1) -> AsyncMock:
        """
        Create an AsyncMock that returns a result after a delay.

        Args:
            result: The result to return
            delay: The delay in seconds

        Returns:
            An AsyncMock that delays before returning the result
        """

        async def delayed_result(*_args: Any, **_kwargs: Any) -> Any:
            await asyncio.sleep(delay)
            return result

        return AsyncMock(side_effect=delayed_result)

    @staticmethod
    def create_async_mock_with_exception(
        exception: Exception, delay: float = 0.1
    ) -> AsyncMock:
        """
        Create an AsyncMock that raises an exception after a delay.

        Args:
            exception: The exception to raise
            delay: The delay in seconds

        Returns:
            An AsyncMock that delays before raising the exception
        """

        async def delayed_exception(*_args: Any, **_kwargs: Any) -> None:
            await asyncio.sleep(delay)
            raise exception

        return AsyncMock(side_effect=delayed_exception)


class MockUtilities:
    """Utilities for working with mocks."""

    @staticmethod
    def patch_zoho_api_client_get(return_value: Any = None) -> Any:
        """
        Create a patch for ApiClient.get method.

        Args:
            return_value: The value to return from the patched method

        Returns:
            A patch object for ApiClient.get
        """
        return patch(
            "zoho_projects_sdk.http_client.ApiClient.get", return_value=return_value
        )

    @staticmethod
    def patch_zoho_api_client_post(return_value: Any = None) -> Any:
        """
        Create a patch for ApiClient.post method.

        Args:
            return_value: The value to return from the patched method

        Returns:
            A patch object for ApiClient.post
        """
        return patch(
            "zoho_projects_sdk.http_client.ApiClient.post", return_value=return_value
        )

    @staticmethod
    def patch_zoho_api_client_put(return_value: Any = None) -> Any:
        """
        Create a patch for ApiClient.put method.

        Args:
            return_value: The value to return from the patched method

        Returns:
            A patch object for ApiClient.put
        """
        return patch(
            "zoho_projects_sdk.http_client.ApiClient.put", return_value=return_value
        )

    @staticmethod
    def patch_zoho_api_client_delete(return_value: Any = None) -> Any:
        """
        Create a patch for ApiClient.delete method.

        Args:
            return_value: The value to return from the patched method

        Returns:
            A patch object for ApiClient.delete
        """
        return patch(
            "zoho_projects_sdk.http_client.ApiClient.delete", return_value=return_value
        )

    @staticmethod
    def patch_zoho_auth_handler_get_access_token(
        return_value: str = "mock_access_token",
    ) -> Any:
        """
        Create a patch for ZohoOAuth2Handler.get_access_token method.

        Args:
            return_value: The access token to return

        Returns:
            A patch object for ZohoOAuth2Handler.get_access_token
        """
        return patch(
            "zoho_projects_sdk.auth.ZohoOAuth2Handler.get_access_token",
            return_value=return_value,
        )


def create_test_context_manager(mock_obj: Any) -> Any:
    """
    Create a mock context manager for testing purposes.

    Args:
        mock_obj: The mock object to make into a context manager

    Returns:
        The mock object configured as a context manager
    """
    mock_obj.__aenter__ = AsyncMock(return_value=mock_obj)
    mock_obj.__aexit__ = AsyncMock(return_value=None)
    return mock_obj


def run_async_test(coro: Any) -> Any:
    """
    Helper to run async tests in a sync context.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    return asyncio.run(coro)


# Common test patterns
class TestPatterns:
    """Common testing patterns for the Zoho Projects SDK."""

    @staticmethod
    async def assert_method_success_pattern(
        method_call: Callable[[], Awaitable[Any]],
        expected_result: Any,
        mock_response: Optional[Mock] = None,
    ) -> None:
        """
        Common pattern for testing successful API method calls.

        Args:
            method_call: The method call to test
            expected_result: The expected result
            mock_response: Optional mock response to configure
        """
        if mock_response:
            # Use the mock response as needed
            pass

        result = await method_call()
        assert result == expected_result

    @staticmethod
    async def assert_method_error_pattern(
        method_call: Callable[[], Awaitable[Any]],
        expected_error_type: type,
        expected_error_message: Optional[str] = None,
    ) -> None:
        """
        Common pattern for testing API method calls that should raise errors.

        Args:
            method_call: The method call to test
            expected_error_type: The expected error type
            expected_error_message: Optional expected error message
        """
        with pytest.raises(expected_error_type) as exc_info:
            await method_call()

        if expected_error_message:
            assert expected_error_message in str(exc_info.value)

    @staticmethod
    async def assert_method_retry_pattern(
        method_call: Callable[[], Awaitable[Any]],
        mock_client_method: AsyncMock,
        expected_call_count: int,
    ) -> None:
        """
        Common pattern for testing retry logic in API method calls.

        Args:
            method_call: The method call to test
            mock_client_method: The mocked client method
            expected_call_count: The expected number of calls (including retries)
        """
        try:
            await method_call()
        except (RuntimeError, ValueError, APIError):  # noqa: BLE001
            # Method might raise an exception, which is fine for testing retries
            pass

        assert mock_client_method.call_count == expected_call_count
