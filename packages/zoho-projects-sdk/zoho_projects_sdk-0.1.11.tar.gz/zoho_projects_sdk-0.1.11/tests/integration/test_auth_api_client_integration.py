"""
Integration tests for authentication and API client interaction.
These tests verify that authentication tokens are obtained and used correctly.
"""

# pylint: disable=protected-access

from unittest.mock import AsyncMock, Mock, patch

import pytest

from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.config import ZohoAuthConfig
from zoho_projects_sdk.http_client import ApiClient


@pytest.mark.asyncio
async def test_api_client_uses_auth_token_in_requests() -> None:
    """Test that the API client properly uses authentication tokens in requests."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_access_token_12345",
            "expires_in": 3600,  # 1 hour
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the auth handler with test credentials
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )
        auth_handler = ZohoOAuth2Handler(config=config)

        # Create the API client with the auth handler
        api_client = ApiClient(auth_handler=auth_handler)

        # Mock the httpx client to avoid actual network calls
        with patch.object(api_client._http_client, "get") as mock_http_get:
            mock_http_get.return_value.json.return_value = {"test": "data"}
            mock_http_get.return_value.raise_for_status.return_value = None

            # Get headers which should trigger token refresh
            headers = await api_client.get_headers()

            # Verify the token was properly set in headers
            assert "Zoho-oauthtoken test_access_token_12345" == headers["Authorization"]
            assert "application/json" == headers["Accept"]
            assert "zoho-projects-sdk-python" == headers["User-Agent"]

            # Verify the token refresh was called
            mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_token_refresh_before_expiry() -> None:
    """Test that tokens are automatically refreshed before expiry."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the initial token refresh response
        initial_response = Mock()
        initial_response.json.return_value = {
            "access_token": "initial_token",
            "expires_in": 60,  # 1 minute (short for testing)
        }
        initial_response.raise_for_status.return_value = None
        mock_post.return_value = initial_response

        # Create the auth handler
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )
        auth_handler = ZohoOAuth2Handler(config=config)

        # Manually set the token expiry to be in the past to trigger refresh
        auth_handler._token_expiry = 1000  # A timestamp in the past

        # Now get the token - this should trigger a refresh
        token = await auth_handler.get_access_token()

        # Verify it's the initial token
        assert token == "initial_token"

        # Mock the second token refresh response
        second_response = Mock()
        second_response.json.return_value = {
            "access_token": "refreshed_token",
            "expires_in": 3600,
        }
        second_response.raise_for_status.return_value = None
        mock_post.return_value = second_response

        # Simulate that the token has expired by setting the expiry to the past
        auth_handler._token_expiry = 1000  # A timestamp in the past

        # Get the token again - this should trigger another refresh
        new_token = await auth_handler.get_access_token()

        # Verify the token was refreshed
        assert new_token == "refreshed_token"
        assert mock_post.call_count >= 2


