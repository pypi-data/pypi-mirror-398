import time

import pytest

from zoho_projects_sdk.http_client import ApiClient


class _FastAuth:
    portal_id = "portal-perf"

    async def get_access_token(self) -> str:
        return "token"


@pytest.mark.asyncio()
async def test_get_headers_runs_quickly() -> None:
    client = ApiClient(auth_handler=_FastAuth())
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        await client.get_headers()
    duration = time.perf_counter() - start
    assert duration < 0.05
    await client.close()
