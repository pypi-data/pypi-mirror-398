"""
This module contains the internal HTTP client for making API requests.
"""

from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .auth import ZohoOAuth2Handler
from .exceptions import APIError


class ApiClient:
    """
    An internal client that wraps httpx.AsyncClient to handle authentication,
    retries, and error handling.
    """

    def __init__(
        self,
        auth_handler: ZohoOAuth2Handler,
        base_url: str = "https://projectsapi.zoho.com/api/v3",
        timeout: Optional[float] = None,
    ):
        self._auth_handler = auth_handler
        self._http_client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    @property
    def portal_id(self) -> Optional[str]:
        """
        Returns the portal ID from the auth handler.
        """
        return self._auth_handler.portal_id

    async def get_headers(self) -> Dict[str, str]:
        """
        Constructs the necessary headers for an API request, including the auth token.
        """
        access_token = await self._auth_handler.get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/json",
            "User-Agent": "zoho-projects-sdk-python",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Performs a GET request."""
        headers = await self.get_headers()
        try:
            response = await self._http_client.get(
                endpoint, headers=headers, params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Only retry on 5xx errors
            if 500 <= e.response.status_code < 600:
                raise e
            # Don't retry on 4xx errors
            raise APIError(
                status_code=e.response.status_code, message=e.response.text
            ) from e
        except httpx.RequestError as e:
            # Retry on network errors
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def post(self, endpoint: str, json: Dict[str, Any]) -> Any:
        """Performs a POST request."""
        headers = await self.get_headers()
        try:
            response = await self._http_client.post(
                endpoint, headers=headers, json=json
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Only retry on 5xx errors
            if 500 <= e.response.status_code < 600:
                raise e
            # Don't retry on 4xx errors
            raise APIError(
                status_code=e.response.status_code, message=e.response.text
            ) from e
        except httpx.RequestError as e:
            # Retry on network errors
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def patch(self, endpoint: str, json: Dict[str, Any]) -> Any:
        """Performs a PATCH request."""
        headers = await self.get_headers()
        try:
            response = await self._http_client.patch(
                endpoint, headers=headers, json=json
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Only retry on 5xx errors
            if 500 <= e.response.status_code < 600:
                raise e
            # Don't retry on 4xx errors
            raise APIError(
                status_code=e.response.status_code, message=e.response.text
            ) from e
        except httpx.RequestError as e:
            # Retry on network errors
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def delete(self, endpoint: str) -> Any:
        """Performs a DELETE request."""
        headers = await self.get_headers()
        try:
            response = await self._http_client.delete(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Only retry on 5xx errors
            if 500 <= e.response.status_code < 600:
                raise e
            # Don't retry on 4xx errors
            raise APIError(
                status_code=e.response.status_code, message=e.response.text
            ) from e
        except httpx.RequestError as e:
            # Retry on network errors
            raise e

    async def close(self) -> None:
        """Closes the underlying HTTP client."""
        await self._http_client.aclose()