@pytest.mark.asyncio
async def test_api_client_uses_auth_token_in_all_request_types() -> None:
    """Test that API client properly uses auth tokens in all types of requests."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_access_token_67890",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create auth handler and API client
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )
        auth_handler = ZohoOAuth2Handler(config=config)
        api_client = ApiClient(auth_handler=auth_handler)

        # Mock the httpx client methods
        with (
            patch.object(
                api_client._http_client, "get", new_callable=AsyncMock
            ) as mock_http_get,
            patch.object(
                api_client._http_client, "post", new_callable=AsyncMock
            ) as mock_http_post,
            patch.object(
                api_client._http_client, "patch", new_callable=AsyncMock
            ) as mock_http_patch,
            patch.object(
                api_client._http_client, "delete", new_callable=AsyncMock
            ) as mock_http_delete,
        ):

            def _mock_response() -> Mock:
                response = Mock()
                response.json.return_value = {"result": "success"}
                response.raise_for_status.return_value = None
                return response

            for mock_method in [
                mock_http_get,
                mock_http_post,
                mock_http_patch,
                mock_http_delete,
            ]:
                mock_method.return_value = _mock_response()

            # Make a GET request
            await api_client.get("/test/endpoint")
            # Verify the Authorization header was set correctly
            mock_http_get.assert_called_once()
            _, kwargs = mock_http_get.call_args
            assert (
                kwargs["headers"]["Authorization"]
                == "Zoho-oauthtoken test_access_token_67890"
            )

            # Reset the mock
            mock_http_get.reset_mock()

            # Make a POST request
            await api_client.post("/test/endpoint", json={"data": "test"})
            # Verify the Authorization header was set correctly
            mock_http_post.assert_called_once()
            _, kwargs = mock_http_post.call_args
            assert (
                kwargs["headers"]["Authorization"]
                == "Zoho-oauthtoken test_access_token_67890"
            )

            # Reset the mock
            mock_http_post.reset_mock()

            # Make a PATCH request
            await api_client.patch("/test/endpoint", json={"data": "test"})
            # Verify the Authorization header was set correctly
            mock_http_patch.assert_called_once()
            _, kwargs = mock_http_patch.call_args
            assert (
                kwargs["headers"]["Authorization"]
                == "Zoho-oauthtoken test_access_token_67890"
            )

            # Reset the mock
            mock_http_patch.reset_mock()

            # Make a DELETE request
            await api_client.delete("/test/endpoint")
            # Verify the Authorization header was set correctly
            mock_http_delete.assert_called_once()
            _, kwargs = mock_http_delete.call_args
            assert (
                kwargs["headers"]["Authorization"]
                == "Zoho-oauthtoken test_access_token_67890"
            )


@pytest.mark.asyncio
async def test_client_api_module_auth_integration() -> None:
    """Ensure API modules (projects/tasks/issues) use the authenticated client."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "client_init_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Verify that the auth handler and API client were properly initialized
        assert client._auth_handler is not None
        assert client._api_client is not None

        # Verify that the auth handler has the correct credentials
        assert client._auth_handler.client_id == "test_client_id"
        assert client._auth_handler.client_secret == "test_client_secret"
        assert client._auth_handler.refresh_token == "test_refresh_token"
        assert client._auth_handler.portal_id == "test_portal_id"

        # Mock the httpx client to avoid actual network calls
        with patch.object(client._api_client._http_client, "get") as mock_http_get:
            mock_http_get.return_value.json.return_value = {"test": "data"}
            mock_http_get.return_value.raise_for_status.return_value = None

            # Get headers which should use the auth handler
            headers = await client._api_client.get_headers()

            # Verify the token was properly set in headers
            assert "Zoho-oauthtoken client_init_token" == headers["Authorization"]


@pytest.mark.asyncio
async def test_auth_error_propagation_to_api_client() -> None:
    """Test that authentication errors propagate through the API client."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock a failed token refresh response
        token_response = Mock()
        token_response.raise_for_status.side_effect = Exception("Token refresh failed")
        mock_post.return_value = token_response

        # Create auth handler and API client
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )
        auth_handler = ZohoOAuth2Handler(config=config)

        # Try to get the access token, which should fail
        with pytest.raises(Exception, match="Token refresh failed"):
            await auth_handler.get_access_token()


@pytest.mark.asyncio
async def test_client_modules_use_authenticated_api_client() -> None:
    """Test that client modules properly use the authenticated API client."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "module_auth_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Verify that API modules have access to the authenticated client
        projects_api = client.projects
        tasks_api = client.tasks
        issues_api = client.issues

        assert projects_api._client is client._api_client
        assert tasks_api._client is client._api_client
        assert issues_api._client is client._api_client

        # Mock the httpx client to avoid actual network calls
        with patch.object(client._api_client._http_client, "get") as mock_http_get:
            mock_http_get.return_value.json.return_value = {"test": "data"}
            mock_http_get.return_value.raise_for_status.return_value = None

            # Get headers which should use the shared auth handler
            headers = await client._api_client.get_headers()

            # Verify the token was properly set in headers
            assert "Zoho-oauthtoken module_auth_token" == headers["Authorization"]
