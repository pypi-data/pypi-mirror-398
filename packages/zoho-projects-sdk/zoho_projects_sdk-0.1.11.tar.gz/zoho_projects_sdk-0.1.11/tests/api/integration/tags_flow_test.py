from typing import Dict, Union, cast

import httpx
import pytest
import respx

from zoho_projects_sdk.api.tags import TagsAPI
from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.http_client import ApiClient
from zoho_projects_sdk.models.tag_models import Tag


class _AuthStub:
    portal_id = "portal-integration"

    async def get_access_token(self) -> str:
        return "integration-token"


@respx.mock
@pytest.mark.asyncio()
async def test_tags_api_fetches_data_with_http_client() -> None:
    api_client = ApiClient(auth_handler=cast(ZohoOAuth2Handler, _AuthStub()))
    route = respx.get(
        "https://projectsapi.zoho.com/api/v3/portal/portal-integration/tags"
    ).mock(
        return_value=httpx.Response(
            200, json={"tags": [{"id": 1, "name": "Integration"}]}
        )
    )
    tags_api = TagsAPI(api_client)

    tags = await tags_api.get_all()

    assert route.called
    assert len(tags) == 1
    assert tags[0].name == "Integration"
    assert (
        route.calls[0].request.headers["Authorization"]
        == "Zoho-oauthtoken integration-token"
    )

    await api_client.close()


@respx.mock
@pytest.mark.asyncio()
async def test_tags_api_create_round_trip() -> None:
    api_client = ApiClient(auth_handler=cast(ZohoOAuth2Handler, _AuthStub()))
    payload: Dict[str, Union[str, int]] = {"id": 9, "name": "New"}
    route = respx.post(
        "https://projectsapi.zoho.com/api/v3/portal/portal-integration/tags"
    ).mock(return_value=httpx.Response(200, json={"tag": payload}))

    created = await TagsAPI(api_client).create(tag_data=Tag.model_validate(payload))

    assert route.called
    assert created.id == 9
    assert created.name == "New"

    await api_client.close()
