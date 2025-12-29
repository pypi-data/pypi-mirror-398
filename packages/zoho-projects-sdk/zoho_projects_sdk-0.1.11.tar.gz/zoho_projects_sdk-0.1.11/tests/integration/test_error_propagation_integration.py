"""
Integration tests for error propagation between components.
These tests verify that errors are properly propagated between different components.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.config import ZohoAuthConfig
from zoho_projects_sdk.exceptions import APIError
from zoho_projects_sdk.http_client import ApiClient


@pytest.mark.asyncio
async def test_http_status_error_propagation_from_api_client_to_modules() -> None:
    """Test that HTTP status errors are properly propagated from API client to modules."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Mock the API client's get method to raise an APIError
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Create a mock APIError
            mock_api_get.side_effect = APIError(status_code=404, message="Not Found")

            # Try to get a project which should raise an APIError
            with pytest.raises(APIError) as exc_info:
                await client.projects.get(project_id=999)  # Non-existent project

            # Verify the error was properly propagated and converted
            assert exc_info.value.status_code == 404
            assert "Not Found" in exc_info.value.message


@pytest.mark.asyncio
async def test_network_error_propagation_through_retry_mechanism() -> None:
    """Test that network errors are properly handled by the retry mechanism."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Mock the API client's get method to raise a RequestError
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            # Create a mock network error
            mock_api_get.side_effect = httpx.RequestError(
                "Network error occurred", request=Mock()
            )

            # Try to get a project which should trigger retries then raise the error
            with pytest.raises(httpx.RequestError):
                await client.projects.get(project_id=1)


@pytest.mark.asyncio
async def test_auth_error_propagation_to_api_client_and_modules() -> None:
    """Test that authentication errors are properly propagated through the chain."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock a failed token refresh response
        error_response = Mock()
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=Mock(),
            response=Mock(status_code=401, text="Unauthorized"),
        )
        mock_post.return_value = error_response

        # Create auth handler that will fail
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="invalid_refresh_token",
            portal_id="test_portal_id",
        )
        auth_handler = ZohoOAuth2Handler(config=config)

        # Create API client with the failing auth handler
        api_client = ApiClient(auth_handler=auth_handler)

        # Try to make a request which should fail at the auth level
        with pytest.raises(Exception):  # This will be an HTTPStatusError from auth
            await api_client.get_headers()


@pytest.mark.asyncio
async def test_api_error_propagation_from_http_client_to_main_client() -> None:
    """Test that API errors are properly propagated from HTTP client to main client."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Mock the API client's get method to raise an APIError
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            mock_api_get.side_effect = APIError(
                status_code=500, message="Internal Server Error"
            )

            # Try to get a project which should raise an APIError after retries
            with pytest.raises(APIError) as exc_info:
                await client.projects.get(project_id=1)

            # Verify the error was properly propagated
            assert exc_info.value.status_code == 500
            assert "Internal Server Error" in exc_info.value.message


@pytest.mark.asyncio
async def test_error_handling_in_different_http_methods() -> None:
    """Test error propagation in different HTTP methods (GET, POST, PATCH, DELETE)."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Test error propagation in GET request
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            mock_api_get.side_effect = APIError(status_code=403, message="Forbidden")

            with pytest.raises(APIError) as exc_info:
                await client.projects.get(project_id=1)
            assert exc_info.value.status_code == 403

        # Test error propagation in POST request
        with patch.object(
            client._api_client, "post", new_callable=AsyncMock
        ) as mock_api_post:
            mock_api_post.side_effect = APIError(status_code=400, message="Bad Request")

            with pytest.raises(APIError) as exc_info:
                await client.projects.create(project_data=Mock())
            assert exc_info.value.status_code == 400

        # Test error propagation in PATCH request
        with patch.object(
            client._api_client, "patch", new_callable=AsyncMock
        ) as mock_api_patch:
            mock_api_patch.side_effect = APIError(status_code=409, message="Conflict")

            with pytest.raises(APIError) as exc_info:
                await client.tasks.update(project_id=1, task_id=1, task_data=Mock())
            assert exc_info.value.status_code == 409

        # Test error propagation in DELETE request
        with patch.object(
            client._api_client, "delete", new_callable=AsyncMock
        ) as mock_api_delete:
            mock_api_delete.side_effect = APIError(status_code=423, message="Locked")

            with pytest.raises(APIError) as exc_info:
                await client.tasks.delete(project_id=1, task_id=1)
            assert exc_info.value.status_code == 423


@pytest.mark.asyncio
async def test_error_context_preservation_across_components() -> None:
    """Test that error context is preserved as errors propagate through components."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Mock the API client's get method to raise an APIError with specific context
        with patch.object(
            client._api_client, "get", new_callable=AsyncMock
        ) as mock_api_get:
            mock_api_get.side_effect = APIError(
                status_code=422, message="Unprocessable Entity - Invalid data format"
            )

            # Try to get a project which should raise an APIError with preserved context
            with pytest.raises(APIError) as exc_info:
                await client.projects.get(project_id=1)

            # Verify the error context was preserved
            assert exc_info.value.status_code == 422
            assert "Unprocessable Entity" in exc_info.value.message
            assert "Invalid data format" in exc_info.value.message


@pytest.mark.asyncio
async def test_error_propagation_with_retry_logic() -> None:
    """Test error propagation behavior with the retry mechanism."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
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

        # Mock the underlying HTTP client's get method to simulate retries
        with patch.object(
            client._api_client._http_client, "get", new_callable=AsyncMock
        ) as mock_http_get:
            call_count = 0

            async def mock_get_side_effect(
                endpoint: str, *args: Any, **kwargs: Any
            ) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                url = f"https://projectsapi.zoho.com/api/v3{endpoint}"

                if call_count <= 2:
                    status_code = 500 if call_count == 1 else 502
                    return httpx.Response(
                        status_code=status_code,
                        request=httpx.Request("GET", url),
                        content=b"Server Error",
                    )

                return httpx.Response(
                    status_code=200,
                    request=httpx.Request("GET", url),
                    json={
                        "projects": [
                            {
                                "id": 1,
                                "name": "Success Project",
                                "status": "active",
                            }
                        ]
                    },
                )

            mock_http_get.side_effect = mock_get_side_effect

            # This should eventually succeed after retries
            project = await client.projects.get(project_id=1)
            assert project.name == "Success Project"

            # Verify that 3 HTTP calls were made (2 retries + 1 success)
            assert call_count == 3

        # Now test with 4xx error that should NOT be retried
        with patch.object(
            client._api_client._http_client, "get", new_callable=AsyncMock
        ) as mock_http_get_4xx:

            async def mock_get_4xx(
                endpoint: str, *args: Any, **kwargs: Any
            ) -> httpx.Response:
                url = f"https://projectsapi.zoho.com/api/v3{endpoint}"
                return httpx.Response(
                    status_code=400,
                    request=httpx.Request("GET", url),
                    content=b"Bad Request",
                )

            mock_http_get_4xx.side_effect = mock_get_4xx

            # This should fail immediately without retries
            with pytest.raises(APIError) as exc_info:
                await client.projects.get(project_id=2)

            # Verify the error was propagated correctly
            assert exc_info.value.status_code == 400
            assert "Bad Request" in exc_info.value.message

            # Verify that the method was called only once (no retries for 4xx)
            assert mock_http_get_4xx.await_count == 1
