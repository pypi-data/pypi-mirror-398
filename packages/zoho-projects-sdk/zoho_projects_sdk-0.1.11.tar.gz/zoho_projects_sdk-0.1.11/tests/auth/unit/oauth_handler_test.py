import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zoho_projects_sdk.auth import ZohoOAuth2Handler
from zoho_projects_sdk.config import ZohoAuthConfig


class TestZohoOAuth2Handler:
    """Test suite for ZohoOAuth2Handler class."""

    def test_init_with_timeout_parameter(self) -> None:
        """
        Test initialization with timeout parameter.
        """
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
            timeout=30.0,
        )
        handler = ZohoOAuth2Handler(config=config)

        assert handler.timeout == 30.0
        assert handler._access_token is None
        assert handler._token_expiry is None

    def test_init_with_parameters(self) -> None:
        """
        Test initialization with explicit parameters.
        """
        config = ZohoAuthConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )
        handler = ZohoOAuth2Handler(config=config)

        assert handler.client_id == "test_client_id"
        assert handler.client_secret == "test_client_secret"
        assert handler.refresh_token == "test_refresh_token"
        assert handler.portal_id == "test_portal_id"
        assert handler._access_token is None
        assert handler._token_expiry is None

    def test_init_with_environment_variables(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ZOHO_PROJECTS_CLIENT_ID": "env_client_id",
                "ZOHO_PROJECTS_CLIENT_SECRET": "env_client_secret",
                "ZOHO_PROJECTS_REFRESH_TOKEN": "env_refresh_token",
                "ZOHO_PROJECTS_PORTAL_ID": "env_portal_id",
            },
        ):
            handler = ZohoOAuth2Handler(config=ZohoAuthConfig())

            assert handler.client_id == "env_client_id"
            assert handler.client_secret == "env_client_secret"
            assert handler.refresh_token == "env_refresh_token"
            assert handler.portal_id == "env_portal_id"

    def test_init_missing_client_id_raises_error(self) -> None:
        """
        Test that ValueError is raised when client_id is missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="Client ID, Client Secret, and Refresh Token are required",
            ):
                ZohoOAuth2Handler(
                    config=ZohoAuthConfig(
                        client_secret="secret",
                        refresh_token="token",
                        portal_id="portal",
                    )
                )

    def test_init_missing_client_secret_raises_error(self) -> None:
        """
        Test that ValueError is raised when client_secret is missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="Client ID, Client Secret, and Refresh Token are required",
            ):
                ZohoOAuth2Handler(
                    config=ZohoAuthConfig(
                        client_id="client",
                        refresh_token="token",
                        portal_id="portal",
                    )
                )

    def test_init_missing_refresh_token_raises_error(self) -> None:
        """
        Test that ValueError is raised when refresh_token is missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="Client ID, Client Secret, and Refresh Token are required",
            ):
                ZohoOAuth2Handler(
                    config=ZohoAuthConfig(
                        client_id="client",
                        client_secret="secret",
                        portal_id="portal",
                    )
                )

    def test_init_missing_portal_id_raises_error(self) -> None:
        """
        Test that ValueError is raised when portal_id is missing.
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="Client ID, Client Secret, and Refresh Token are required",
            ):
                ZohoOAuth2Handler(
                    config=ZohoAuthConfig(
                        client_id="client",
                        client_secret="secret",
                        refresh_token="token",
                    )
                )

    @pytest.mark.asyncio
    async def test_get_access_token_first_time(self) -> None:
        """
        Test get_access_token when called for the first time (no existing token).
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        with patch.object(
            handler, "_refresh_access_token", new_callable=AsyncMock
        ) as mock_refresh:
            # Set up the mock to set the access token when called
            def set_token():
                handler._access_token = "mocked_token"
                handler._token_expiry = time.time() + 3600

            mock_refresh.side_effect = set_token

            result = await handler.get_access_token()

            mock_refresh.assert_called_once()
            assert result == "mocked_token"

    @pytest.mark.asyncio
    async def test_get_access_token_expired_token(self) -> None:
        """
        Test get_access_token when token is expired.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        # Set an expired token
        handler._access_token = "old_token"
        handler._token_expiry = time.time() - 100  # Expired 100 seconds ago

        with patch.object(
            handler, "_refresh_access_token", new_callable=AsyncMock
        ) as mock_refresh:
            # Set up the mock to set the access token when called
            mock_refresh.return_value = None
            handler._access_token = "mocked_token"

            result = await handler.get_access_token()

            mock_refresh.assert_called_once()
            assert result == "mocked_token"

    @pytest.mark.asyncio
    async def test_get_access_token_valid_token(self) -> None:
        """
        Test get_access_token when token is still valid.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        # Set a valid token
        handler._access_token = "valid_token"
        handler._token_expiry = time.time() + 3600  # Valid for 1 hour

        with patch.object(
            handler, "_refresh_access_token", new_callable=AsyncMock
        ) as mock_refresh:
            result = await handler.get_access_token()

            mock_refresh.assert_not_called()
            assert result == "valid_token"

    @pytest.mark.asyncio
    async def test_get_access_token_refresh_failure_raises_error(self) -> None:
        """
        Test that get_access_token raises RuntimeError when refresh fails to set token.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        # Set refresh to not set the access token
        with patch.object(
            handler, "_refresh_access_token", new_callable=AsyncMock
        ) as mock_refresh:
            mock_refresh.return_value = None
            # Ensure _access_token remains None
            handler._access_token = None

            with pytest.raises(
                RuntimeError, match="Access token could not be refreshed"
            ):
                await handler.get_access_token()

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self) -> None:
        """
        Test successful access token refresh.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await handler._refresh_access_token()

            assert handler._access_token == "new_access_token"
            # Check that expiry is set with buffer (60 seconds before actual expiry)
            expected_expiry = time.time() + 3600 - 60
            assert (
                abs(handler._token_expiry - expected_expiry) < 1
            )  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_refresh_access_token_default_expiry(self) -> None:
        """
        Test access token refresh with default expiry when not provided.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            # No expires_in provided
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await handler._refresh_access_token()

            assert handler._access_token == "new_access_token"
            # Check that default expiry (3600) is used with buffer
            expected_expiry = time.time() + 3600 - 60
            assert (
                abs(handler._token_expiry - expected_expiry) < 1
            )  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_refresh_access_token_http_error(self) -> None:
        """
        Test access token refresh when HTTP request fails.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=Exception("HTTP Error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(Exception, match="HTTP Error"):
                await handler._refresh_access_token()

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_response(self) -> None:
        """
        Test access token refresh with invalid JSON response.
        """
        config = ZohoAuthConfig(
            client_id="client",
            client_secret="secret",
            refresh_token="token",
            portal_id="portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="Invalid JSON"):
                await handler._refresh_access_token()

    def test_refresh_access_token_correct_request_data(self) -> None:
        """
        Test that _refresh_access_token sends correct request data.
        """
        config = ZohoAuthConfig(
            client_id="test_client",
            client_secret="test_secret",
            refresh_token="test_refresh",
            portal_id="test_portal",
        )
        handler = ZohoOAuth2Handler(config=config)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Run the refresh in an async context
            import asyncio

            asyncio.run(handler._refresh_access_token())

            # Verify the POST request was made with correct data
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://accounts.zoho.com/oauth/v2/token"
            assert call_args[1]["data"] == {
                "refresh_token": "test_refresh",
                "client_id": "test_client",
                "client_secret": "test_secret",
                "grant_type": "refresh_token",
            }
