import time

import httpx
import pytest
import respx

from zoho_projects_sdk.client import ZohoProjects


def _prime_auth(client: ZohoProjects, portal_id: str = "portal-e2e") -> None:
    client._auth_handler._access_token = "e2e-token"
    client._auth_handler._token_expiry = time.time() + 3600
    client._auth_handler.portal_id = portal_id


@respx.mock
@pytest.mark.asyncio()
async def test_end_to_end_project_listing_and_tasks() -> None:
    sdk = ZohoProjects(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        portal_id="portal",
    )
    _prime_auth(sdk)

    projects_route = respx.get(
        "https://projectsapi.zoho.com/api/v3/portal/portal-e2e/projects"
    ).mock(
        return_value=httpx.Response(
            200, json={"projects": [{"id": 1, "name": "Alpha", "status": "active"}]}
        )
    )
    tasks_route = respx.get(
        "https://projectsapi.zoho.com/api/v3/portal/portal-e2e/projects/1/tasks"
    ).mock(
        return_value=httpx.Response(200, json={"tasks": [{"id": 10, "name": "Setup"}]})
    )

    projects = await sdk.projects.get_all()
    tasks = await sdk.tasks.get_all(project_id=1)

    assert projects_route.called
    assert tasks_route.called
    assert projects[0].name == "Alpha"
    assert tasks[0].id == 10

    await sdk.close()
