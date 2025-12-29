from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock

import httpx
import pytest

from zoho_projects_sdk.exceptions import APIError
from zoho_projects_sdk.http_client import ApiClient


class _StubAuth:
    portal_id = "portal-1"

    async def get_access_token(self) -> str:
        return "access-token"


class _StubResponse:
    def __init__(
        self,
        json_payload: Dict[str, Any],
        error: Optional[Exception] = None,
        status: int = 200,
    ):
        self._json_payload = json_payload
        self._error = error
        request = httpx.Request("GET", "https://example.com")
        self._httpx_response = httpx.Response(status, request=request)
        self.request = request
        self.response = self._httpx_response

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error

    def json(self) -> Dict[str, Any]:
        return dict(self._json_payload)


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(status, request=request, text="error")
    return httpx.HTTPStatusError("boom", request=request, response=response)


@pytest.fixture()
def client() -> ApiClient:
    api_client = ApiClient(auth_handler=_StubAuth())
    api_client._http_client = AsyncMock()
    return api_client


@pytest.mark.asyncio()
async def test_portal_id_property(client: ApiClient) -> None:
    assert client.portal_id == "portal-1"


@pytest.mark.asyncio()
async def test_get_headers_uses_auth_handler(client: ApiClient) -> None:
    headers = await client.get_headers()
    assert headers["Authorization"] == "Zoho-oauthtoken access-token"


@pytest.mark.asyncio()
async def test_get_returns_json_payload(client: ApiClient) -> None:
    response = _StubResponse({"value": 1})
    client._http_client.get.return_value = response
    data = await ApiClient.get.__wrapped__(client, "/items")
    assert data == {"value": 1}
    client._http_client.get.assert_awaited_once()


@pytest.mark.asyncio()
async def test_post_returns_json_payload(client: ApiClient) -> None:
    response = _StubResponse({"created": True})
    client._http_client.post.return_value = response
    payload = {"name": "test"}
    data = await ApiClient.post.__wrapped__(client, "/items", json=payload)
    assert data == {"created": True}
    client._http_client.post.assert_awaited_once()


@pytest.mark.asyncio()
async def test_patch_returns_json_payload(client: ApiClient) -> None:
    response = _StubResponse({"updated": True})
    client._http_client.patch.return_value = response
    payload = {"name": "updated"}
    data = await ApiClient.patch.__wrapped__(client, "/items/1", json=payload)
    assert data == {"updated": True}
    client._http_client.patch.assert_awaited_once()


@pytest.mark.asyncio()
async def test_delete_succeeds(client: ApiClient) -> None:
    response = _StubResponse({"deleted": True})
    client._http_client.delete.return_value = response
    data = await ApiClient.delete.__wrapped__(client, "/items/1")
    assert data == {"deleted": True}
    client._http_client.delete.assert_awaited_once()


@pytest.mark.asyncio()
async def test_get_converts_client_error_to_api_error(client: ApiClient) -> None:
    error = _status_error(404)
    client._http_client.get.return_value = _StubResponse({}, error=error)
    with pytest.raises(APIError) as exc:
        await ApiClient.get.__wrapped__(client, "/missing")
    assert exc.value.status_code == 404
    assert "error" in exc.value.message


@pytest.mark.asyncio()
async def test_get_propagates_server_errors(client: ApiClient) -> None:
    error = _status_error(502)
    client._http_client.get.return_value = _StubResponse({}, error=error, status=502)
    with pytest.raises(httpx.HTTPStatusError):
        await ApiClient.get.__wrapped__(client, "/unstable")


@pytest.mark.asyncio()
async def test_get_propagates_request_errors(client: ApiClient) -> None:
    request_error = httpx.RequestError(
        "network", request=httpx.Request("GET", "https://example.com")
    )
    client._http_client.get.side_effect = request_error
    with pytest.raises(httpx.RequestError):
        await ApiClient.get.__wrapped__(client, "/network")


@pytest.mark.asyncio()
async def test_close_closes_underlying_client(client: ApiClient) -> None:
    closer = AsyncMock()
    client._http_client.aclose = closer
    await client.close()
    closer.assert_awaited_once()
