"""
Configuration loader for the SDK.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


def load_sdk_config() -> None:
    """
    Loads configuration from a .env file and environment variables.
    """
    load_dotenv()


@dataclass
class ZohoAuthConfig:
    """
    Configuration for Zoho OAuth2 authentication.
    """

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    portal_id: Optional[str] = None
    timeout: Optional[float] = None

    def __post_init__(self) -> None:
        """Initialize values from environment if not provided."""
        self.client_id = self.client_id or os.getenv("ZOHO_PROJECTS_CLIENT_ID")
        self.client_secret = self.client_secret or os.getenv(
            "ZOHO_PROJECTS_CLIENT_SECRET"
        )
        self.refresh_token = self.refresh_token or os.getenv(
            "ZOHO_PROJECTS_REFRESH_TOKEN"
        )
        self.portal_id = self.portal_id or os.getenv("ZOHO_PROJECTS_PORTAL_ID")
        if self.timeout is None:
            timeout_env = os.getenv("ZOHO_PROJECTS_TIMEOUT")
            self.timeout = float(timeout_env) if timeout_env else None


class Settings:
    """
    Holds all settings for the SDK.
    """

    ZOHO_PROJECTS_CLIENT_ID: Optional[str] = os.getenv("ZOHO_PROJECTS_CLIENT_ID")
    ZOHO_PROJECTS_CLIENT_SECRET: Optional[str] = os.getenv(
        "ZOHO_PROJECTS_CLIENT_SECRET"
    )
    ZOHO_PROJECTS_REFRESH_TOKEN: Optional[str] = os.getenv(
        "ZOHO_PROJECTS_REFRESH_TOKEN"
    )
    ZOHO_PROJECTS_PORTAL_ID: Optional[str] = os.getenv("ZOHO_PROJECTS_PORTAL_ID")
    _timeout_env: Optional[str] = os.getenv("ZOHO_PROJECTS_TIMEOUT")
    ZOHO_PROJECTS_TIMEOUT: Optional[float] = (
        float(_timeout_env) if _timeout_env else None
    )


# Load the configuration when the module is imported
load_sdk_config()
settings = Settings()
