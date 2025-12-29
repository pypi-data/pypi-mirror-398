"""
Global test fixtures and configurations for the Zoho Projects SDK tests.

This module provides centralized fixtures for common test objects, including:
- Authentication parameters and handlers
- API clients and their dependencies
- Mock implementations of core SDK components
- Test data configurations
"""

from typing import Dict
from unittest.mock import AsyncMock, Mock

import pytest

from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.config import ZohoAuthConfig
from zoho_projects_sdk.http_client import ApiClient


@pytest.fixture
def auth_params() -> Dict[str, str]:
    """
    Provides default authentication parameters for testing.

    Returns:
        dict: A dictionary containing default authentication parameters
              including client_id, client_secret, refresh_token, and portal_id.
    """
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "refresh_token": "test_refresh_token",
        "portal_id": "test_portal_id",
    }


@pytest.fixture
def auth_config(
    auth_params: Dict[str, str],  # pylint: disable=redefined-outer-name
) -> ZohoAuthConfig:
    """
    Provides a ZohoAuthConfig instance with test parameters.

    Args:
        auth_params: The authentication parameters fixture.

    Returns:
        ZohoAuthConfig: A configuration instance with test values.
    """
    return ZohoAuthConfig(**auth_params)


@pytest.fixture
def mock_auth_handler() -> Mock:
    """
    Creates a mock authentication handler for testing purposes.

    This fixture provides a mock ZohoOAuth2Handler with predefined behavior,
    including a mock get_access_token method that returns a test access token.

    Returns:
        Mock: A mock ZohoOAuth2Handler instance with preconfigured behavior.
    """
    mock = Mock(spec=ZohoOAuth2Handler)
    mock.portal_id = "test_portal_id"
    mock.get_access_token = AsyncMock(return_value="test_access_token")
    return mock


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """
    Creates a mock API client for testing purposes.

    This fixture provides a mock ApiClient with the correct AsyncMock spec,
    allowing tests to control the behavior of API calls without making HTTP requests.

    Returns:
        AsyncMock: A mock ApiClient instance.
    """
    mock = AsyncMock(spec=ApiClient)
    # Set up the mock to have a portal_id property that can be accessed
    # This simulates the public portal_id property of ApiClient
    mock.portal_id = "test_portal_id"
    return mock


@pytest.fixture
def mock_zoho_client(
    mock_auth_handler: Mock, mock_api_client: AsyncMock
) -> ZohoProjects:
    """
    Creates a ZohoProjects instance with mocked dependencies.

    This fixture provides a ZohoProjects client with mocked auth handler
    and API client, allowing tests to focus on client logic without external deps.

    Args:
        mock_auth_handler: The mocked authentication handler fixture
        mock_api_client: The mocked API client fixture

    Returns:
        ZohoProjects: A ZohoProjects instance with mocked dependencies.
    """
    # pylint: disable=redefined-outer-name,protected-access
    client_instance = ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
    )
    client_instance._auth_handler = mock_auth_handler
    client_instance._api_client = mock_api_client
    return client_instance


@pytest.fixture
def api_client_with_mocks(auth_config: ZohoAuthConfig) -> ApiClient:
    """
    Creates an ApiClient instance with mocked dependencies.

    This fixture provides an ApiClient with a mocked auth handler,
    allowing tests to control auth behavior while testing HTTP client functionality.

    Args:
        auth_config: The authentication configuration fixture

    Returns:
        ApiClient: An ApiClient instance with mocked authentication.
    """
    # pylint: disable=redefined-outer-name
    auth_handler = ZohoOAuth2Handler(config=auth_config)
    api_client_instance = ApiClient(auth_handler=auth_handler)
    return api_client_instance
