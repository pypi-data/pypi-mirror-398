import httpx
import pytest
import respx

from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.config import ZohoAuthConfig


@respx.mock
@pytest.mark.asyncio()
async def test_oauth_refresh_flow_returns_token() -> None:
    respx.post("https://accounts.zoho.com/oauth/v2/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "e2e-token", "expires_in": 3600}
        )
    )
    config = ZohoAuthConfig(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )
    handler = ZohoOAuth2Handler(config=config)

    token_first = await handler.get_access_token()
    token_second = await handler.get_access_token()

    assert token_first == "e2e-token"
    assert token_second == "e2e-token"
