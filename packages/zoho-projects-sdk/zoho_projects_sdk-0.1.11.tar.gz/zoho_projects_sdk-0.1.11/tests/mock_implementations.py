"""
Mock implementations of external dependencies for the Zoho Projects SDK tests.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import httpx


class MockZohoOAuth2Handler:
    """
    Mock implementation of ZohoOAuth2Handler for testing purposes.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        portal_id: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or "test_client_id"
        self.client_secret = client_secret or "test_client_secret"
        self.refresh_token = refresh_token or "test_refresh_token"
        self.portal_id = portal_id or "test_portal_id"
        self._access_token = "mock_access_token"
        self._token_expiry: Optional[float] = None
        self.get_access_token = AsyncMock(return_value=self._access_token)


class MockHttpxAsyncClient:
    """
    Mock implementation of httpx.AsyncClient for testing HTTP requests.
    """

    def __init__(self) -> None:
        self.get = AsyncMock()
        self.post = AsyncMock()
        self.put = AsyncMock()
        self.patch = AsyncMock()
        self.delete = AsyncMock()
        self.aclose = AsyncMock()
        self._request_count: int = 0

    def add_response(self, method: str, _url: str, response: Any) -> None:
        """Add a mock response for a specific method and URL."""
        mock_method = getattr(self, method.lower())
        mock_method.return_value = response


class MockHttpResponse:
    """
    Mock implementation of httpx.Response for testing.
    """

    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text_data: str = "",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self._json_data: Dict[str, Any] = json_data or {}
        self._text_data = text_data
        self.headers = headers or {}
        self.content = text_data.encode("utf-8")

        # Mock the json() method
        self.json = Mock(return_value=self._json_data)

        # Mock the raise_for_status method
        if status_code >= 400:
            request = httpx.Request("GET", "https://example.com/mock")
            response = httpx.Response(
                status_code=status_code,
                request=request,
                content=self.content,
                headers=self.headers,
            )
            self.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "Mock error", request=request, response=response
                )
            )
        else:
            self.raise_for_status = Mock()


class MockApiClient:  # noqa: PLR0902
    """
    Mock implementation of ApiClient for testing API interactions.
    """

    def __init__(self, auth_handler: Optional[MockZohoOAuth2Handler] = None) -> None:
        self.auth_handler = auth_handler or MockZohoOAuth2Handler()
        self.portal_id = getattr(self.auth_handler, "portal_id", None)
        self.get_headers = AsyncMock(
            return_value={
                "Authorization": "Zoho-oauthtoken mock_access_token",
                "Accept": "application/json",
                "User-Agent": "zoho-projects-sdk-python",
            }
        )
        # Group HTTP methods together
        self.http_methods = self._create_http_methods()

    def _create_http_methods(self) -> Dict[str, AsyncMock]:
        """Create mock HTTP methods."""
        return {
            "get": AsyncMock(),
            "post": AsyncMock(),
            "put": AsyncMock(),
            "patch": AsyncMock(),
            "delete": AsyncMock(),
            "close": AsyncMock(),
        }

    def __getattr__(self, name: str) -> Any:
        """Delegate HTTP method calls to the http_methods dict."""
        if name in self.http_methods:
            return self.http_methods[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


def create_mock_auth_handler(
    *,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    refresh_token: Optional[str] = None,
    portal_id: Optional[str] = None,
) -> MockZohoOAuth2Handler:
    """Factory function to create a mock authentication handler."""
    return MockZohoOAuth2Handler(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        portal_id=portal_id,
    )


def create_mock_http_client() -> MockHttpxAsyncClient:
    """Factory function to create a mock HTTP client."""
    return MockHttpxAsyncClient()


def create_mock_http_response(
    *,
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text_data: str = "",
    headers: Optional[Dict[str, str]] = None,
) -> MockHttpResponse:
    """Factory function to create a mock HTTP response."""
    return MockHttpResponse(
        status_code=status_code,
        json_data=json_data,
        text_data=text_data,
        headers=headers,
    )


def create_mock_api_client(
    *, auth_handler: Optional[MockZohoOAuth2Handler] = None
) -> MockApiClient:
    """Factory function to create a mock API client."""
    return MockApiClient(auth_handler=auth_handler)


# Mock implementations for specific API modules
class MockProjectsAPI:
    """Mock implementation of ProjectsAPI."""

    def __init__(self, api_client: Optional[MockApiClient] = None) -> None:
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockTasksAPI:
    """Mock implementation of TasksAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockIssuesAPI:
    """Mock implementation of IssuesAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockUsersAPI:
    """Mock implementation of UsersAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockClientsAPI:
    """Mock implementation of ClientsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockContactsAPI:
    """Mock implementation of ContactsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockPortalsAPI:
    """Mock implementation of PortalsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockRolesAPI:
    """Mock implementation of RolesAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockTagsAPI:
    """Mock implementation of TagsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockTasklistsAPI:
    """Mock implementation of TasklistsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockTimelogsAPI:
    """Mock implementation of TimelogsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockCommentsAPI:
    """Mock implementation of CommentsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockAttachmentsAPI:
    """Mock implementation of AttachmentsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockBaselinesAPI:
    """Mock implementation of BaselinesAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockBusinessHoursAPI:
    """Mock implementation of BusinessHoursAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockEventsAPI:
    """Mock implementation of EventsAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockMilestonesAPI:
    """Mock implementation of MilestonesAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()


class MockPhasesAPI:
    """Mock implementation of PhasesAPI."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client or create_mock_api_client()
        self.get = AsyncMock()
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.list = AsyncMock()
