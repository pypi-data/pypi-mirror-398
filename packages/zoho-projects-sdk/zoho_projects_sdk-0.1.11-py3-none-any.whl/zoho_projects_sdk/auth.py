"""
Handles OAuth2 authentication and token management for the Zoho Projects API.
"""

import time
from typing import Optional

import httpx

from .config import ZohoAuthConfig


class ZohoOAuth2Handler:
    """
    Manages the OAuth2 flow for Zoho APIs, including token refresh.
    """

    def __init__(self, config: Optional[ZohoAuthConfig] = None):
        """
        Initialize the OAuth2 handler with configuration.

        Args:
            config: ZohoAuthConfig instance. If not provided, will create one
                   using environment variables.
        """
        self.config = config or ZohoAuthConfig()
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        self.refresh_token = self.config.refresh_token
        self.portal_id = self.config.portal_id
        self.timeout = self.config.timeout
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[float] = None
        self._client = httpx.AsyncClient(timeout=self.timeout)

        if not all(
            [self.client_id, self.client_secret, self.refresh_token, self.portal_id]
        ):
            raise ValueError(
                "Client ID, Client Secret, and Refresh Token are required."
            )

    async def get_access_token(self) -> str:
        """
        Retrieves the access token, refreshing it if necessary.
        """
        # Check if token is expired or doesn't exist
        if (
            self._access_token is None
            or self._token_expiry is None
            or time.time() >= self._token_expiry
        ):
            await self._refresh_access_token()

        # After _refresh_access_token runs, _access_token should be a valid string.
        # The refresh call happens whenever the token was None or expired.
        if self._access_token is None:
            # This should not happen if _refresh_access_token works correctly,
            # but added as a safety check.
            raise RuntimeError("Access token could not be refreshed.")

        return self._access_token

    async def _refresh_access_token(self) -> None:
        """
        Makes a request to the Zoho API to refresh the access token.
        """
        url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, data=data)
            response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        # Zoho typically returns the expiry in seconds. Add a buffer for
        # processing time.
        expires_in_seconds = token_data.get(
            "expires_in", 3600
        )  # Default to 1 hour if not provided
        self._token_expiry = (
            time.time() + expires_in_seconds - 60
        )  # Refresh 1 minute before expiry
